"""Gestión de cuentas y autenticación básica."""

import hashlib
import hmac
import os
import tempfile

from modelos.usuario import Usuario
from persistencia.almacenamiento import cargar_json, guardar_json


class GestorUsuarios:
    """Administra usuarios en memoria y mantiene su archivo JSON actualizado."""

    def __init__(self, ruta_archivo):
        """Carga los usuarios y crea una búsqueda directa por nombre de usuario."""
        self.ruta_archivo = ruta_archivo
        self.usuarios = []
        self.usuarios_por_nombre = {}
        self._cargar()

    def _cargar(self):
        """Carga registros válidos y reconstruye las estructuras en memoria."""
        registros = cargar_json(self.ruta_archivo, [])
        if not isinstance(registros, list):
            print("Advertencia: usuarios.json debe contener una lista; se usará una lista vacía.")
            return

        for registro in registros:
            if not isinstance(registro, dict):
                continue
            try:
                usuario = Usuario.desde_diccionario(registro)
            except (KeyError, TypeError):
                continue
            if not all(
                isinstance(valor, str) and valor.strip()
                for valor in (usuario.nombre, usuario.nombre_usuario, usuario.contrasena)
            ):
                continue
            if usuario.nombre_usuario in self.usuarios_por_nombre:
                continue
            self.usuarios.append(usuario)
            self.usuarios_por_nombre[usuario.nombre_usuario] = usuario

    def registrar_usuario(self, nombre, nombre_usuario, contrasena):
        """Registra y persiste una cuenta; genera ValueError si faltan datos o se repite."""
        nombre = nombre.strip()
        if not nombre or not nombre_usuario or not contrasena.strip():
            raise ValueError("Todos los campos son obligatorios.")
        if any(caracter.isspace() for caracter in nombre_usuario):
            raise ValueError("El nombre de usuario no puede contener espacios.")
        if any(u.nombre_usuario.casefold() == nombre_usuario.casefold() for u in self.usuarios):
            raise ValueError("Ese nombre de usuario ya está registrado.")

        usuario = Usuario(nombre, nombre_usuario, self._proteger(contrasena))
        self.usuarios.append(usuario)
        self.usuarios_por_nombre[nombre_usuario] = usuario
        try:
            self._guardar()
        except OSError:
            self.usuarios.remove(usuario)
            del self.usuarios_por_nombre[nombre_usuario]
            raise
        return usuario

    def iniciar_sesion(self, nombre_usuario, contrasena):
        """Devuelve la cuenta si las credenciales coinciden; de lo contrario, None."""
        if not nombre_usuario.strip() or not contrasena.strip():
            raise ValueError("Todos los campos son obligatorios.")
        nombre_usuario = nombre_usuario.strip()
        candidatos = [u for u in self.usuarios if u.nombre_usuario.casefold() == nombre_usuario.casefold()]
        # Conserva el acceso exacto a cuentas antiguas que solo difieren en mayúsculas.
        usuario = self.usuarios_por_nombre.get(nombre_usuario)
        if usuario is None and len(candidatos) == 1:
            usuario = candidatos[0]
        if usuario is None:
            return None
        almacenada = usuario.contrasena
        if almacenada.startswith("pbkdf2_sha256$"):
            try:
                _, iteraciones, sal, resumen = almacenada.split("$")
                if int(iteraciones) != 600000:
                    return None
                esperado = bytes.fromhex(resumen)
                calculado = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), bytes.fromhex(sal), int(iteraciones))
                return usuario if hmac.compare_digest(calculado, esperado) else None
            except (ValueError, OverflowError):
                return None
        if not hmac.compare_digest(almacenada.encode("utf-8"), contrasena.encode("utf-8")):
            return None
        usuario.contrasena = self._proteger(contrasena)
        try:
            self._guardar()
        except OSError:
            usuario.contrasena = almacenada
            raise
        return usuario

    @staticmethod
    def _proteger(contrasena):
        sal = os.urandom(16)
        resumen = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, 600000)
        return "pbkdf2_sha256$600000${}${}".format(sal.hex(), resumen.hex())

    def buscar_usuarios(self, consulta):
        consulta = consulta.strip().casefold()
        if not consulta:
            return []
        return [usuario for usuario in self.usuarios
                if consulta in usuario.nombre.casefold()
                or consulta in usuario.nombre_visible.casefold()
                or consulta in usuario.nombre_usuario.casefold()]

    def actualizar_perfil(self, actor, propietario, nombre_visible, biografia, foto_perfil=None):
        """Actualiza datos públicos solo cuando el propietario coincide con la cuenta."""
        if actor is not propietario:
            raise PermissionError("Solo puedes editar tu propio perfil.")
        if self.usuarios_por_nombre.get(propietario.nombre_usuario) is not propietario:
            raise PermissionError("Solo puedes editar tu propio perfil.")
        nombre_visible = nombre_visible.strip()
        if not nombre_visible:
            raise ValueError("El nombre visible es obligatorio.")
        if len(biografia) > 150:
            raise ValueError("La biografía no puede superar los 150 caracteres.")
        anteriores = (propietario.nombre_visible, propietario.biografia, propietario.foto_perfil)
        propietario.nombre_visible = nombre_visible
        propietario.biografia = biografia
        if foto_perfil is not None:
            propietario.foto_perfil = foto_perfil
        try:
            self._guardar()
        except OSError:
            propietario.nombre_visible, propietario.biografia, propietario.foto_perfil = anteriores
            raise

    def _guardar(self):
        """Persiste la lista de usuarios."""
        carpeta = os.path.dirname(os.path.abspath(self.ruta_archivo))
        descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".json")
        os.close(descriptor)
        try:
            guardar_json(temporal, [usuario.a_diccionario() for usuario in self.usuarios])
            os.replace(temporal, self.ruta_archivo)
        finally:
            if os.path.exists(temporal):
                os.remove(temporal)
