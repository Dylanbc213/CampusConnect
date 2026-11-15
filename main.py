"""Punto de entrada de la aplicación CampusConnect."""

import os
import tkinter as tk

from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_publicaciones import GestorPublicaciones
from gestores.gestor_configuracion import GestorConfiguracion
from gestores.gestor_usuarios import GestorUsuarios
from gui.panel_principal import PanelPrincipal
from gui.ventana_inicio import VentanaInicio
from gui.ventana_login import VentanaLogin
from gui.ventana_registro import VentanaRegistro
from gui.estilo import aplicar_tema, preparar


class CampusConnectApp:
    """Coordina los gestores, las vistas y la navegación de la aplicación."""

    def __init__(self, raiz, carpeta_datos):
        """Inicializa la persistencia, carga los datos y presenta la pantalla inicial."""
        self.raiz = raiz
        self.raiz.title("CampusConnect")
        preparar(self.raiz)
        self.gestor_configuracion = GestorConfiguracion(
            os.path.join(carpeta_datos, "configuracion.json")
        )
        self.modo_tema = self.gestor_configuracion.tema
        self.boton_tema = tk.Button(
            self.raiz, text="", command=self.alternar_tema,
            background="#F3F4F6", foreground="#1F2937", activebackground="#E5E7EB",
            relief="flat", borderwidth=0, highlightthickness=1,
            highlightbackground="#E5E7EB", highlightcolor="#E4002B",
            padx=5, pady=0, width=2, height=1,
            cursor="hand2", font=("Segoe UI Symbol", 12),
        )
        self.boton_tema._campus_rol = "tema"
        self.boton_tema.place(relx=1.0, x=-8, y=4, anchor="ne")
        self.gestor_usuarios = GestorUsuarios(os.path.join(carpeta_datos, "usuarios.json"))
        self.gestor_amistades = GestorAmistades(
            os.path.join(carpeta_datos, "amistades.json"),
            self.gestor_usuarios,
        )
        self.gestor_publicaciones = GestorPublicaciones(
            os.path.join(carpeta_datos, "publicaciones.json")
        )
        self.contenedor = tk.Frame(raiz, padx=20, pady=0)
        self.contenedor.pack(fill="both", expand=True)
        self._actualizar_boton_tema()
        aplicar_tema(self.raiz, self.modo_tema)
        self.vista_actual = None
        self.vista_instancia = None
        self.usuario_actual = None
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
        self.usuario_actual = usuario if nombre_vista == "panel" else None
        if nombre_vista == "panel":
            self.vista_instancia = clase_vista(self.contenedor, self, usuario)
        else:
            self.vista_instancia = clase_vista(self.contenedor, self)
        aplicar_tema(self.raiz, self.modo_tema)
        self.boton_tema.lift()

    def _actualizar_boton_tema(self):
        if hasattr(self, "boton_tema"):
            if self.modo_tema == "oscuro":
                self.boton_tema.configure(text="\u2600")
            else:
                self.boton_tema.configure(text="\u263e")

    def alternar_tema(self):
        nuevo = "oscuro" if self.modo_tema == "claro" else "claro"
        try:
            self.gestor_configuracion.establecer_tema(nuevo)
        except OSError:
            from tkinter import messagebox
            messagebox.showerror("Tema", "No se pudo guardar la preferencia de tema.", parent=self.raiz)
            return
        self.modo_tema = nuevo
        self._actualizar_boton_tema()
        aplicar_tema(self.raiz, self.modo_tema)
        self.boton_tema.lift()


def main():
    """Crea los archivos de datos que falten y ejecuta el ciclo de Tkinter."""
    carpeta_proyecto = os.path.dirname(os.path.abspath(__file__))
    carpeta_datos = os.path.join(carpeta_proyecto, "datos")
    raiz = tk.Tk()
    CampusConnectApp(raiz, carpeta_datos)
    raiz.mainloop()


if __name__ == "__main__":
    main()
