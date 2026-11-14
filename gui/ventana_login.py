"""Formulario básico de inicio de sesión."""

import tkinter as tk
from gui.estilo import estructura, decorar, encabezado
from tkinter import messagebox


class VentanaLogin:
    """Muestra el formulario para acceder a una cuenta existente."""


    def __init__(self, contenedor, aplicacion):
        """Construye los campos y conecta la validación con el gestor de usuarios."""
        lateral, contenedor = estructura(contenedor, formulario=True)
        tk.Label(contenedor, text="Iniciar sesión", font=("Arial", 18, "bold")).pack(pady=16)
        tk.Label(contenedor, text="Nombre de usuario").pack(anchor="w")
        self.campo_usuario = tk.Entry(contenedor)
        self.campo_usuario.pack(fill="x", pady=(4, 10))
        tk.Label(contenedor, text="Contraseña").pack(anchor="w")
        self.campo_contrasena = tk.Entry(contenedor, show="*")
        self.campo_contrasena.pack(fill="x", pady=(4, 10))
        self.visible = False
        self.boton_visibilidad = tk.Button(contenedor, text="Mostrar contraseña", command=self._alternar_contrasena)
        self.boton_visibilidad.pack(anchor="w")
        for campo in (self.campo_usuario, self.campo_contrasena):
            campo.bind("<Return>", lambda evento: self._iniciar_sesion(aplicacion))
        self.campo_usuario.focus_set()
        tk.Button(
            contenedor, text="Entrar",
            command=lambda: self._iniciar_sesion(aplicacion),
        ).pack(fill="x", pady=(12, 6))
        tk.Button(
            contenedor, text="Volver",
            command=lambda: aplicacion.mostrar_vista("inicio"),
        ).pack(anchor="w")

        decorar(contenedor)
        encabezado(contenedor, "Iniciar sesión")

    def _alternar_contrasena(self):
        self.visible = not self.visible
        self.campo_contrasena.configure(show="" if self.visible else "*")
        self.boton_visibilidad.configure(text="Ocultar contraseña" if self.visible else "Mostrar contraseña")

    def _iniciar_sesion(self, aplicacion):
        """Autentica al usuario y abre el panel si las credenciales son correctas."""
        try:
            usuario = aplicacion.gestor_usuarios.iniciar_sesion(
                self.campo_usuario.get(),
                self.campo_contrasena.get(),
            )
        except ValueError as error:
            messagebox.showerror("Acceso denegado", str(error))
            return
        except OSError:
            messagebox.showerror("No se pudo iniciar sesión", "No se pudo guardar la contraseña protegida. Inténtalo de nuevo.")
            return
        if usuario is None:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            return
        messagebox.showinfo("Acceso correcto", "Inicio de sesión exitoso.")
        aplicacion.mostrar_vista("panel", usuario)
