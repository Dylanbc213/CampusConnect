"""Auditoría local en archivos diarios JSON Lines, sin credenciales ni mensajes."""

import inspect
import json
import os
import sys
import threading
import uuid
from datetime import datetime, timezone
from functools import wraps


class Auditoria:
    """Conserva los eventos de cada ejecución y sesión sin sobrescribirlos."""

    CAMPOS = {
        "nombre_usuario", "actor", "propietario", "emisor", "receptor",
        "destino", "destinos", "identificador", "parent_id", "reaccion",
        "tema", "marcar",
    }

    def __init__(self, carpeta_datos):
        self.carpeta = os.path.join(carpeta_datos, "logs")
        self.ejecucion = uuid.uuid4().hex
        self.sesion = None
        self.usuario = None
        self._cerrojo = threading.RLock()

    def registrar(self, accion, resultado="exito", usuario=None, **detalles):
        """Añade un evento; un fallo del log no revierte operaciones ya guardadas."""
        ahora = datetime.now(timezone.utc)
        evento = {
            "id": uuid.uuid4().hex,
            "fecha": ahora.isoformat(timespec="milliseconds"),
            "ejecucion": self.ejecucion,
            "sesion": self.sesion,
            "usuario": usuario if usuario is not None else self.usuario,
            "accion": accion,
            "resultado": resultado,
            "detalles": detalles,
        }
        try:
            with self._cerrojo:
                os.makedirs(self.carpeta, exist_ok=True)
                ruta = os.path.join(self.carpeta, "auditoria-{}.log".format(ahora.date()))
                with open(ruta, "a", encoding="utf-8") as archivo:
                    archivo.write(json.dumps(evento, ensure_ascii=False) + "\n")
        except OSError as error:
            print("Advertencia: no se pudo guardar la auditoría ({})".format(
                type(error).__name__), file=sys.stderr)

    def cerrar_sesion(self, motivo):
        if self.sesion is not None:
            self.registrar("cerrar_sesion", motivo=motivo)
        self.usuario = None
        self.sesion = None

    def conectar(self, gestor):
        """Registra operaciones públicas, consultas y errores de un gestor."""
        for nombre, metodo in inspect.getmembers(gestor, inspect.ismethod):
            if not nombre.startswith("_"):
                setattr(gestor, nombre, self._envolver(metodo))

    @staticmethod
    def _dato(valor):
        if hasattr(valor, "nombre_usuario"):
            return valor.nombre_usuario
        if isinstance(valor, (str, int, float, bool)) or valor is None:
            return valor
        if isinstance(valor, (list, tuple)):
            return [Auditoria._dato(elemento) for elemento in valor]
        return type(valor).__name__

    def _envolver(self, metodo):
        firma = inspect.signature(metodo)
        accion = "{}.{}".format(type(metodo.__self__).__name__, metodo.__name__)

        @wraps(metodo)
        def ejecutar(*args, **kwargs):
            parametros = firma.bind_partial(*args, **kwargs).arguments
            detalles = {clave: self._dato(valor) for clave, valor in parametros.items()
                        if clave in self.CAMPOS}
            autenticacion = metodo.__name__ == "iniciar_sesion"
            usuario = detalles.get("nombre_usuario") if autenticacion else self.usuario
            try:
                resultado = metodo(*args, **kwargs)
            except Exception as error:
                self.registrar(accion, "error", usuario=usuario,
                               tipo_error=type(error).__name__, **detalles)
                raise
            estado = "exito"
            if autenticacion:
                if resultado is None:
                    estado = "denegado"
                else:
                    self.cerrar_sesion("nuevo_inicio")
                    self.usuario = resultado.nombre_usuario
                    self.sesion = uuid.uuid4().hex
                    usuario = self.usuario
            if hasattr(resultado, "identificador"):
                detalles["id_resultado"] = resultado.identificador
            elif isinstance(resultado, dict) and "id" in resultado:
                detalles["id_resultado"] = resultado["id"]
            elif isinstance(resultado, (list, tuple)):
                detalles["cantidad_resultados"] = len(resultado)
            self.registrar(accion, estado, usuario=usuario, **detalles)
            return resultado

        return ejecutar
