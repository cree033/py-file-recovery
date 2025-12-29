"""Resource usage configuration"""

import time
import os
import ctypes
import platform

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Windows memory detection using ctypes (fallback if psutil not available)
if platform.system() == 'Windows':
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    
    def get_windows_memory():
        """Gets total and available memory on Windows using Windows API"""
        try:
            mem_status = MEMORYSTATUSEX()
            mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))
            
            total_mb = mem_status.ullTotalPhys / (1024 * 1024)
            available_mb = mem_status.ullAvailPhys / (1024 * 1024)
            return total_mb, available_mb
        except:
            return None, None
else:
    def get_windows_memory():
        return None, None


class ResourceConfig:
    """Configuration for resource usage during recovery"""
    
    def __init__(self, max_memory_mb=None, cpu_limit=None, 
                 block_delay_ms=0, buffer_size=3):
        """
        Initialize resource configuration
        
        Args:
            max_memory_mb: Maximum memory usage in MB (None = unlimited)
            cpu_limit: CPU usage limit as percentage (None = unlimited)
            block_delay_ms: Delay between blocks in milliseconds (0 = no delay)
            buffer_size: Size of block buffer for fragmented text reconstruction
        """
        self.max_memory_mb = max_memory_mb
        self.cpu_limit = cpu_limit
        self.block_delay_ms = block_delay_ms
        self.buffer_size = buffer_size
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
    
    def check_memory_limit(self):
        """Checks if memory usage is within limits"""
        if self.max_memory_mb is None:
            return True
        
        if not PSUTIL_AVAILABLE or not self.process:
            # If psutil not available, assume OK
            return True
        
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            if memory_mb > self.max_memory_mb:
                return False
        except:
            # If error checking memory, allow continuation
            return True
        return True
    
    def get_memory_usage_mb(self):
        """Gets current memory usage in MB"""
        if not PSUTIL_AVAILABLE or not self.process:
            return 0.0
        
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)
        except:
            return 0.0
    
    def apply_block_delay(self):
        """Applies delay between blocks if configured"""
        if self.block_delay_ms > 0:
            time.sleep(self.block_delay_ms / 1000.0)
    
    def should_continue(self):
        """Checks if recovery should continue based on resource limits"""
        if not self.check_memory_limit():
            return False
        return True
    
    @staticmethod
    def get_available_memory_mb():
        """Gets available system memory in MB"""
        # Try psutil first
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                # Return total system memory (RAM total)
                return memory.total / (1024 * 1024)
            except:
                pass
        
        # Fallback to Windows API if on Windows
        if platform.system() == 'Windows':
            total_mb, _ = get_windows_memory()
            if total_mb:
                return total_mb
        
        # Default to 8GB if detection fails
        return 8192
    
    @staticmethod
    def get_free_memory_mb():
        """Gets free/available system memory in MB"""
        # Try psutil first
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                # Return available memory (free + cached)
                return memory.available / (1024 * 1024)
            except:
                pass
        
        # Fallback to Windows API if on Windows
        if platform.system() == 'Windows':
            _, available_mb = get_windows_memory()
            if available_mb:
                return available_mb
        
        # Default to 4GB if detection fails
        return 4096
    
    @staticmethod
    def create_performance_mode():
        """Creates config for maximum performance (uses 75% of total RAM)"""
        total_memory = ResourceConfig.get_available_memory_mb()
        free_memory = ResourceConfig.get_free_memory_mb()
        
        # Use 75% of total RAM as primary target
        max_memory = int(total_memory * 0.75)
        
        # Only limit if free memory is critically low (less than 20% of total)
        # This allows using RAM even if it's currently in use by other processes
        if free_memory < total_memory * 0.20:
            # If system is critically low on free memory, use 90% of what's free
            max_memory = min(max_memory, int(free_memory * 0.90))
        
        # Ensure minimum of 1GB and maximum of 80% of total RAM
        max_memory = max(1024, min(max_memory, int(total_memory * 0.80)))
        
        # Calculate optimal buffer size based on available memory
        # More memory = larger buffer = less I/O operations = faster processing
        # Buffer size scales with memory: ~1 block per 100MB of available memory
        buffer_size = max(5, min(50, int(max_memory / 100)))  # Between 5 and 50 blocks
        
        return ResourceConfig(
            max_memory_mb=max_memory,
            cpu_limit=None,      # Unlimited CPU
            block_delay_ms=0,    # No delay
            buffer_size=buffer_size  # Dynamic buffer based on memory
        )
    
    @staticmethod
    def create_balanced_mode():
        """Creates config for balanced performance (uses ~50% of total RAM)"""
        total_memory = ResourceConfig.get_available_memory_mb()
        free_memory = ResourceConfig.get_free_memory_mb()
        
        # Use 50% of total RAM as primary target
        max_memory = int(total_memory * 0.50)
        
        # Only limit if free memory is critically low (less than 15% of total)
        # This allows using RAM even if it's currently in use by other processes
        if free_memory < total_memory * 0.15:
            # If system is critically low on free memory, use 80% of what's free
            max_memory = min(max_memory, int(free_memory * 0.80))
        
        # Ensure minimum of 512MB and maximum of 60% of total RAM
        max_memory = max(512, min(max_memory, int(total_memory * 0.60)))
        
        # Calculate optimal buffer size based on available memory
        # More memory = larger buffer = less I/O operations = faster processing
        buffer_size = max(3, min(30, int(max_memory / 150)))  # Between 3 and 30 blocks
        
        return ResourceConfig(
            max_memory_mb=max_memory,
            cpu_limit=80,        # 80% CPU
            block_delay_ms=0,    # No delay for better performance
            buffer_size=buffer_size  # Dynamic buffer based on memory
        )
    
    @staticmethod
    def create_low_resource_mode():
        """Creates config for low resource usage (uses ~25% of total RAM)"""
        total_memory = ResourceConfig.get_available_memory_mb()
        free_memory = ResourceConfig.get_free_memory_mb()
        
        # Use 25% of total RAM as primary target
        max_memory = int(total_memory * 0.25)
        
        # Only limit if free memory is critically low (less than 10% of total)
        # This allows using RAM even if it's currently in use by other processes
        if free_memory < total_memory * 0.10:
            # If system is critically low on free memory, use 70% of what's free
            max_memory = min(max_memory, int(free_memory * 0.70))
        
        # Ensure minimum of 256MB and maximum of 30% of total RAM
        max_memory = max(256, min(max_memory, int(total_memory * 0.30)))
        
        # Calculate optimal buffer size based on available memory
        buffer_size = max(2, min(15, int(max_memory / 200)))  # Between 2 and 15 blocks
        
        return ResourceConfig(
            max_memory_mb=max_memory,
            cpu_limit=50,        # 50% CPU
            block_delay_ms=5,    # Reduced delay (was 10ms)
            buffer_size=buffer_size  # Dynamic buffer based on memory
        )

