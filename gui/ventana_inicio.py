"""Pantalla inicial y opciones de navegación."""

import tkinter as tk
from gui.estilo import estructura, decorar, encabezado


class VentanaInicio:
    """Presenta las opciones de registro e inicio de sesión."""


    def __init__(self, contenedor, aplicacion):
        """Construye la pantalla inicial."""
        lateral, contenedor = estructura(contenedor, formulario=True)
        tk.Label(contenedor, text="CampusConnect", font=("Arial", 22, "bold")).pack(pady=24)
        tk.Label(contenedor, text="Conecta con tu comunidad estudiantil").pack(pady=8)
        tk.Button(
            contenedor, text="Iniciar sesión",
            command=lambda: aplicacion.mostrar_vista("login"),
        ).pack(pady=8)
        tk.Label(contenedor, text="¿No tienes cuenta?", font=("Arial", 9)).pack(pady=4)
        tk.Button(
            contenedor, text="Registrarse",
            command=lambda: aplicacion.mostrar_vista("registro"),
        ).pack(pady=8)
        decorar(contenedor)
        encabezado(contenedor, "CampusConnect")

