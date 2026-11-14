"""Modelo de una publicación estudiantil."""

from datetime import datetime


class Publicacion:
    """Representa una publicación escrita por una persona usuaria."""

    def __init__(self, identificador, nombre_usuario, contenido, fecha=None):
        """Crea una publicación con fecha actual si no se especifica otra."""
        self.identificador = identificador
        self.nombre_usuario = nombre_usuario
        self.contenido = contenido
        self.fecha = fecha or datetime.now().isoformat(timespec="seconds")

    def a_diccionario(self):
        """Devuelve la publicación en un formato serializable a JSON."""
        return {
            "identificador": self.identificador,
            "nombre_usuario": self.nombre_usuario,
            "contenido": self.contenido,
            "fecha": self.fecha,
        }

    @classmethod
    def desde_diccionario(cls, datos):
        """Construye una publicación desde un diccionario previamente validado."""
        return cls(
            datos["identificador"],
            datos["nombre_usuario"],
            datos["contenido"],
            datos.get("fecha"),
        )
