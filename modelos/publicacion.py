"""Modelo de una publicación estudiantil."""

from datetime import datetime

REACCIONES = ("Me gusta", "Me divierte", "No me gusta")


class Publicacion:
    """Representa una publicación escrita por una persona usuaria."""

    def __init__(self, identificador, nombre_usuario, contenido, fecha=None, comentarios=None,
                 ruta_imagen="", reacciones=None):
        """Crea una publicación con fecha actual si no se especifica otra."""
        self.identificador = identificador
        self.nombre_usuario = nombre_usuario
        self.contenido = contenido
        self.fecha = fecha or datetime.now().isoformat(timespec="seconds")
        self.comentarios = []
        if isinstance(comentarios, list):
            ids_usados = set()
            for comentario in comentarios:
                if not isinstance(comentario, dict):
                    continue
                ruta = comentario.get("ruta_imagen", "")
                if not isinstance(ruta, str):
                    ruta = ""
                if (isinstance(comentario.get("nombre_usuario"), str)
                        and comentario["nombre_usuario"].strip()
                        and isinstance(comentario.get("fecha"), str)
                        and isinstance(comentario.get("contenido"), str)
                        and (comentario["contenido"].strip() or ruta)):
                    identificador_respuesta = comentario.get("id")
                    if (type(identificador_respuesta) is not int or identificador_respuesta <= 0
                            or identificador_respuesta in ids_usados):
                        identificador_respuesta = max(ids_usados, default=0) + 1
                    padre = comentario.get("parent_id")
                    tipo_padre = comentario.get("parent_type")
                    if (tipo_padre != "respuesta" or type(padre) is not int
                            or padre not in ids_usados):
                        tipo_padre = "publicacion"
                        padre = self.identificador
                    ids_usados.add(identificador_respuesta)
                    self.comentarios.append({
                        "id": identificador_respuesta,
                        "parent_id": padre,
                        "parent_type": tipo_padre,
                        "nombre_usuario": comentario["nombre_usuario"],
                        "fecha": comentario["fecha"],
                        "contenido": comentario["contenido"],
                        "ruta_imagen": ruta,
                    })
        self.ruta_imagen = ruta_imagen if isinstance(ruta_imagen, str) else ""
        self.reacciones = {}
        if isinstance(reacciones, dict):
            self.reacciones = {
                usuario: reaccion for usuario, reaccion in reacciones.items()
                if isinstance(usuario, str) and usuario.strip() and isinstance(reaccion, str)
            }

    def a_diccionario(self):
        """Devuelve la publicación en un formato serializable a JSON."""
        return {
            "identificador": self.identificador,
            "nombre_usuario": self.nombre_usuario,
            "contenido": self.contenido,
            "fecha": self.fecha,
            "comentarios": self.comentarios,
            "ruta_imagen": self.ruta_imagen,
            "reacciones": self.reacciones,
        }

    @classmethod
    def desde_diccionario(cls, datos):
        """Construye una publicación desde un diccionario previamente validado."""
        return cls(
            datos["identificador"],
            datos["nombre_usuario"],
            datos["contenido"],
            datos.get("fecha"),
            datos.get("comentarios", []),
            datos.get("ruta_imagen", ""),
            datos.get("reacciones", {}),
        )
