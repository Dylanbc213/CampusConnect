"""Validación y vista previa de imágenes, con Pillow opcional requerido para JPG/WEBP."""

import math
import os
import tkinter as tk

try:
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    Image = ImageOps = ImageTk = None


FORMATOS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP", ".gif": "GIF"}
LIMITE_BYTES = 5 * 1024 * 1024


def validar_imagen(ruta):
    extension = os.path.splitext(ruta)[1].lower()
    if extension not in FORMATOS:
        raise ValueError("El formato debe ser JPG, JPEG, PNG, WEBP o GIF.")
    if os.path.getsize(ruta) > LIMITE_BYTES:
        raise ValueError("La imagen no puede superar 5 MB.")
    if Image is not None:
        with Image.open(ruta) as imagen:
            if imagen.format != FORMATOS[extension]:
                raise ValueError("El contenido del archivo no coincide con su extensión.")
            imagen.verify()
        return
    if extension not in (".png", ".gif"):
        raise ValueError("Para abrir JPG, JPEG o WEBP instala las dependencias de requirements.txt (Pillow).")
    with open(ruta, "rb") as archivo:
        firma = archivo.read(8)
    valida = firma.startswith(b"\x89PNG\r\n\x1a\n") if extension == ".png" else firma.startswith((b"GIF87a", b"GIF89a"))
    if not valida:
        raise ValueError("El contenido del archivo no coincide con PNG o GIF.")
    try:
        tk.PhotoImage(file=ruta)
    except tk.TclError as error:
        raise ValueError("Tkinter no puede leer esta imagen.") from error


def cargar_vista_previa(ruta, ancho_maximo, alto_maximo=None):
    """Devuelve una imagen Tk escalada proporcionalmente dentro de los límites dados."""
    if Image is not None:
        with Image.open(ruta) as origen:
            origen.seek(0)
            imagen = ImageOps.exif_transpose(origen).convert("RGBA")
            limites = (max(1, ancho_maximo), max(1, alto_maximo or imagen.height))
            imagen.thumbnail(limites, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(imagen)
    imagen = tk.PhotoImage(file=ruta)
    limites = [max(1, ancho_maximo)]
    if alto_maximo:
        limites.append(max(1, alto_maximo))
    factor = max(1, math.ceil(max(imagen.width() / limites[0], imagen.height() / (limites[1] if len(limites) > 1 else imagen.height()))))
    return imagen.subsample(factor, factor) if factor > 1 else imagen
