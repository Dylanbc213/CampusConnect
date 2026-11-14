"""Gestión de publicaciones."""

import os
import tempfile

from modelos.publicacion import Publicacion
from persistencia.almacenamiento import cargar_json, guardar_json


class GestorPublicaciones:
    """Mantiene la lista de publicaciones y la persiste en JSON."""

    LIMITE_CARACTERES = 500

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
        if len(contenido) > self.LIMITE_CARACTERES:
            raise ValueError("La publicación no puede superar los 500 caracteres.")
        contenido = contenido.strip()
        if not nombre_usuario.strip() or not contenido:
            raise ValueError("El autor y el contenido son obligatorios.")
        identificador = max(
            (publicacion.identificador for publicacion in self.publicaciones
             if isinstance(publicacion.identificador, int)),
            default=0,
        ) + 1
        publicacion = Publicacion(identificador, nombre_usuario, contenido)
        self.publicaciones.append(publicacion)
        try:
            self._guardar()
        except OSError:
            self.publicaciones.remove(publicacion)
            raise
        return publicacion

    def obtener_publicaciones_usuario(self, nombre_usuario):
        return [p for p in self.publicaciones if p.nombre_usuario == nombre_usuario]

    def obtener_publicaciones_amigos(self, nombre_usuario, gestor_amistades):
        amigos = set(gestor_amistades.obtener_amistades(nombre_usuario))
        return [p for p in self.publicaciones if p.nombre_usuario in amigos]

    def _guardar(self):
        """Persiste la lista de publicaciones."""
        carpeta = os.path.dirname(os.path.abspath(self.ruta_archivo))
        descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".json")
        os.close(descriptor)
        try:
            guardar_json(temporal, [p.a_diccionario() for p in self.publicaciones])
            os.replace(temporal, self.ruta_archivo)
        finally:
            if os.path.exists(temporal):
                os.remove(temporal)
