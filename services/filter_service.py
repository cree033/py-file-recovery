"""Service for file filtering"""

import os
import re
from typing import Optional, List
from models.config import SystemFiles, SystemDirectories
from services.detection_service import DetectionService


class FilterService:
    """Service for filtering files according to criteria"""
    
    @staticmethod
    def convert_wildcard_to_regex(pattern: str) -> Optional[str]:
        """Converts a pattern with wildcards (* and %) to regular expression"""
        if not pattern:
            return None
        
        # Escapar caracteres especiales de regex excepto * y %
        patron_escaped = re.escape(pattern)
        
        # Reemplazar los wildcards escapados por sus equivalentes regex
        # * = cualquier secuencia de caracteres (0 o más)
        # % = uno o más caracteres (más flexible que solo uno)
        patron_escaped = patron_escaped.replace(r'\*', '.*')
        patron_escaped = patron_escaped.replace(r'\%', '.+')
        
        # También manejar si el usuario usa * o % sin escapar
        patron_escaped = patron_escaped.replace('*', '.*')
        patron_escaped = patron_escaped.replace('%', '.+')
        
        return patron_escaped
    
    @staticmethod
    def matches_search(nombre: str, nombre_busqueda: Optional[str] = None, 
                      tipos_permitidos: Optional[List[str]] = None) -> bool:
        """Checks if a file matches search criteria using wildcards"""
        if not nombre:
            return False
        
        nombre_lower = nombre.lower()
        
        # Si hay búsqueda específica por nombre
        if nombre_busqueda:
            busqueda_lower = nombre_busqueda.lower()
            
            # Separar nombre y extensión del patrón de búsqueda
            busqueda_sin_ext, busqueda_ext = os.path.splitext(busqueda_lower)
            nombre_sin_ext, nombre_ext = os.path.splitext(nombre_lower)
            
            # Verificar si el patrón contiene wildcards
            tiene_wildcards = '*' in busqueda_lower or '%' in busqueda_lower
            
            if tiene_wildcards:
                # Usar regex para búsqueda con wildcards
                if busqueda_ext:
                    # Convertir wildcards a regex
                    patron_regex = FilterService.convert_wildcard_to_regex(busqueda_lower)
                    if patron_regex:
                        try:
                            if re.match(f'^{patron_regex}$', nombre_lower, re.IGNORECASE):
                                return True
                        except:
                            pass
                else:
                    # Solo buscar en el nombre (sin extensión)
                    patron_regex = FilterService.convert_wildcard_to_regex(busqueda_sin_ext)
                    if patron_regex:
                        try:
                            if re.match(f'^{patron_regex}$', nombre_sin_ext, re.IGNORECASE):
                                return True
                        except:
                            pass
            else:
                # Búsqueda simple sin wildcards (búsqueda parcial)
                if busqueda_ext:
                    # Si incluye extensión, buscar en nombre completo
                    if busqueda_lower == nombre_lower or busqueda_lower in nombre_lower:
                        return True
                else:
                    # Si no incluye extensión, buscar solo en el nombre (sin extensión)
                    # Pero también permitir búsqueda parcial
                    if busqueda_sin_ext in nombre_sin_ext or busqueda_sin_ext in nombre_lower:
                        return True
                    # También buscar si el nombre empieza con el patrón
                    if nombre_sin_ext.startswith(busqueda_sin_ext):
                        return True
        
        # Si hay tipos permitidos, verificar extensión
        if tipos_permitidos:
            ext = os.path.splitext(nombre_lower)[1].lstrip('.')
            if ext not in tipos_permitidos:
                return False
        
        return True
    
    @staticmethod
    def apply_filters(nombre: str, datos: bytes, tipos_archivo: Optional[List[str]] = None,
                     nombre_busqueda: Optional[str] = None, filtrar_sistema: bool = True):
        """Applies all filters to a file before saving it"""
        if not nombre:
            return False, None
        
        # 1. Filtrar archivos del sistema
        if filtrar_sistema and SystemFiles.is_system_file(nombre):
            return False, None
        
        # 1.5. Filtrar archivos de directorios del sistema y programas instalados
        if filtrar_sistema and SystemDirectories.is_system_directory(nombre):
            return False, None
        
        # 2. Detectar tipo de archivo
        tipo_detectado = DetectionService.detect_file_type(datos) if datos else None
        
        # 3. Verificar tipo de archivo permitido (STRICT CHECK)
        if tipos_archivo:
            # Get extension from filename
            ext_from_name = os.path.splitext(nombre)[1].lstrip('.').lower()
            
            # Determine final type: prefer extension from name, then detected type
            final_type = None
            if ext_from_name:
                final_type = ext_from_name
            elif tipo_detectado:
                final_type = tipo_detectado
            
            # STRICT: Must have a type and it must be in allowed types
            if not final_type:
                # If no type can be determined, reject if types are specified
                return False, None
            
            if final_type not in tipos_archivo:
                return False, tipo_detectado
        
        # 4. Verificar búsqueda por nombre
        if nombre_busqueda and not FilterService.matches_search(nombre, nombre_busqueda):
            return False, tipo_detectado
        
        return True, tipo_detectado

