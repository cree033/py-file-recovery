"""Utilidades para detección de codificación y texto"""

import string
from models.config import CODIFICACIONES, MIN_TEXT_LEN


def is_text(data, threshold=0.7):
    """Detección mejorada de texto con múltiples umbrales"""
    if not data or len(data) < 10:
        return False
    
    imprimibles = bytes(string.printable, "ascii")
    validos = sum(b in imprimibles for b in data)
    ratio = validos / len(data)
    
    # Verificar si hay secuencias de caracteres imprimibles
    max_secuencia = 0
    secuencia_actual = 0
    
    for b in data:
        if b in imprimibles:
            secuencia_actual += 1
            max_secuencia = max(max_secuencia, secuencia_actual)
        else:
            if secuencia_actual >= 10:
                pass
            secuencia_actual = 0
    
    # Criterios múltiples para detectar texto
    return (ratio >= threshold) or (max_secuencia >= 50 and ratio >= 0.5)


def detect_encoding(data):
    """Intenta detectar la codificación del texto"""
    for codif in CODIFICACIONES:
        try:
            texto = data.decode(codif)
            # Verificar que sea texto válido
            if len(texto.strip()) >= MIN_TEXT_LEN:
                return codif, texto
        except:
            continue
    return None, None

