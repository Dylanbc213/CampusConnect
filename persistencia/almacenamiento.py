"""Funciones reutilizables para leer y guardar archivos JSON."""

import json
import os


def cargar_json(ruta_archivo, valor_predeterminado):
    """Lee un JSON, creando el archivo si falta y recuperándose de contenido inválido."""
    carpeta = os.path.dirname(os.path.abspath(ruta_archivo))
    os.makedirs(carpeta, exist_ok=True)
    if not os.path.exists(ruta_archivo):
        guardar_json(ruta_archivo, valor_predeterminado)
        return valor_predeterminado
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
        if not contenido.strip():
            return valor_predeterminado
        return json.loads(contenido)
    except (json.JSONDecodeError, OSError) as error:
        print("Advertencia: no se pudo leer {}: {}".format(ruta_archivo, error))
        return valor_predeterminado


def guardar_json(ruta_archivo, datos):
    """Guarda datos en JSON UTF-8 y crea la carpeta de destino si es necesario."""
    carpeta = os.path.dirname(os.path.abspath(ruta_archivo))
    os.makedirs(carpeta, exist_ok=True)
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)
