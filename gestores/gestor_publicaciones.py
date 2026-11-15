"""Gestión de publicaciones."""

import os
import tempfile
from datetime import datetime

from modelos.publicacion import Publicacion, REACCIONES
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
        self.publicaciones = []
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
                or not (publicacion.contenido.strip() or publicacion.ruta_imagen)
            ):
                continue
            self.publicaciones.append(publicacion)

    def recargar(self):
        """Vuelve a leer las publicaciones y comentarios desde el archivo JSON."""
        self._cargar()
        return list(self.publicaciones)

    def crear_publicacion(self, nombre_usuario, contenido, ruta_imagen=""):
        """Crea una publicación, la añade a la lista y guarda todos los registros."""
        contenido = contenido or ""
        ruta_imagen = ruta_imagen or ""
        if len(contenido) > self.LIMITE_CARACTERES:
            raise ValueError("La publicación no puede superar los 500 caracteres.")
        contenido = contenido.strip()
        if not nombre_usuario.strip() or not (contenido or ruta_imagen):
            raise ValueError("La publicación debe incluir texto o una imagen.")
        if not isinstance(ruta_imagen, str):
            raise ValueError("La ruta de imagen no es válida.")
        identificador = max(
            (publicacion.identificador for publicacion in self.publicaciones
             if isinstance(publicacion.identificador, int)),
            default=0,
        ) + 1
        publicacion = Publicacion(identificador, nombre_usuario, contenido, ruta_imagen=ruta_imagen)
        self.publicaciones.append(publicacion)
        try:
            self._guardar()
        except OSError:
            self.publicaciones.remove(publicacion)
            raise
        return publicacion

    def obtener_publicaciones_usuario(self, nombre_usuario):
        return self._ordenar_publicaciones(
            p for p in self.publicaciones if p.nombre_usuario == nombre_usuario
        )

    def obtener_publicaciones_inicio(self, nombre_usuario, gestor_amistades):
        autores = set(gestor_amistades.obtener_amistades(nombre_usuario))
        autores.add(nombre_usuario)
        resultado, identificadores = [], set()
        for publicacion in self.publicaciones:
            if publicacion.nombre_usuario in autores and publicacion.identificador not in identificadores:
                resultado.append(publicacion)
                identificadores.add(publicacion.identificador)
        return self._ordenar_publicaciones(resultado)

    def agregar_comentario(self, identificador, nombre_usuario, contenido, ruta_imagen="", parent_id=None):
        contenido = (contenido or "").strip()
        ruta_imagen = ruta_imagen or ""
        if not nombre_usuario or not nombre_usuario.strip():
            raise ValueError("El autor de la respuesta es obligatorio.")
        if not (contenido or ruta_imagen):
            raise ValueError("La respuesta debe incluir texto o una imagen.")
        if not isinstance(ruta_imagen, str):
            raise ValueError("La ruta de imagen no es válida.")
        publicacion = next((p for p in self.publicaciones if p.identificador == identificador), None)
        if publicacion is None:
            raise ValueError("La publicación ya no está disponible.")
        if parent_id is not None and type(parent_id) is not int:
            raise ValueError("La referencia de la respuesta no es válida.")
        if parent_id is not None and not any(
                comentario["id"] == parent_id for comentario in publicacion.comentarios):
            raise ValueError("La respuesta a la que intentas responder ya no está disponible.")
        parent_type = "respuesta" if parent_id is not None else "publicacion"
        parent_id = parent_id if parent_id is not None else publicacion.identificador
        nuevo_id = max((comentario["id"] for comentario in publicacion.comentarios), default=0) + 1
        comentario = {
            "id": nuevo_id,
            "parent_id": parent_id,
            "parent_type": parent_type,
            "nombre_usuario": nombre_usuario,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "contenido": contenido,
            "ruta_imagen": ruta_imagen,
        }
        publicacion.comentarios.append(comentario)
        try:
            self._guardar()
        except OSError:
            publicacion.comentarios.pop()
            raise
        return comentario

    def establecer_reaccion(self, identificador, nombre_usuario, reaccion):
        if not nombre_usuario or not nombre_usuario.strip():
            raise ValueError("El usuario es obligatorio para reaccionar.")
        if reaccion not in REACCIONES:
            raise ValueError("Selecciona una reacción válida.")
        publicacion = next((p for p in self.publicaciones if p.identificador == identificador), None)
        if publicacion is None:
            raise ValueError("La publicación ya no está disponible.")
        anterior = publicacion.reacciones.get(nombre_usuario)
        publicacion.reacciones[nombre_usuario] = reaccion
        try:
            self._guardar()
        except OSError:
            if anterior is None:
                publicacion.reacciones.pop(nombre_usuario, None)
            else:
                publicacion.reacciones[nombre_usuario] = anterior
            raise
        return reaccion

    def quitar_reaccion(self, identificador, nombre_usuario):
        if not nombre_usuario or not nombre_usuario.strip():
            raise ValueError("El usuario es obligatorio para quitar la reacción.")
        publicacion = next((p for p in self.publicaciones if p.identificador == identificador), None)
        if publicacion is None:
            raise ValueError("La publicación ya no está disponible.")
        anterior = publicacion.reacciones.pop(nombre_usuario, None)
        if anterior is None:
            return False
        try:
            self._guardar()
        except OSError:
            publicacion.reacciones[nombre_usuario] = anterior
            raise
        return True

    def obtener_publicaciones_amigos(self, nombre_usuario, gestor_amistades):
        amigos = set(gestor_amistades.obtener_amistades(nombre_usuario))
        return self._ordenar_publicaciones(p for p in self.publicaciones if p.nombre_usuario in amigos)

    @staticmethod
    def _ordenar_publicaciones(publicaciones):
        """Ordena por fecha descendente; empata por ID y deja inválidas al final."""
        def clave(publicacion):
            try:
                fecha = datetime.fromisoformat(publicacion.fecha.replace("Z", "+00:00"))
                marca_tiempo = fecha.timestamp()
            except (AttributeError, TypeError, ValueError, OverflowError, OSError):
                return (0, float("-inf"), publicacion.identificador)
            return (1, marca_tiempo, publicacion.identificador)

        return sorted(publicaciones, key=clave, reverse=True)

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
