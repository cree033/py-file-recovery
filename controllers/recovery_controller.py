"""Main recovery controller"""

from typing import Optional, List
from services.disk_service import DiskService
from services.recovery_service import RecoveryService
from models.resource_config import ResourceConfig


class RecoveryController:
    """Controller that orchestrates file recovery"""
    
    def __init__(self):
        self.disk_service = DiskService()
        self.recovery_service = None
    
    def list_logical_drives(self) -> List[str]:
        """Lists logical drives"""
        return self.disk_service.list_logical_drives()
    
    def list_physical_drives(self) -> List[str]:
        """Lists physical drives"""
        return self.disk_service.list_physical_drives()
    
    def list_physical_drives_with_names(self) -> List[dict]:
        """Lists physical drives with their names/models"""
        return self.disk_service.list_physical_drives_with_names()
    
    def get_disk_size(self, disk_path: str) -> Optional[int]:
        """Gets disk size"""
        return self.disk_service.get_disk_size(disk_path)
    
    def start_recovery(self, disk_path: str, output_dir: str,
                      file_types: Optional[List[str]] = None,
                      search_pattern: Optional[str] = None,
                      filter_system: bool = True,
                      progress_callback=None,
                      resource_config: Optional[ResourceConfig] = None,
                      preview_mode: bool = False) -> int:
        """
        Starts the recovery process
        
        Args:
            disk_path: Disk path
            output_dir: Output directory
            file_types: Allowed file types
            search_pattern: Search pattern
            filter_system: Filter system files
            progress_callback: Progress callback
            resource_config: Resource configuration (None = balanced mode)
            preview_mode: If True, only lists files without saving
        
        Returns:
            Number of files found/recovered
        """
        self.recovery_service = RecoveryService(progress_callback, resource_config)
        return self.recovery_service.recover_files(
            disk_path, output_dir, file_types, search_pattern, filter_system, preview_mode
        )
    
    def get_preview_list(self):
        """Gets the preview list if in preview mode"""
        if self.recovery_service:
            return self.recovery_service.get_preview_list()
        return []

