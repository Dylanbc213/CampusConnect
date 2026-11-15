"""Avatares circulares con recorte centrado y respaldo por iniciales."""

import os
import tkinter as tk

from gui.imagenes import Image, ImageOps, ImageTk


def foto_circular(ruta, tamano):
    """Carga el primer fotograma y lo centra en un avatar circular."""
    if Image is None:
        if os.path.splitext(ruta)[1].lower() not in (".png", ".gif"):
            return None
        return tk.PhotoImage(file=ruta)
    escala = 4
    lado = tamano * escala
    with Image.open(ruta) as origen:
        origen.seek(0)
        imagen = ImageOps.exif_transpose(origen).convert("RGBA")
        imagen = ImageOps.fit(imagen, (lado, lado), method=Image.Resampling.LANCZOS,
                              centering=(0.5, 0.5))
        mascara = Image.new("L", (lado, lado), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mascara).ellipse((0, 0, lado - 1, lado - 1), fill=255)
        imagen.putalpha(mascara)
        imagen = imagen.resize((tamano, tamano), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(imagen)


def ruta_foto(usuario, carpeta_datos):
    foto = getattr(usuario, "foto_perfil", "")
    return os.path.join(carpeta_datos, foto) if foto and not os.path.isabs(foto) else foto


def dibujar_avatar(canvas, usuario, carpeta_datos, tamano):
    margen = 1
    canvas.create_oval(margen, margen, tamano - margen, tamano - margen,
                       fill="#FCE7EC", outline="")
    try:
        ruta = ruta_foto(usuario, carpeta_datos)
        imagen = foto_circular(ruta, tamano - 2) if ruta and os.path.isfile(ruta) else None
        if imagen:
            canvas.create_image(tamano / 2, tamano / 2, image=imagen)
            canvas._foto_perfil = imagen
            return imagen
    except (OSError, tk.TclError, ValueError):
        pass
    iniciales = "".join(p[0] for p in usuario.nombre_visible.split()[:2]).upper() or "?"
    canvas.create_text(tamano / 2, tamano / 2, text=iniciales, fill="#E4002B",
                       font=("Segoe UI", max(9, tamano // 4), "bold"))
    return None
