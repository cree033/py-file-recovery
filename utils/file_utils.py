"""Utilidades para manejo de archivos y nombres"""

import os
import re
from collections import Counter
from models.config import CODIFICACIONES, MIN_TEXT_LEN


def clean_filename(nombre):
    """Limpia un nombre de archivo eliminando caracteres inválidos"""
    if not nombre:
        return None
    
    # Convertir a string si es necesario
    if not isinstance(nombre, str):
        try:
            nombre = str(nombre)
        except:
            return None
    
    # Eliminar caracteres nulos y otros caracteres de control
    nombre = ''.join(c for c in nombre if c.isprintable() or c in ' \t')
    
    # Eliminar caracteres inválidos para nombres de archivo en Windows
    caracteres_invalidos = '<>:"|?*\\/\x00\r\n\t'
    for char in caracteres_invalidos:
        nombre = nombre.replace(char, '_')
    
    # Eliminar caracteres no ASCII problemáticos (excepto letras acentuadas comunes)
    nombre_limpio = ''
    for c in nombre:
        if c.isascii() or c in 'áéíóúÁÉÍÓÚñÑ':
            nombre_limpio += c
        elif c.isalnum():
            nombre_limpio += c
        else:
            nombre_limpio += '_'
    
    nombre = nombre_limpio
    
    # Eliminar espacios al inicio y final
    nombre = nombre.strip()
    
    # Eliminar puntos al final (excepto la extensión)
    while nombre.endswith('.') and len(nombre) > 1:
        nombre = nombre[:-1]
    
    # Eliminar espacios múltiples y reemplazar por un solo espacio
    nombre = re.sub(r'\s+', ' ', nombre)
    
    # Eliminar guiones y guiones bajos múltiples
    nombre = re.sub(r'[-_]{2,}', '_', nombre)
    
    # Si el nombre está vacío o es muy corto, retornar None
    if len(nombre) < 1:
        return None
    
    # Limitar longitud
    if len(nombre) > 200:
        nombre = nombre[:200]
    
    # Asegurar que no empiece con punto, espacio o guion
    nombre = nombre.lstrip('. -_')
    
    # Si después de limpiar está vacío, retornar None
    if not nombre or len(nombre) < 1:
        return None
    
    # Verificar que tenga al menos una letra
    if not re.search(r'[a-zA-Z]', nombre):
        return None
    
    return nombre


def extract_filename_from_content(texto, datos_raw=None):
    """Intenta extraer el nombre del archivo del contenido del texto"""
    nombres_candidatos = []
    
    # Buscar en las primeras líneas del texto (donde es más probable encontrar metadatos)
    # Aumentar el rango para capturar más nombres
    lineas_relevantes = texto.split('\n')[:50]
    texto_busqueda = '\n'.join(lineas_relevantes)
    
    # También buscar en todo el texto si es pequeño (menos de 10KB)
    if len(texto) < 10000:
        texto_busqueda = texto
    
    # Patrón 1: Nombres de archivos con contexto específico (más confiable)
    patrones_nombres = [
        # Patrones con contexto claro (prioridad alta)
        r'(?:filename|file name|nombre archivo|archivo|file)[:\s=]+["\']?([a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ\s]{1,80}\.[a-zA-Z0-9]{2,5})["\']?',
        r'(?:saved as|guardado como|save as|guardado|saved)[:\s=]+["\']?([a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ\s]{1,80}\.[a-zA-Z0-9]{2,5})["\']?',
        r'(?:document|documento|file|archivo)\s+name[:\s=]+["\']?([a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ\s]{1,80}\.[a-zA-Z0-9]{2,5})["\']?',
        # Nombres de archivo al inicio de línea (más probable que sea un nombre real)
        r'^([a-zA-Z][a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ\s]{2,70}\.[a-zA-Z0-9]{2,5})',
        # Rutas completas de Windows (solo si tienen estructura válida)
        r'([A-Z]:\\[a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ\\\s]{5,100}\.[a-zA-Z0-9]{2,5})',
        # Nombres entre comillas o comillas simples
        r'["\']([a-zA-Z][a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ\s]{2,70}\.[a-zA-Z0-9]{2,5})["\']',
        # Nombres después de palabras clave comunes
        r'(?:title|título|name|nombre)[:\s=]+["\']?([a-zA-Z][a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ\s]{2,70}\.[a-zA-Z0-9]{2,5})["\']?',
    ]
    
    for patron in patrones_nombres:
        matches = re.findall(patron, texto_busqueda, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                nombre = match[0] if match[0] else match[1] if len(match) > 1 else None
            else:
                nombre = match
            if nombre:
                # Limpiar el nombre
                nombre = nombre.strip('"\' \t\r\n')
                if os.path.sep in nombre:
                    nombre = os.path.basename(nombre)
                # Validar que sea un nombre válido
                if is_valid_filename(nombre):
                    nombres_candidatos.append(nombre)
    
    # Filtrar y validar todos los candidatos
    nombres_validos = []
    for nombre in nombres_candidatos:
        nombre_limpio = clean_filename(nombre)
        if nombre_limpio and is_valid_filename(nombre_limpio):
            nombres_validos.append(nombre_limpio)
    
    # Retornar el mejor candidato (el más común o el primero válido)
    if nombres_validos:
        # Contar frecuencia - el más común es probablemente el correcto
        contador = Counter(nombres_validos)
        mejor_nombre = contador.most_common(1)[0][0]
        return mejor_nombre
    
    return None


def is_valid_filename(nombre):
    """Valida si un string parece ser un nombre de archivo real"""
    if not nombre or len(nombre) < 3 or len(nombre) > 200:
        return False
    
    # No debe tener demasiados caracteres especiales consecutivos
    if re.search(r'[_\-\s]{3,}', nombre):
        return False
    
    # Debe tener al menos una letra
    if not re.search(r'[a-zA-Z]', nombre):
        return False
    
    # No debe tener demasiados caracteres no imprimibles
    caracteres_imprimibles = sum(1 for c in nombre if c.isprintable() or c in ' \t')
    if caracteres_imprimibles / len(nombre) < 0.8:
        return False
    
    # No debe ser solo números y caracteres especiales
    if re.match(r'^[\d\s_\-\.]+$', nombre):
        return False
    
    # No debe tener secuencias sospechosas (muchos caracteres repetidos)
    if re.search(r'(.)\1{4,}', nombre):
        return False
    
    return True

