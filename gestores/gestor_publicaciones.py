"""Gestión de publicaciones."""

from modelos.publicacion import Publicacion
from persistencia.almacenamiento import cargar_json, guardar_json


class GestorPublicaciones:
    """Mantiene la lista de publicaciones y la persiste en JSON."""

    def __init__(self, ruta_archivo):
        """Carga publicaciones válidas desde el archivo indicado."""
        self.ruta_archivo = ruta_archivo
        self.publicaciones = []
        self._cargar()

    def _cargar(self):
        """Carga las publicaciones y descarta registros mal formados."""
        registros = cargar_json(self.ruta_archivo, [])
        if not isinstance(registros, list):
            print("Advertencia: publicaciones.json debe contener una lista; se usará una lista vacía.")
            return
        for registro in registros:
            if not isinstance(registro, dict):
                continue
            try:
                publicacion = Publicacion.desde_diccionario(registro)
            except (KeyError, TypeError):
                continue
            if (
                not isinstance(publicacion.identificador, int)
                or not isinstance(publicacion.nombre_usuario, str)
                or not publicacion.nombre_usuario
                or not isinstance(publicacion.contenido, str)
                or not publicacion.contenido
            ):
                continue
            self.publicaciones.append(publicacion)

    def crear_publicacion(self, nombre_usuario, contenido):
        """Crea una publicación, la añade a la lista y guarda todos los registros."""
        contenido = contenido.strip()
        if not nombre_usuario or not contenido:
            raise ValueError("El autor y el contenido son obligatorios.")
        identificador = max(
            (publicacion.identificador for publicacion in self.publicaciones
             if isinstance(publicacion.identificador, int)),
            default=0,
        ) + 1
        publicacion = Publicacion(identificador, nombre_usuario, contenido)
        self.publicaciones.append(publicacion)
        self._guardar()
        return publicacion

    def _guardar(self):
        """Persiste la lista de publicaciones."""
        guardar_json(
            self.ruta_archivo,
            [publicacion.a_diccionario() for publicacion in self.publicaciones],
        )
