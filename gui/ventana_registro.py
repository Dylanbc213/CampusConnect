"""Formulario básico de registro."""

import tkinter as tk
from tkinter import messagebox


class VentanaRegistro:
    """Muestra el formulario para crear una cuenta."""

    def __init__(self, contenedor, aplicacion):
        """Construye los campos y conecta el formulario con el gestor de usuarios."""
        tk.Label(contenedor, text="Crear cuenta", font=("Arial", 18, "bold")).pack(pady=16)
        tk.Label(contenedor, text="Nombre completo").pack()
        self.campo_nombre = tk.Entry(contenedor)
        self.campo_nombre.pack(pady=4)
        tk.Label(contenedor, text="Nombre de usuario").pack()
        self.campo_usuario = tk.Entry(contenedor)
        self.campo_usuario.pack(pady=4)
        tk.Label(contenedor, text="Contraseña").pack()
        self.campo_contrasena = tk.Entry(contenedor, show="*")
        self.campo_contrasena.pack(pady=4)
        tk.Button(
            contenedor, text="Crear cuenta",
            command=lambda: self._registrar(aplicacion),
        ).pack(pady=10)
        tk.Button(
            contenedor, text="Volver",
            command=lambda: aplicacion.mostrar_vista("inicio"),
        ).pack()

    def _registrar(self, aplicacion):
        """Valida y registra la cuenta, informando al usuario del resultado."""
        try:
            aplicacion.gestor_usuarios.registrar_usuario(
                self.campo_nombre.get(),
                self.campo_usuario.get(),
                self.campo_contrasena.get(),
            )
        except ValueError as error:
            messagebox.showerror("No se pudo registrar", str(error))
            return
        messagebox.showinfo("Registro completado", "La cuenta se creó correctamente.")
        aplicacion.mostrar_vista("login")
