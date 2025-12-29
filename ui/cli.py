"""Command line interface"""

from typing import Optional, List
from controllers.recovery_controller import RecoveryController
from models.config import FileSignatures
from models.resource_config import ResourceConfig


class CLI:
    """Command line interface for the file recovery system"""
    
    def __init__(self):
        self.controller = RecoveryController()
    
    def run(self):
        """Runs the CLI interface"""
        print("\n===== FILE RECOVERY SYSTEM =====\n")
        print("1. Scan logical drive (C:, D:)")
        print("2. Scan physical drive (PhysicalDrive)\n")
        
        option = input("Select option: ").strip()
        
        if option == "1":
            drives = self.controller.list_logical_drives()
            if not drives:
                print("❌ No drives detected")
                return
            
            for i, d in enumerate(drives):
                print(f"{i + 1}. {d}:")
            
            try:
                idx = int(input("Select drive: ")) - 1
                path = rf"\\.\{drives[idx]}:"
            except:
                print("❌ Invalid selection")
                return
        
        elif option == "2":
            drives_info = self.controller.list_physical_drives_with_names()
            if not drives_info:
                # Fallback to simple list if detailed info fails
                drives = self.controller.list_physical_drives()
                if not drives:
                    print("❌ No physical drives detected")
                    return
                
                for i, d in enumerate(drives):
                    print(f"{i + 1}. {d}")
                
                try:
                    idx = int(input("Select physical drive: ")) - 1
                    path = rf"\\.\{drives[idx]}"
                except:
                    print("❌ Invalid selection")
                    return
            else:
                for i, drive in enumerate(drives_info):
                    model = drive.get('model', 'Unknown')
                    size_gb = ""
                    if 'size' in drive and drive['size']:
                        size_gb = f" ({drive['size'] / (1024**3):.2f} GB)"
                    print(f"{i + 1}. {drive['display_name']}{size_gb}")
                
                try:
                    idx = int(input("Select physical drive: ")) - 1
                    selected_drive = drives_info[idx]
                    path = rf"\\.\{selected_drive['name']}"
                except:
                    print("❌ Invalid selection")
                    return
        
        else:
            print("❌ Invalid option")
            return
        
        output = input("Path to save recovered files: ").strip()
        if not output:
            print("❌ Invalid path")
            return
        
        # File type configuration
        print("\n📋 File types to recover:")
        print("   Available types: " + ", ".join(FileSignatures.get_all_types()))
        print("   (Press Enter to recover ALL types)")
        types_input = input("   Enter types separated by commas (e.g: txt,pdf,doc): ").strip()
        
        file_types = None
        if types_input:
            file_types = [t.strip().lower() for t in types_input.split(',') if t.strip()]
            valid_types = FileSignatures.get_all_types()
            file_types = [t for t in file_types if t in valid_types]
            if not file_types:
                print("⚠️  No valid types. Will recover ALL types.")
                file_types = None
        
        # Specific name search
        print("\n🔎 Specific search:")
        print("   (Press Enter to search ALL files)")
        print("   You can use wildcards:")
        print("   - * = any sequence of characters (e.g: *pass*.txt)")
        print("   - % = single character (e.g: %wall%)")
        print("   - If you don't include extension, searches only in filename")
        search_pattern = input("   Enter search pattern (e.g: *pass*.txt or %wall%): ").strip()
        if not search_pattern:
            search_pattern = None
        
        # System files filter
        print("\n🚫 System files filter:")
        filter_input = input("   Filter system files? (Y/n): ").strip().lower()
        filter_system = filter_input != 'n'
        
        # Resource usage mode
        print("\n⚙️  Resource usage mode:")
        print("   1. Performance (uses all resources - fastest)")
        print("   2. Balanced (moderate resource usage - recommended)")
        print("   3. Low resources (minimal resource usage - slower)")
        resource_mode = input("   Select mode (1-3, default=2): ").strip() or "2"
        
        if resource_mode == "1":
            resource_config = ResourceConfig.create_performance_mode()
            mem_gb = resource_config.max_memory_mb / 1024
            print(f"   ⚡ Performance mode selected (85% RAM = {mem_gb:.1f} GB max)")
        elif resource_mode == "3":
            resource_config = ResourceConfig.create_low_resource_mode()
            mem_gb = resource_config.max_memory_mb / 1024
            print(f"   🐢 Low resource mode selected (25% RAM = {mem_gb:.1f} GB max)")
        else:
            resource_config = ResourceConfig.create_balanced_mode()
            mem_gb = resource_config.max_memory_mb / 1024
            print(f"   ⚖️  Balanced mode selected (50% RAM = {mem_gb:.1f} GB max)")
        
        # Get disk size
        total_size = self.controller.get_disk_size(path)
        is_physical = path.startswith(r"\\.\PhysicalDrive")
        
        # Progress callback
        def progress_callback(blocks, position, found, memory_usage=None):
            mb_scanned = position / (1024 * 1024)
            if total_size and total_size > 0:
                percentage = (position / total_size) * 100
                mb_total = total_size / (1024 * 1024)
                mem_info = f" | Memory: {memory_usage:.1f} MB" if memory_usage else ""
                print(f"📊 Blocks: {blocks:,} | Progress: {percentage:.2f}% | "
                      f"Scanned: {mb_scanned:.1f} MB / {mb_total:.1f} MB | "
                      f"Found: {found}{mem_info}")
            else:
                mem_info = f" | Memory: {memory_usage:.1f} MB" if memory_usage else ""
                print(f"📊 Blocks: {blocks:,} | Scanned: {mb_scanned:.1f} MB | "
                      f"Found: {found}{mem_info}")
        
        # Show initial information
        print(f"\n🔍 Deep scan started: {path}")
        print(f"📁 Saving to: {output}")
        print(f"🔬 Mode: Complex deep scan")
        if file_types:
            print(f"📋 File types: {', '.join(file_types)}")
        else:
            print(f"📋 File types: ALL")
        if search_pattern:
            print(f"🔎 Specific search: {search_pattern}")
        if filter_system:
            print(f"🚫 System files filter: ENABLED")
        if total_size:
            print(f"💾 Disk size: {total_size / (1024*1024*1024):.2f} GB")
        if resource_config.max_memory_mb:
            mem_gb = resource_config.max_memory_mb / 1024
            print(f"💾 Memory limit: {resource_config.max_memory_mb} MB ({mem_gb:.1f} GB)")
        print()
        
        # Start recovery
        try:
            found = self.controller.start_recovery(
                path, output, file_types, search_pattern, filter_system, 
                progress_callback, resource_config
            )
            
            print("\n✅ Deep scan completed")
            print(f"📄 Files recovered: {found}")
            if total_size and total_size > 0:
                print(f"💾 Total size scanned: {total_size / (1024*1024*1024):.2f} GB")
            else:
                mb_scanned = self.controller.recovery_service.blocks * 4096 / (1024 * 1024)
                print(f"💾 Total size scanned: {mb_scanned:.1f} MB")
        
        except PermissionError:
            print("\n❌ PERMISSION DENIED")
            print("👉 Run as ADMINISTRATOR or use WinPE / Hiren's Boot")
        except Exception as e:
            print(f"\n❌ Error during scan: {e}")
            if self.controller.recovery_service:
                print(f"📄 Files recovered until error: {self.controller.recovery_service.found_count}")

