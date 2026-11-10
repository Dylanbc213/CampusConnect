"""Punto de entrada de la aplicación CampusConnect."""

import os
import tkinter as tk

from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_publicaciones import GestorPublicaciones
from gestores.gestor_usuarios import GestorUsuarios
from gui.panel_principal import PanelPrincipal
from gui.ventana_inicio import VentanaInicio
from gui.ventana_login import VentanaLogin
from gui.ventana_registro import VentanaRegistro


class CampusConnectApp:
    """Coordina los gestores, las vistas y la navegación de la aplicación."""

    def __init__(self, raiz, carpeta_datos):
        """Inicializa la persistencia, carga los datos y presenta la pantalla inicial."""
        self.raiz = raiz
        self.raiz.title("CampusConnect")
        self.raiz.geometry("420x420")
        self.gestor_usuarios = GestorUsuarios(os.path.join(carpeta_datos, "usuarios.json"))
        self.gestor_amistades = GestorAmistades(
            os.path.join(carpeta_datos, "amistades.json"),
            self.gestor_usuarios,
        )
        self.gestor_publicaciones = GestorPublicaciones(
            os.path.join(carpeta_datos, "publicaciones.json")
        )
        self.contenedor = tk.Frame(raiz, padx=20, pady=20)
        self.contenedor.pack(fill="both", expand=True)
        self.vista_actual = None
        self.mostrar_vista("inicio")

    def mostrar_vista(self, nombre_vista, usuario=None):
        """Reemplaza la pantalla activa por la vista solicitada."""
        vistas = {
            "inicio": VentanaInicio,
            "registro": VentanaRegistro,
            "login": VentanaLogin,
        }
        if nombre_vista == "panel":
            if usuario is None:
                raise ValueError("El panel principal requiere un usuario autenticado.")
            clase_vista = PanelPrincipal
        else:
            clase_vista = vistas.get(nombre_vista)
        if clase_vista is None:
            raise ValueError("Vista desconocida: {}".format(nombre_vista))

        for widget in self.contenedor.winfo_children():
            widget.destroy()
        self.vista_actual = nombre_vista
        if nombre_vista == "panel":
            clase_vista(self.contenedor, self, usuario)
        else:
            clase_vista(self.contenedor, self)


def main():
    """Crea los archivos de datos que falten y ejecuta el ciclo de Tkinter."""
    carpeta_proyecto = os.path.dirname(os.path.abspath(__file__))
    carpeta_datos = os.path.join(carpeta_proyecto, "datos")
    raiz = tk.Tk()
    CampusConnectApp(raiz, carpeta_datos)
    raiz.mainloop()


if __name__ == "__main__":
    main()
