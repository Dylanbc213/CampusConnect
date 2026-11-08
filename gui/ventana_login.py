"""Formulario básico de inicio de sesión."""

import tkinter as tk
from tkinter import messagebox


class VentanaLogin:
    """Muestra el formulario para acceder a una cuenta existente."""

    def __init__(self, contenedor, aplicacion):
        """Construye los campos y conecta la validación con el gestor de usuarios."""
        tk.Label(contenedor, text="Iniciar sesión", font=("Arial", 18, "bold")).pack(pady=16)
        tk.Label(contenedor, text="Nombre de usuario").pack()
        self.campo_usuario = tk.Entry(contenedor)
        self.campo_usuario.pack(pady=4)
        tk.Label(contenedor, text="Contraseña").pack()
        self.campo_contrasena = tk.Entry(contenedor, show="*")
        self.campo_contrasena.pack(pady=4)
        tk.Button(
            contenedor, text="Entrar",
            command=lambda: self._iniciar_sesion(aplicacion),
        ).pack(pady=10)
        tk.Button(
            contenedor, text="Volver",
            command=lambda: aplicacion.mostrar_vista("inicio"),
        ).pack()

    def _iniciar_sesion(self, aplicacion):
        """Autentica al usuario y abre el panel si las credenciales son correctas."""
        usuario = aplicacion.gestor_usuarios.iniciar_sesion(
            self.campo_usuario.get(),
            self.campo_contrasena.get(),
        )
        if usuario is None:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            return
        aplicacion.mostrar_vista("panel", usuario)
