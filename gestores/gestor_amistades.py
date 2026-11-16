"""Gestión de amistades mediante una lista de adyacencia."""

import os
import tempfile

from persistencia.almacenamiento import cargar_json, guardar_json


class GestorAmistades:
    """Administra relaciones simétricas entre nombres de usuario."""

    def __init__(self, ruta_archivo, gestor_usuarios=None):
        """Carga la lista de adyacencia desde el archivo JSON."""
        self.ruta_archivo = ruta_archivo
        self.gestor_usuarios = gestor_usuarios
        self.adyacencias = {}
        self.solicitudes = []
        self._cargar()

    def _cargar(self):
        """Carga un diccionario válido y normaliza sus listas de amistades."""
        datos = cargar_json(self.ruta_archivo, {})
        if isinstance(datos, dict) and datos.get("version") == 2:
            pendientes = datos.get("solicitudes", [])
            self.solicitudes = [r for r in pendientes if isinstance(r, dict)
                                and isinstance(r.get("emisor"), str)
                                and isinstance(r.get("receptor"), str)
                                and r["emisor"] != r["receptor"]] if isinstance(pendientes, list) else []
            datos = datos.get("amistades", {})
        if not isinstance(datos, dict):
            print("Advertencia: amistades.json debe contener un objeto; se usará uno vacío.")
            return
        for nombre_usuario, amistades in datos.items():
            if isinstance(nombre_usuario, str) and isinstance(amistades, list):
                self.adyacencias[nombre_usuario] = list(
                    dict.fromkeys(
                        amigo for amigo in amistades
                        if isinstance(amigo, str) and amigo != nombre_usuario
                    )
                )

        for usuario, amigos in list(self.adyacencias.items()):
            for amigo in list(amigos):
                inversas = self.adyacencias.setdefault(amigo, [])
                if usuario not in inversas:
                    inversas.append(usuario)

    def _confirmar_amistad(self, usuario_a, usuario_b):
        """Añade una amistad en ambas direcciones y guarda el cambio."""
        if usuario_a == usuario_b:
            raise ValueError("Una persona no puede agregarse a sí misma.")
        if self.gestor_usuarios is not None:
            usuarios = self.gestor_usuarios.usuarios_por_nombre
            if usuario_a not in usuarios or usuario_b not in usuarios:
                raise ValueError("Ambos usuarios deben estar registrados.")
        if usuario_b in self.adyacencias.get(usuario_a, []):
            raise ValueError("Estos usuarios ya son amigos.")
        anteriores = {usuario: list(amigos) for usuario, amigos in self.adyacencias.items()}
        self.adyacencias.setdefault(usuario_a, [])
        self.adyacencias.setdefault(usuario_b, [])
        if usuario_b not in self.adyacencias[usuario_a]:
            self.adyacencias[usuario_a].append(usuario_b)
        if usuario_a not in self.adyacencias[usuario_b]:
            self.adyacencias[usuario_b].append(usuario_a)
        try:
            self._guardar()
        except OSError:
            self.adyacencias = anteriores
            raise

    def obtener_amistades(self, nombre_usuario):
        """Devuelve una copia de la lista de amistades del usuario indicado."""
        return list(self.adyacencias.get(nombre_usuario, []))

    def estado_solicitud(self, emisor, receptor):
        if {"emisor": emisor, "receptor": receptor} in self.solicitudes:
            return "enviada"
        if {"emisor": receptor, "receptor": emisor} in self.solicitudes:
            return "recibida"
        return ""

    def agregar_amistad(self, emisor, receptor):
        """Envía una invitación; nunca crea una amistad sin aceptación."""
        if not emisor or not receptor or emisor == receptor:
            raise ValueError("Selecciona a otra persona para enviar la solicitud.")
        if self.gestor_usuarios is not None:
            usuarios = self.gestor_usuarios.usuarios_por_nombre
            if emisor not in usuarios or receptor not in usuarios:
                raise ValueError("Ambos usuarios deben estar registrados.")
        if receptor in self.obtener_amistades(emisor):
            raise ValueError("Ya son amigos.")
        if self.estado_solicitud(emisor, receptor):
            raise ValueError("Ya existe una solicitud pendiente entre ambos.")
        solicitud = {"emisor": emisor, "receptor": receptor}
        self.solicitudes.append(solicitud)
        try:
            self._guardar()
        except OSError:
            self.solicitudes.remove(solicitud)
            raise

    def aceptar_solicitud(self, receptor, emisor):
        solicitud = {"emisor": emisor, "receptor": receptor}
        if solicitud not in self.solicitudes:
            raise ValueError("No tienes una solicitud pendiente de esta persona.")
        anteriores = list(self.solicitudes)
        self.solicitudes.remove(solicitud)
        try:
            self._confirmar_amistad(emisor, receptor)
        except (OSError, ValueError):
            self.solicitudes = anteriores
            raise

    def rechazar_solicitud(self, receptor, emisor):
        solicitud = {"emisor": emisor, "receptor": receptor}
        if solicitud not in self.solicitudes:
            raise ValueError("No tienes una solicitud pendiente de esta persona.")
        anteriores = list(self.solicitudes)
        self.solicitudes.remove(solicitud)
        try:
            self._guardar()
        except OSError:
            self.solicitudes = anteriores
            raise

    def _guardar(self):
        """Persiste la lista de adyacencia."""
        carpeta = os.path.dirname(os.path.abspath(self.ruta_archivo))
        descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".json")
        os.close(descriptor)
        try:
            guardar_json(temporal, {"version": 2, "amistades": self.adyacencias,
                                   "solicitudes": self.solicitudes})
            os.replace(temporal, self.ruta_archivo)
        finally:
            if os.path.exists(temporal):
                os.remove(temporal)
