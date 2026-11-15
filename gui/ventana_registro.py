"""Formulario básico de registro."""

import tkinter as tk
from gui.estilo import estructura, decorar, encabezado, crear_campo_redondeado
from tkinter import messagebox


class VentanaRegistro:
    """Muestra el formulario para crear una cuenta."""


    def __init__(self, contenedor, aplicacion):
        """Construye los campos y conecta el formulario con el gestor de usuarios."""

        lateral, contenedor = estructura(contenedor, formulario=True)
        tk.Label(contenedor, text="Crear cuenta", font=("Arial", 18, "bold")).pack(pady=16)
        tk.Label(contenedor, text="Nombre completo").pack(anchor="w")
        self.marco_nombre, self.campo_nombre = crear_campo_redondeado(contenedor, tk.Entry)
        self.marco_nombre.pack(fill="x", pady=(4, 10))
        tk.Label(contenedor, text="Nombre de usuario").pack(anchor="w")
        self.marco_usuario, self.campo_usuario = crear_campo_redondeado(contenedor, tk.Entry)
        self.marco_usuario.pack(fill="x", pady=(4, 10))
        tk.Label(contenedor, text="Contraseña").pack(anchor="w")
        self.marco_contrasena, self.campo_contrasena = crear_campo_redondeado(
            contenedor, tk.Entry, show="*")
        self.marco_contrasena.pack(fill="x", pady=(4, 10))
        tk.Label(contenedor, text="Confirmar contraseña").pack(anchor="w")
        self.marco_confirmacion, self.campo_confirmacion = crear_campo_redondeado(
            contenedor, tk.Entry, show="*")
        self.marco_confirmacion.pack(fill="x", pady=(4, 10))
        self.visible = False
        self.boton_visibilidad = tk.Button(contenedor, text="Mostrar contraseñas", command=self._alternar_contrasena)
        self.boton_visibilidad.pack(anchor="w")
        self.campo_nombre.focus_set()
        tk.Button(
            contenedor, text="Crear cuenta",
            command=lambda: self._registrar(aplicacion),
        ).pack(fill="x", pady=(12, 6))
        tk.Button(
            contenedor, text="Volver",
            command=lambda: aplicacion.mostrar_vista("inicio"),
        ).pack(anchor="w")

        decorar(contenedor)
        encabezado(contenedor, "Crear cuenta")

    def _alternar_contrasena(self):
        self.visible = not self.visible
        for campo in (self.campo_contrasena, self.campo_confirmacion):
            campo.configure(show="" if self.visible else "*")
        self.boton_visibilidad.configure(text="Ocultar contraseñas" if self.visible else "Mostrar contraseñas")

    def _registrar(self, aplicacion):
        """Valida y registra la cuenta, informando al usuario del resultado."""
        try:
            if not self.campo_confirmacion.get().strip():
                raise ValueError("Confirma tu contraseña.")
            if self.campo_contrasena.get() != self.campo_confirmacion.get():
                raise ValueError("Las contraseñas no coinciden.")
            aplicacion.gestor_usuarios.registrar_usuario(
                self.campo_nombre.get(),
                self.campo_usuario.get(),
                self.campo_contrasena.get(),
            )
        except ValueError as error:
            messagebox.showerror("No se pudo registrar", str(error))
            return
        except OSError:
            messagebox.showerror("No se pudo registrar", "No se pudo guardar la cuenta. Inténtalo de nuevo.")
            return
        messagebox.showinfo("Registro completado", "La cuenta se creó correctamente.")
        aplicacion.mostrar_vista("login")
