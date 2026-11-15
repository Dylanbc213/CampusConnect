"""Validación y apertura de videos cortos adjuntos."""

import os
import shutil
import subprocess
import webbrowser


EXTENSIONES_VIDEO = {".mp4", ".webm", ".mov"}
LIMITE_VIDEO = 25 * 1024 * 1024
DURACION_MAXIMA = 60


def validar_video(ruta, limite_bytes=LIMITE_VIDEO):
    extension = os.path.splitext(ruta)[1].lower()
    if extension not in EXTENSIONES_VIDEO:
        raise ValueError("El video debe estar en formato MP4, WebM o MOV.")
    if not os.path.isfile(ruta):
        raise ValueError("No se encontró el archivo de video.")
    if os.path.getsize(ruta) > limite_bytes:
        raise ValueError("El video no puede superar 25 MB.")
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            resultado = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", ruta],
                capture_output=True, text=True, timeout=8, check=True)
            duracion = float(resultado.stdout.strip())
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            raise ValueError("No se pudo comprobar la duración del video.") from error
        if duracion > DURACION_MAXIMA:
            raise ValueError("El video no puede durar más de 60 segundos.")


def abrir_video(ruta):
    ruta = os.path.abspath(ruta)
    if not os.path.isfile(ruta):
        raise OSError("El archivo de video ya no está disponible.")
    abrir = getattr(os, "startfile", None)
    if abrir:
        abrir(ruta)
    else:
        webbrowser.open("file://" + ruta.replace(os.sep, "/"))
