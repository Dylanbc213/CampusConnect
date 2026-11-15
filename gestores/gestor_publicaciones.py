"""Gestión de publicaciones."""

import os
import tempfile
from datetime import datetime

from modelos.publicacion import Publicacion, REACCIONES
from persistencia.almacenamiento import cargar_json, guardar_json


class VistaRepost:
    """Referencia de presentación; el contenido siempre pertenece al original."""
    def __init__(self, original, registro):
        self.original = original
        self.reposteador = registro["nombre_usuario"]
        self.fecha_repost = registro["fecha"]

    def __getattr__(self, nombre):
        return getattr(self.original, nombre)


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
        self.reposts = []
        registros = cargar_json(self.ruta_archivo, [])
        if not isinstance(registros, list):
            print("Advertencia: publicaciones.json debe contener una lista; se usará una lista vacía.")
            return
        for registro in registros:
            if not isinstance(registro, dict):
                continue
            if registro.get("tipo") == "repost":
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
        originales = {p.identificador: p for p in self.publicaciones}
        vistos = set()
        for r in registros:
            if not isinstance(r, dict) or r.get("tipo") != "repost":
                continue
            usuario, referencia = r.get("nombre_usuario"), r.get("original_id")
            if not isinstance(usuario, str) or not usuario.strip() or type(referencia) is not int:
                continue
            if referencia not in originales or originales[referencia].nombre_usuario == usuario:
                continue
            if not isinstance(r.get("fecha"), str) or (usuario, referencia) in vistos:
                continue
            vistos.add((usuario, referencia))
            self.reposts.append({"tipo": "repost", "nombre_usuario": usuario,
                                 "original_id": referencia, "fecha": r["fecha"]})

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
        return self._feed({nombre_usuario})

    def _feed(self, autores):
        originales = {p.identificador: p for p in self.publicaciones}
        entradas = [p for p in originales.values() if p.nombre_usuario in autores]
        entradas.extend(VistaRepost(originales[r["original_id"]], r) for r in self.reposts
                        if r["nombre_usuario"] in autores and r["original_id"] in originales)
        return self._ordenar_publicaciones(entradas)

    def repostear(self, identificador, nombre_usuario):
        original = next((p for p in self.publicaciones if p.identificador == identificador), None)
        if original is None:
            raise ValueError("La publicación ya no está disponible.")
        if not isinstance(nombre_usuario, str) or not nombre_usuario.strip():
            raise ValueError("El usuario es obligatorio.")
        if original.nombre_usuario == nombre_usuario:
            raise PermissionError("Solo puedes repostear publicaciones ajenas.")
        if self.tiene_repost(identificador, nombre_usuario):
            raise ValueError("Ya reposteaste esta publicación.")
        registro = {"tipo": "repost", "original_id": identificador,
                    "nombre_usuario": nombre_usuario, "fecha": datetime.now().isoformat(timespec="seconds")}
        self.reposts.append(registro)
        try:
            self._guardar()
        except Exception:
            self.reposts.remove(registro)
            raise

    def tiene_repost(self, identificador, nombre_usuario):
        return any(r["original_id"] == identificador and r["nombre_usuario"] == nombre_usuario
                   for r in self.reposts)

    def contar_reposts(self, identificador):
        return sum(r["original_id"] == identificador for r in self.reposts)

    def deshacer_repost(self, identificador, nombre_usuario):
        anteriores = self.reposts
        self.reposts = [r for r in anteriores if not (
            r["original_id"] == identificador and r["nombre_usuario"] == nombre_usuario)]
        try:
            self._guardar()
        except Exception:
            self.reposts = anteriores
            raise

    def eliminar_publicacion(self, identificador, nombre_usuario):
        publicacion = next((p for p in self.publicaciones if p.identificador == identificador), None)
        if publicacion is None:
            raise ValueError("La publicación ya no está disponible.")
        if not nombre_usuario or publicacion.nombre_usuario != nombre_usuario:
            raise PermissionError("Solo el autor puede eliminar esta publicación.")
        anteriores = self.publicaciones
        reposts_anteriores = self.reposts
        self.reposts = [r for r in self.reposts if r["original_id"] != identificador]
        self.publicaciones = [p for p in anteriores if p is not publicacion]
        try:
            self._guardar()
        except Exception:
            self.publicaciones = anteriores
            self.reposts = reposts_anteriores
            raise
        # Respuestas y reacciones pertenecen al registro eliminado. Se conservan
        # los archivos de imágenes, que pueden estar referenciados en otros contenidos.

    def obtener_publicaciones_inicio(self, nombre_usuario, gestor_amistades):
        autores = set(gestor_amistades.obtener_amistades(nombre_usuario))
        autores.add(nombre_usuario)
        return self._feed(autores)

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
        return self._feed(set(amigos))

    @staticmethod
    def _ordenar_publicaciones(publicaciones):
        """Ordena por fecha descendente; empata por ID y deja inválidas al final."""
        def clave(publicacion):
            try:
                fecha = datetime.fromisoformat(getattr(publicacion, "fecha_repost", publicacion.fecha).replace("Z", "+00:00"))
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
            guardar_json(temporal, [p.a_diccionario() for p in self.publicaciones] + self.reposts)
            os.replace(temporal, self.ruta_archivo)
        finally:
            if os.path.exists(temporal):
                os.remove(temporal)
