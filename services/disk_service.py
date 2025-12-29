"""Service for disk management"""

import os
import string
import subprocess
from typing import List, Optional


class DiskService:
    """Service for listing and getting disk information"""
    
    @staticmethod
    def list_logical_drives() -> List[str]:
        """Lists available logical drives"""
        drives = []
        for letter in string.ascii_uppercase:
            if os.path.exists(f"{letter}:\\"):
                drives.append(letter)
        return drives
    
    @staticmethod
    def list_physical_drives() -> List[str]:
        """Lists available physical drives"""
        try:
            output = subprocess.check_output(
                "wmic diskdrive get Index,Model,Size",
                shell=True
            ).decode(errors="ignore")
            
            drives = []
            for line in output.splitlines():
                parts = line.strip().split()
                if parts and parts[0].isdigit():
                    drives.append(f"PhysicalDrive{parts[0]}")
            return drives
        except:
            return []
    
    @staticmethod
    def get_physical_drive_info(drive_index: str) -> Optional[dict]:
        """Gets detailed information about a physical drive"""
        try:
            output = subprocess.check_output(
                f'wmic diskdrive where Index={drive_index} get Model,Size,SerialNumber,InterfaceType /format:list',
                shell=True
            ).decode(errors="ignore")
            
            info = {}
            for line in output.splitlines():
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key == 'Model':
                        info['model'] = value.strip()
                    elif key == 'Size':
                        if value.strip().isdigit():
                            info['size'] = int(value.strip())
                    elif key == 'SerialNumber':
                        info['serial'] = value.strip()
                    elif key == 'InterfaceType':
                        info['interface'] = value.strip()
            
            return info if info else None
        except:
            return None
    
    @staticmethod
    def list_physical_drives_with_names() -> List[dict]:
        """Lists physical drives with their names/models"""
        try:
            output = subprocess.check_output(
                "wmic diskdrive get Index,Model,Size",
                shell=True
            ).decode(errors="ignore")
            
            drives = []
            lines = output.splitlines()
            
            # Skip header line
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # Parse the line - format is usually: Index Model Size
                parts = line.split(None, 2)  # Split into max 3 parts
                if len(parts) >= 2 and parts[0].isdigit():
                    index = parts[0]
                    model = parts[1] if len(parts) > 1 else "Unknown"
                    size_str = parts[2] if len(parts) > 2 else "0"
                    
                    # Get additional info
                    drive_info = DiskService.get_physical_drive_info(index)
                    
                    drive_dict = {
                        'index': index,
                        'name': f"PhysicalDrive{index}",
                        'model': model,
                        'display_name': f"PhysicalDrive{index} - {model}"
                    }
                    
                    if drive_info:
                        if 'size' in drive_info:
                            drive_dict['size'] = drive_info['size']
                        if 'serial' in drive_info:
                            drive_dict['serial'] = drive_info['serial']
                        if 'interface' in drive_info:
                            drive_dict['interface'] = drive_info['interface']
                    
                    drives.append(drive_dict)
            
            return drives
        except Exception as e:
            return []
    
    @staticmethod
    def get_physical_drive_size(drive_index: str) -> Optional[int]:
        """Gets the size of a physical drive using wmic"""
        try:
            output = subprocess.check_output(
                f"wmic diskdrive where Index={drive_index} get Size",
                shell=True
            ).decode(errors="ignore")
            
            for line in output.splitlines():
                line = line.strip()
                if line and line.isdigit():
                    return int(line)
        except:
            pass
        return None
    
    @staticmethod
    def get_disk_size(disk_path: str) -> Optional[int]:
        """Gets the disk size, whether logical or physical"""
        # If it's a physical disk, use wmic
        if disk_path.startswith(r"\\.\PhysicalDrive"):
            try:
                # Extract the disk index
                index = disk_path.replace(r"\\.\PhysicalDrive", "")
                size = DiskService.get_physical_drive_size(index)
                if size:
                    return size
            except:
                pass
        
        # For logical disks, try seek
        try:
            with open(disk_path, "rb") as disk:
                disk.seek(0, 2)  # Go to end
                size = disk.tell()
                return size
        except:
            return None

