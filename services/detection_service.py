"""Service for file type detection"""

from typing import Optional
from models.config import FileSignatures, MIN_TEXT_LEN
from utils.encoding_utils import is_text


class DetectionService:
    """Servicio para detectar tipos de archivo y contenido"""
    
    @staticmethod
    def detect_file_type(data: bytes) -> Optional[str]:
        """Detecta el tipo de archivo por su firma (magic number)"""
        if not data or len(data) < 4:
            return None
        
        # Verificar firmas conocidas
        for tipo, firmas in FileSignatures.SIGNATURES.items():
            for firma in firmas:
                if firma and data.startswith(firma):
                    return tipo
                # Para tipos de texto sin firma específica, verificar si es texto
                if not firma and tipo in ['txt', 'csv', 'log', 'ini', 'cfg', 'conf']:
                    if is_text(data[:1024], threshold=0.8):
                        return tipo
        
        # Si no tiene firma pero es texto, asumir txt
        if is_text(data[:1024], threshold=0.8):
            return 'txt'
        
        return None

