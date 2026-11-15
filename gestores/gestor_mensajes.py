"""Mensajes locales de una sesión, persistidos de forma atómica."""
import json
import os
import tempfile
import uuid
import shutil
from datetime import datetime
from gui.imagenes import validar_imagen
from gui.videos import validar_video


class GestorMensajes:
    def __init__(self, ruta, usuarios, amistades, sesion):
        self.ruta = ruta
        self.usuarios = usuarios
        self.amistades = amistades
        self.sesion = sesion

    def _usuario(self):
        usuario = self.sesion()
        if usuario is None or self.usuarios.usuarios_por_nombre.get(usuario.nombre_usuario) is not usuario:
            raise PermissionError("Inicia sesión para acceder a los mensajes.")
        return usuario.nombre_usuario

    def _validar(self, destino):
        usuario = self._usuario()
        if destino not in self.usuarios.usuarios_por_nombre or destino not in self.amistades.obtener_amistades(usuario):
            raise PermissionError("Solo puedes conversar con tus amigos.")
        return usuario

    def _leer(self):
        try:
            with open(self.ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except FileNotFoundError:
            return []
        if not isinstance(datos, list):
            raise ValueError("El archivo de mensajes no es válido.")
        for m in datos:
            if not isinstance(m, dict) or not all(isinstance(m.get(k), str) for k in
                    ("id", "remitente", "destinatario", "fecha", "contenido")) or type(m.get("leido")) is not bool:
                raise ValueError("El archivo de mensajes contiene un registro inválido.")
            datetime.fromisoformat(m["fecha"])
        return datos

    def _guardar(self, datos):
        carpeta = os.path.dirname(self.ruta)
        os.makedirs(carpeta, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".json")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
            os.replace(temporal, self.ruta)
        finally:
            if os.path.exists(temporal):
                os.remove(temporal)

    def ruta_imagen(self, relativa):
        if not isinstance(relativa, str) or not relativa or os.path.isabs(relativa):
            raise ValueError("Ruta de imagen inválida.")
        carpeta = os.path.realpath(os.path.join(os.path.dirname(self.ruta), "imagenes"))
        ruta = os.path.realpath(os.path.join(os.path.dirname(self.ruta), relativa))
        if os.path.commonpath([carpeta, ruta]) != carpeta or ruta == carpeta:
            raise ValueError("Ruta de imagen inválida.")
        return ruta

    def ruta_video(self, relativa):
        if not isinstance(relativa, str) or not relativa or os.path.isabs(relativa):
            raise ValueError("Ruta de video inv\u00e1lida.")
        carpeta = os.path.realpath(os.path.join(os.path.dirname(self.ruta), "videos"))
        ruta = os.path.realpath(os.path.join(os.path.dirname(self.ruta), relativa))
        if os.path.commonpath([carpeta, ruta]) != carpeta or ruta == carpeta:
            raise ValueError("Ruta de video inv\u00e1lida.")
        return ruta

    def enviar(self, destino, contenido, imagen=None, video=None):
        usuario = self._validar(destino)
        if not isinstance(contenido, str) or not (contenido.strip() or imagen or video):
            raise ValueError("Escribe un mensaje o adjunta una imagen o un video.")
        if imagen and video:
            raise ValueError("Adjunta una imagen o un video por mensaje.")
        if len(contenido) > 5000:
            raise ValueError("El mensaje no puede superar 5000 caracteres.")
        datos = self._leer()
        mensaje = dict(id=uuid.uuid4().hex, remitente=usuario, destinatario=destino,
                       fecha=datetime.now().isoformat(timespec="microseconds"),
                       contenido=contenido.strip(), leido=False)
        copiada = None
        try:
            if imagen:
                validar_imagen(imagen, 10 * 1024 * 1024)
                relativa = "imagenes/" + uuid.uuid4().hex + os.path.splitext(imagen)[1].lower()
                copiada = self.ruta_imagen(relativa)
                os.makedirs(os.path.dirname(copiada), exist_ok=True)
                shutil.copyfile(imagen, copiada)
                validar_imagen(copiada, 10 * 1024 * 1024)
                mensaje["ruta_imagen"] = relativa
            elif video:
                validar_video(video)
                relativa = "videos/" + uuid.uuid4().hex + os.path.splitext(video)[1].lower()
                copiada = self.ruta_video(relativa)
                os.makedirs(os.path.dirname(copiada), exist_ok=True)
                shutil.copyfile(video, copiada)
                validar_video(copiada)
                mensaje["ruta_video"] = relativa
            datos.append(mensaje)
            self._guardar(datos)
        except Exception:
            if copiada and os.path.isfile(copiada):
                os.remove(copiada)
            raise
        return mensaje.copy()

    def conversacion(self, destino, marcar=False):
        usuario = self._validar(destino)
        datos = self._leer()
        mensajes = [m for m in datos if {m["remitente"], m["destinatario"]} == {usuario, destino}]
        if marcar:
            pendientes = [m for m in mensajes if m["destinatario"] == usuario and not m["leido"]]
            for m in pendientes:
                m["leido"] = True
            if pendientes:
                self._guardar(datos)
        return sorted(mensajes, key=lambda m: datetime.fromisoformat(m["fecha"]))

    def compartir(self, destinos, identificador, publicaciones):
        destinos = list(dict.fromkeys(destinos))
        if not destinos:
            raise ValueError("Selecciona al menos un amigo.")
        for destino in destinos:
            self._validar(destino)
        if not any(p.identificador == identificador for p in publicaciones.publicaciones):
            raise ValueError("La publicación ya no está disponible.")
        datos = self._leer()
        for destino in destinos:
            datos.append(dict(id=uuid.uuid4().hex, remitente=self._usuario(), destinatario=destino,
                              fecha=datetime.now().isoformat(timespec="microseconds"), contenido="",
                              leido=False, publicacion_id=identificador))
        self._guardar(datos)

    def conversaciones(self):
        usuario = self._usuario()
        amigos = set(self.amistades.obtener_amistades(usuario))
        resultado = {}
        for m in sorted(self._leer(), key=lambda m: datetime.fromisoformat(m["fecha"])):
            if usuario not in (m["remitente"], m["destinatario"]):
                continue
            otro = m["destinatario"] if m["remitente"] == usuario else m["remitente"]
            if otro not in amigos:
                continue
            fila = resultado.setdefault(otro, {"usuario": otro, "no_leidos": 0})
            fila["ultimo"] = m
            fila["no_leidos"] += int(m["destinatario"] == usuario and not m["leido"])
        return sorted(resultado.values(), key=lambda r: r["ultimo"]["fecha"], reverse=True)
