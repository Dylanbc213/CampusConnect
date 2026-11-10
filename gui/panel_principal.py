"""Panel principal de la cuenta autenticada."""

import tkinter as tk


class PanelPrincipal:
    """Presenta un saludo y permite cerrar la sesión."""

    def __init__(self, contenedor, aplicacion, usuario):
        """Construye una vista inicial sencilla para una cuenta autenticada."""
        tk.Label(contenedor, text="Panel principal", font=("Arial", 18, "bold")).pack(pady=16)
        tk.Label(contenedor, text="Bienvenido/a, {}".format(usuario.nombre)).pack(pady=8)
        tk.Label(
            contenedor,
            text="Las funciones sociales se incorporarán en las siguientes fases.",
        ).pack(pady=8)
        tk.Button(
            contenedor, text="Cerrar sesión",
            command=lambda: aplicacion.mostrar_vista("inicio"),
        ).pack(pady=10)
