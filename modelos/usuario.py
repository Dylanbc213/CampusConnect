"""Modelo que representa a una persona usuaria de CampusConnect."""

from datetime import datetime


class Usuario:
    """Almacena los datos básicos de una cuenta estudiantil."""

    def __init__(self, nombre, nombre_usuario, contrasena, fecha_registro=None,
                 nombre_visible=None, biografia="", foto_perfil=""):
        """Crea un usuario y asigna la fecha actual si no se proporciona."""
        self.nombre = nombre
        self.nombre_usuario = nombre_usuario
        self.contrasena = contrasena
        self.fecha_registro = fecha_registro or datetime.now().isoformat(timespec="seconds")
        self.nombre_visible = nombre_visible or nombre
        self.biografia = biografia if isinstance(biografia, str) else ""
        self.foto_perfil = foto_perfil if isinstance(foto_perfil, str) else ""

    def a_diccionario(self):
        """Devuelve los datos del usuario en un formato serializable a JSON."""
        return {
            "nombre": self.nombre,
            "nombre_usuario": self.nombre_usuario,
            "contrasena": self.contrasena,
            "fecha_registro": self.fecha_registro,
            "nombre_visible": self.nombre_visible,
            "biografia": self.biografia,
            "foto_perfil": self.foto_perfil,
        }

    @classmethod
    def desde_diccionario(cls, datos):
        """Construye un usuario a partir de un diccionario previamente validado."""
        return cls(
            datos["nombre"],
            datos["nombre_usuario"],
            datos["contrasena"],
            datos.get("fecha_registro"),
            datos.get("nombre_visible", datos["nombre"]),
            datos.get("biografia", ""),
            datos.get("foto_perfil", ""),
        )
