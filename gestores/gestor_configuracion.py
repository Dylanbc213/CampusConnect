"""Preferencias de apariencia almacenadas aparte de los datos de usuario."""

import os
import tempfile

from persistencia.almacenamiento import cargar_json, guardar_json


class GestorConfiguracion:
    TEMAS = ("claro", "oscuro")

    def __init__(self, ruta_archivo):
        self.ruta_archivo = ruta_archivo
        datos = cargar_json(ruta_archivo, {})
        tema = datos.get("tema") if isinstance(datos, dict) else None
        self.tema = tema if tema in self.TEMAS else "claro"

    def establecer_tema(self, tema):
        if tema not in self.TEMAS:
            raise ValueError("El tema debe ser claro u oscuro.")
        carpeta = os.path.dirname(os.path.abspath(self.ruta_archivo))
        os.makedirs(carpeta, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".json")
        os.close(descriptor)
        try:
            guardar_json(temporal, {"tema": tema})
            os.replace(temporal, self.ruta_archivo)
        finally:
            if os.path.exists(temporal):
                os.remove(temporal)
        self.tema = tema
        return tema
