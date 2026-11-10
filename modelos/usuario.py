"""Modelo que representa a una persona usuaria de CampusConnect."""

from datetime import datetime


class Usuario:
    """Almacena los datos básicos de una cuenta estudiantil."""

    def __init__(self, nombre, nombre_usuario, contrasena, fecha_registro=None):
        """Crea un usuario y asigna la fecha actual si no se proporciona."""
        self.nombre = nombre
        self.nombre_usuario = nombre_usuario
        self.contrasena = contrasena
        self.fecha_registro = fecha_registro or datetime.now().isoformat(timespec="seconds")

    def a_diccionario(self):
        """Devuelve los datos del usuario en un formato serializable a JSON."""
        return {
            "nombre": self.nombre,
            "nombre_usuario": self.nombre_usuario,
            "contrasena": self.contrasena,
            "fecha_registro": self.fecha_registro,
        }

    @classmethod
    def desde_diccionario(cls, datos):
        """Construye un usuario a partir de un diccionario previamente validado."""
        return cls(
            datos["nombre"],
            datos["nombre_usuario"],
            datos["contrasena"],
            datos.get("fecha_registro"),
        )
