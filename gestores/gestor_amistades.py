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
        self._cargar()

    def _cargar(self):
        """Carga un diccionario válido y normaliza sus listas de amistades."""
        datos = cargar_json(self.ruta_archivo, {})
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

    def agregar_amistad(self, usuario_a, usuario_b):
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

    def _guardar(self):
        """Persiste la lista de adyacencia."""
        carpeta = os.path.dirname(os.path.abspath(self.ruta_archivo))
        descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".json")
        os.close(descriptor)
        try:
            guardar_json(temporal, self.adyacencias)
            os.replace(temporal, self.ruta_archivo)
        finally:
            if os.path.exists(temporal):
                os.remove(temporal)
