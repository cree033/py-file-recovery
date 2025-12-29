"""Main file recovery service"""

import os
from collections import deque
from typing import Optional, List
from models.config import BLOCK_SIZE, WINDOW_SIZE, OVERLAP, MIN_TEXT_LEN
from models.resource_config import ResourceConfig
from services.detection_service import DetectionService
from services.filter_service import FilterService
from utils.encoding_utils import is_text, detect_encoding
from utils.file_utils import clean_filename, extract_filename_from_content


class RecoveryService:
    """Service for recovering files from disks"""
    
    def __init__(self, progress_callback=None, resource_config=None):
        """
        Initializes the recovery service
        
        Args:
            progress_callback: Callback function to report progress
            resource_config: ResourceConfig object for resource management
        """
        self.progress_callback = progress_callback
        self.resource_config = resource_config or ResourceConfig.create_balanced_mode()
        self.unique_texts = set()
        # Calculate max unique texts based on available memory
        # Each hash is ~24 bytes, so we can store many with limited memory
        # With more memory, we can store more hashes = less cleanup = faster processing
        max_memory_mb = self.resource_config.max_memory_mb or 4096
        # Scale with memory: ~2M hashes per GB (more aggressive with more memory)
        max_unique_texts = int((max_memory_mb / 1024) * 2000000)  # ~2M per GB
        self.max_unique_texts = max(100000, min(max_unique_texts, 50000000))  # Between 100K and 50M
        self.block_buffer = deque(maxlen=self.resource_config.buffer_size)
        self.found_count = 0
        self.blocks = 0
        self.cancelled = False
        self.last_cleanup_blocks = 0
        # Dynamic cleanup interval: more memory = less frequent cleanups = faster
        # Scale cleanup interval with memory: ~100K blocks per GB
        self.cleanup_interval = max(50000, min(500000, int((max_memory_mb / 1024) * 100000)))
    
    def recover_files(self, disk_path: str, output_dir: str, 
                     file_types: Optional[List[str]] = None,
                     search_pattern: Optional[str] = None,
                     filter_system: bool = True,
                     preview_mode: bool = False) -> int:
        """
        Recovers files from disk
        
        Args:
            disk_path: Path of the disk to scan
            output_dir: Directory where to save files (only used if preview_mode=False)
            file_types: List of allowed extensions
            search_pattern: Search pattern with wildcards
            filter_system: If True, filters system files
            preview_mode: If True, only lists files without saving them
        
        Returns:
            Number of files found/recovered
        """
        # Create output directory only if not in preview mode
        if not preview_mode:
            try:
                os.makedirs(output_dir, exist_ok=True)
                if not os.path.isdir(output_dir):
                    raise ValueError(f"Output path exists but is not a directory: {output_dir}")
            except Exception as e:
                raise ValueError(f"Could not create output directory '{output_dir}': {e}")
        
        self.preview_mode = preview_mode
        self.preview_list = []  # List to store preview results
        
        self.found_count = 0
        self.blocks = 0
        self.unique_texts.clear()
        self.block_buffer.clear()
        self.cancelled = False
        
        try:
            with open(disk_path, "rb") as disk:
                while True:
                    try:
                        block = disk.read(BLOCK_SIZE)
                        if not block:
                            break
                    except (OSError, IOError):
                        # For physical disks, there may be errors
                        if disk_path.startswith(r"\\.\PhysicalDrive"):
                            try:
                                disk.seek(BLOCK_SIZE, 1)
                                continue
                            except:
                                break
                        else:
                            raise
                    
                    # Check if cancelled
                    if self.cancelled:
                        break
                    
                    current_position = self.blocks * BLOCK_SIZE
                    
                    # Method 1: Direct block scan
                    self._process_block(block, current_position, output_dir, 
                                      file_types, search_pattern, filter_system)
                    
                    # Method 2: Sliding window
                    self._process_sliding_window(block, current_position, output_dir,
                                                file_types, search_pattern, filter_system)
                    
                    # Method 3: Fragmented reconstruction
                    self._process_fragmented(block, disk_path, current_position, output_dir,
                                           file_types, search_pattern, filter_system)
                    
                    # Method 4: Offset scan (every 10 blocks)
                    if self.blocks % 10 == 0:
                        self._process_offset_scan(block, current_position, output_dir,
                                                 file_types, search_pattern, filter_system)
                    
                    self.blocks += 1
                    
                    # Periodic cleanup of unique_texts to prevent excessive memory growth
                    if self.blocks - self.last_cleanup_blocks >= self.cleanup_interval:
                        self._cleanup_memory()
                        self.last_cleanup_blocks = self.blocks
                    
                    # Check resource limits
                    if not self.resource_config.should_continue():
                        # Try cleanup before raising error
                        self._cleanup_memory()
                        if not self.resource_config.should_continue():
                            raise MemoryError(f"Memory limit exceeded ({self.resource_config.max_memory_mb} MB)")
                    
                    # Apply block delay if configured
                    self.resource_config.apply_block_delay()
                    
                    # Report progress
                    if self.blocks % 1000 == 0 and self.progress_callback:
                        memory_usage = self.resource_config.get_memory_usage_mb()
                        self.progress_callback(self.blocks, current_position, self.found_count, memory_usage)
        
        except PermissionError:
            raise PermissionError("PERMISSION DENIED. Run as ADMINISTRATOR")
        except Exception as e:
            raise Exception(f"Error during scan: {e}")
        
        return self.found_count
    
    def cancel(self):
        """Cancels the recovery process"""
        self.cancelled = True
    
    def _cleanup_memory(self):
        """Cleans up memory by reducing unique_texts set if it's too large"""
        if len(self.unique_texts) > self.max_unique_texts:
            # If set is too large, keep only a portion to free memory
            # Since sets don't have order, we'll keep a random sample
            # This is acceptable because we're just preventing duplicates, not tracking history
            keep_count = int(self.max_unique_texts * 0.7)  # Keep 70% of max
            if keep_count < len(self.unique_texts):
                # Convert to list, take sample, convert back to set
                unique_list = list(self.unique_texts)
                # Keep a random sample (or last N if we want some determinism)
                # For simplicity, keep the last N entries
                self.unique_texts = set(unique_list[-keep_count:])
    
    def _process_block(self, block: bytes, position: int, output_dir: str,
                      file_types: Optional[List[str]], search_pattern: Optional[str],
                      filter_system: bool):
        """Processes a block directly"""
        if is_text(block, threshold=0.7):
            encoding, text = detect_encoding(block)
            if text:
                text_hash = hash(text[:100])
                if text_hash not in self.unique_texts:
                    self.unique_texts.add(text_hash)
                    self._save_file(block, text, position, output_dir,
                                  file_types, search_pattern, filter_system, "")
    
    def _process_sliding_window(self, block: bytes, position: int, output_dir: str,
                               file_types: Optional[List[str]], search_pattern: Optional[str],
                               filter_system: bool):
        """Processes using sliding window"""
        for start in range(0, len(block) - WINDOW_SIZE, OVERLAP):
            window = block[start:start + WINDOW_SIZE]
            if is_text(window, threshold=0.6):
                encoding, text = detect_encoding(window)
                if text and len(text.strip()) >= MIN_TEXT_LEN:
                    text_hash = hash(text[:100])
                    if text_hash not in self.unique_texts:
                        self.unique_texts.add(text_hash)
                        self._save_file(window, text, position + start, output_dir,
                                      file_types, search_pattern, filter_system, "")
    
    def _process_fragmented(self, block: bytes, disk_path: str, position: int, output_dir: str,
                           file_types: Optional[List[str]], search_pattern: Optional[str],
                           filter_system: bool):
        """Processes fragmented text"""
        self.block_buffer.append(block)
        if len(self.block_buffer) >= 2:
            combined_data = b''.join(self.block_buffer)
            reconstructed_text = self._reconstruct_text(combined_data)
            if reconstructed_text:
                text_hash = hash(reconstructed_text[:100])
                if text_hash not in self.unique_texts:
                    self.unique_texts.add(text_hash)
                    self._save_file(combined_data, reconstructed_text, position - BLOCK_SIZE,
                                  output_dir, file_types, search_pattern, filter_system, "frag_")
    
    def _process_offset_scan(self, block: bytes, position: int, output_dir: str,
                            file_types: Optional[List[str]], search_pattern: Optional[str],
                            filter_system: bool):
        """Processes with offset scan"""
        for offset in [0, 128, 256, 512, 1024, 2048, 3072]:
            if offset < len(block):
                sub_block = block[offset:offset + WINDOW_SIZE]
                if is_text(sub_block, threshold=0.65):
                    encoding, text = detect_encoding(sub_block)
                    if text:
                        text_hash = hash(text[:100])
                        if text_hash not in self.unique_texts:
                            self.unique_texts.add(text_hash)
                            self._save_file(sub_block, text, position + offset, output_dir,
                                          file_types, search_pattern, filter_system, "offset_")
    
    def _reconstruct_text(self, data: bytes) -> Optional[str]:
        """Reconstructs fragmented text"""
        from models.config import CODIFICACIONES
        import re
        
        best_text = None
        best_length = 0
        
        for encoding in CODIFICACIONES:
            try:
                text = data.decode(encoding, errors="ignore")
                words = re.findall(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]{3,}', text)
                if len(words) >= 10:
                    clean_text = ' '.join(words)
                    if len(clean_text) >= MIN_TEXT_LEN:
                        if len(clean_text) > best_length:
                            best_length = len(clean_text)
                            best_text = clean_text
            except:
                continue
        
        return best_text
    
    def _save_file(self, data: bytes, text: str, position: int, output_dir: str,
                  file_types: Optional[List[str]], search_pattern: Optional[str],
                  filter_system: bool, prefix: str):
        """Saves a file if it passes filters"""
        # Try to get original name FIRST - this is the priority
        original_name = extract_filename_from_content(text, data)
        
        # Detect type
        detected_type = DetectionService.detect_file_type(data)
        
        # Determine filename: PRIORITY to original name if available
        filename = None
        
        if original_name:
            # We have an original name - use it
            clean_name = clean_filename(original_name)
            if clean_name:
                # Ensure it has an extension
                if '.' not in clean_name:
                    # Add extension based on detected type
                    clean_name += f'.{detected_type or "txt"}'
                filename = clean_name
            else:
                # Original name couldn't be cleaned, use generic
                filename = f"{prefix}recovered_{self.found_count:05d}.{detected_type or 'txt'}"
        else:
            # No original name found - use generic name
            filename = f"{prefix}recovered_{self.found_count:05d}.{detected_type or 'txt'}"
        
        # Apply filters
        passes_filters, filter_type = FilterService.apply_filters(
            filename, data, file_types, search_pattern, filter_system
        )
        
        if not passes_filters:
            return
        
        # STRICT: Verify file type matches allowed types (double check)
        if file_types:
            # Get extension from filename
            ext_from_name = os.path.splitext(filename)[1].lstrip('.').lower()
            
            # Determine final type: prefer extension from name, then detected type
            final_type = None
            if ext_from_name:
                final_type = ext_from_name
            elif detected_type:
                final_type = detected_type
            elif filter_type:
                final_type = filter_type
            
            # STRICT: Must have a type and it must be in allowed types
            if not final_type:
                # If no type can be determined and types are specified, reject
                return
            
            if final_type not in file_types:
                return
        
        if not detected_type and filter_type:
            detected_type = filter_type
        
        # Create file info for tracking
        file_info = {
            'filename': filename,
            'original_name': original_name,
            'type': detected_type or 'txt',
            'size': len(text),
            'position': position
        }
        
        # In preview mode, just add to list and return
        if self.preview_mode:
            self.preview_list.append(file_info)
            self.found_count += 1
            return
        
        # In recover mode, also track in preview_list for cancellation display
        self.preview_list.append(file_info)
        
        # Save file
        try:
            base_path = os.path.join(output_dir, filename)
            counter = 1
            while os.path.exists(base_path):
                name_base, ext = os.path.splitext(filename)
                base_path = os.path.join(output_dir, f"{name_base}_{counter}{ext}")
                counter += 1
            
            with open(base_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            self.found_count += 1
            # Show message indicating if original name was used
            if original_name:
                clean_original = clean_filename(original_name)
                if clean_original and clean_original == filename:
                    print(f"  ✓ Recovered: {filename} (nombre original detectado)")
                else:
                    print(f"  ✓ Recovered: {filename}")
            else:
                print(f"  ✓ Recovered: {filename}")
        except (OSError, IOError, ValueError):
            # If it fails, try with generic name
            try:
                filename = f"{prefix}recovered_{self.found_count:05d}.txt"
                base_path = os.path.join(output_dir, filename)
                counter = 1
                while os.path.exists(base_path):
                    name_base, ext = os.path.splitext(filename)
                    base_path = os.path.join(output_dir, f"{name_base}_{counter}{ext}")
                    counter += 1
                with open(base_path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.found_count += 1
            except:
                pass
    
    def get_preview_list(self):
        """Returns the list of files found in preview mode"""
        return self.preview_list
