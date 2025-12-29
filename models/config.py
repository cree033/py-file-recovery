"""Configuración y constantes del sistema"""

import re

# Constantes de escaneo
BLOCK_SIZE = 4096
MIN_TEXT_LEN = 200
WINDOW_SIZE = 512  # Tamaño de ventana deslizante
OVERLAP = 256  # Solapamiento entre ventanas
CODIFICACIONES = ['utf-8', 'latin-1', 'windows-1252', 'cp850', 'ascii']


class FileSignatures:
    """Firmas de archivos (magic numbers)"""
    SIGNATURES = {
        'txt': [b''],
        'pdf': [b'%PDF'],
        'doc': [b'\xd0\xcf\x11\xe0', b'PK\x03\x04'],  # DOC y DOCX
        'docx': [b'PK\x03\x04'],
        'xls': [b'\xd0\xcf\x11\xe0', b'PK\x03\x04'],  # XLS y XLSX
        'xlsx': [b'PK\x03\x04'],
        'ppt': [b'\xd0\xcf\x11\xe0'],
        'pptx': [b'PK\x03\x04'],
        'zip': [b'PK\x03\x04', b'PK\x05\x06'],
        'rar': [b'Rar!\x1a\x07', b'Rar!\x1a\x07\x00'],
        'jpg': [b'\xff\xd8\xff'],
        'jpeg': [b'\xff\xd8\xff'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'gif': [b'GIF87a', b'GIF89a'],
        'html': [b'<html', b'<!DOCTYPE html', b'<HTML'],
        'htm': [b'<html', b'<!DOCTYPE html', b'<HTML'],
        'xml': [b'<?xml', b'<xml'],
        'json': [b'{', b'['],
        'csv': [b''],
        'log': [b''],
        'ini': [b'['],
        'cfg': [b''],
        'conf': [b''],
    }
    
    @classmethod
    def get_signatures(cls, file_type):
        """Obtiene las firmas para un tipo de archivo"""
        return cls.SIGNATURES.get(file_type, [])
    
    @classmethod
    def get_all_types(cls):
        """Obtiene todos los tipos de archivo soportados"""
        return list(cls.SIGNATURES.keys())


class SystemFiles:
    """Nombres de archivos del sistema a filtrar"""
    SYSTEM_FILES = [
        'desktop.ini', 'thumbs.db', '$mft', '$logfile', '$volume',
        'ntuser.dat', 'ntuser.ini', 'boot.ini', 'system.ini', 'win.ini',
        'pagefile.sys', 'hiberfil.sys', 'swapfile.sys', 'ntldr', 'bootmgr',
        'bootsect.bak', 'bootfont.bin', 'bootsect.dos', 'io.sys', 'msdos.sys',
        'config.sys', 'autoexec.bat', 'command.com', 'ntdetect.com',
    ]
    
    SYSTEM_EXTENSIONS = ['.sys', '.dll', '.exe', '.drv', '.vxd', '.386']
    
    @classmethod
    def is_system_file(cls, filename):
        """Verifica si un archivo es del sistema"""
        if not filename:
            return False
        
        filename_lower = filename.lower()
        
        # Verificar nombres específicos
        for sys_file in cls.SYSTEM_FILES:
            if sys_file.lower() in filename_lower:
                return True
        
        # Verificar si empieza con $ (archivos NTFS)
        if filename_lower.startswith('$'):
            return True
        
        # Verificar extensiones del sistema
        for ext in cls.SYSTEM_EXTENSIONS:
            if filename_lower.endswith(ext):
                return True
        
        return False


class SystemDirectories:
    """Directorios del sistema y programas instalados a excluir"""
    # Directorios del sistema de Windows
    SYSTEM_DIRECTORIES = [
        r'program files',
        r'program files (x86)',
        r'programdata',
        r'windows',
        r'windows\system32',
        r'windows\syswow64',
        r'windows\winsxs',
        r'windows\assembly',
        r'windows\installer',
        r'windows\temp',
        r'windows\tmp',
        r'$recycle.bin',
        r'system volume information',
        r'recovery',
        r'boot',
        r'perflogs',
        r'programdata\microsoft',
        r'programdata\application data',
    ]
    
    @classmethod
    def is_system_directory(cls, filepath):
        """
        Verifica si una ruta de archivo pertenece a un directorio del sistema
        
        Args:
            filepath: Ruta completa del archivo o solo el nombre
        
        Returns:
            True si la ruta contiene algún directorio del sistema
        """
        if not filepath:
            return False
        
        # Normalizar la ruta (convertir a minúsculas y normalizar separadores)
        filepath_lower = filepath.lower().replace('/', '\\')
        
        # Verificar cada directorio del sistema
        for sys_dir in cls.SYSTEM_DIRECTORIES:
            sys_dir_normalized = sys_dir.lower()
            
            # Buscar el directorio en la ruta con patrones más específicos
            # para evitar falsos positivos (ej: un archivo llamado "myprogram.txt")
            
            # Patrones que indican una ruta real del sistema:
            # 1. C:\Program Files\... (con unidad y barra)
            # 2. \Program Files\... (barra inicial)
            # 3. Program Files\... (al inicio de la ruta o después de una barra)
            patterns = [
                # Patrón con unidad de disco: C:\Program Files\...
                rf'[a-z]:\\{re.escape(sys_dir_normalized)}\\',
                rf'[a-z]:\\{re.escape(sys_dir_normalized)}$',
                # Patrón con barra inicial: \Program Files\...
                rf'\\{re.escape(sys_dir_normalized)}\\',
                rf'\\{re.escape(sys_dir_normalized)}$',
                # Patrón al inicio: Program Files\... (sin unidad, pero con barra después)
                rf'^{re.escape(sys_dir_normalized)}\\',
            ]
            
            for pattern in patterns:
                if re.search(pattern, filepath_lower):
                    return True
        
        return False


class Config:
    """Configuración principal del sistema"""
    def __init__(self):
        self.block_size = BLOCK_SIZE
        self.min_text_len = MIN_TEXT_LEN
        self.window_size = WINDOW_SIZE
        self.overlap = OVERLAP
        self.encodings = CODIFICACIONES.copy()

