"""Pruebas de cambio de apariencia, borradores y persistencia."""

import os
import tempfile
import tkinter as tk
import unittest

from gestores.gestor_usuarios import GestorUsuarios
from gui.estilo import preparar
from main import CampusConnectApp


class PruebasTema(unittest.TestCase):
    def test_cambio_en_sitio_navegacion_y_preferencia_persistida(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            app = CampusConnectApp(raiz, carpeta)
            self.assertEqual(app.modo_tema, "claro")
            self.assertEqual(app.boton_tema.cget("text"), "☾")
            self.assertEqual(app.contenedor.cget("pady"), 0)
            self.assertEqual(app.boton_tema.winfo_manager(), "place")
            app.mostrar_vista("panel", ana)
            panel = app.vista_instancia
            panel._mostrar_seccion("Buscar usuarios")
            panel.campo_busqueda.insert(0, "borrador de búsqueda")
            panel._mostrar_seccion("Inicio")
            panel.muro.boton_agregar.invoke()
            panel.muro.campo_contenido.insert("1.0", "borrador de publicación")

            app.alternar_tema()
            self.assertEqual(app.modo_tema, "oscuro")
            self.assertEqual(app.boton_tema.cget("text"), "☀")
            self.assertEqual(raiz.cget("background"), "#111318")
            self.assertEqual(app.boton_tema.cget("background"), "#1E2128")
            self.assertEqual(app.boton_tema.cget("foreground"), "#FFFFFF")
            self.assertIs(app.vista_instancia, panel)
            self.assertEqual(panel.seccion_activa, "Inicio")
            self.assertEqual(panel.campo_busqueda.get(), "borrador de búsqueda")
            self.assertEqual(panel.muro.campo_contenido.get("1.0", "end-1c"),
                             "borrador de publicación")
            self.assertEqual(panel.muro.compositor.winfo_manager(), "pack")

            app.mostrar_vista("login")
            self.assertEqual(app.vista_instancia.campo_usuario.cget("background"), "#171A20")
            self.assertEqual(app.vista_instancia.tarjeta.cget("background"), "#1E2128")
            app.mostrar_vista("registro")
            self.assertEqual(app.vista_instancia.campo_usuario.cget("background"), "#171A20")

            app.alternar_tema()
            self.assertEqual(app.modo_tema, "claro")
            self.assertEqual(raiz.cget("background"), "#FFFFFF")
            self.assertEqual(app.gestor_configuracion.tema, "claro")

            app.alternar_tema()
            self.assertEqual(app.gestor_configuracion.tema, "oscuro")
            self.assertEqual(
                app.gestor_configuracion.__class__(os.path.join(carpeta, "configuracion.json")).tema,
                "oscuro",
            )


if __name__ == "__main__":
    unittest.main()
