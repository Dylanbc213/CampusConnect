"""Gestión de cuentas y autenticación básica."""

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
        nombre_usuario = nombre_usuario.strip()
        if not nombre or not nombre_usuario or not contrasena:
            raise ValueError("Todos los campos son obligatorios.")
        if nombre_usuario in self.usuarios_por_nombre:
            raise ValueError("Ese nombre de usuario ya está registrado.")

        usuario = Usuario(nombre, nombre_usuario, contrasena)
        self.usuarios.append(usuario)
        self.usuarios_por_nombre[nombre_usuario] = usuario
        self._guardar()
        return usuario

    def iniciar_sesion(self, nombre_usuario, contrasena):
        """Devuelve la cuenta si las credenciales coinciden; de lo contrario, None."""
        usuario = self.usuarios_por_nombre.get(nombre_usuario.strip())
        if usuario is not None and usuario.contrasena == contrasena:
            return usuario
        return None

    def _guardar(self):
        """Persiste la lista de usuarios."""
        guardar_json(
            self.ruta_archivo,
            [usuario.a_diccionario() for usuario in self.usuarios],
        )
