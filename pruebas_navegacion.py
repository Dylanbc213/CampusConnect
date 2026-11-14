import os
import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gestores.gestor_usuarios import GestorUsuarios
from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_publicaciones import GestorPublicaciones
from gui.estilo import preparar
from gui.panel_principal import PanelPrincipal


class PruebasNavegacion(unittest.TestCase):
    def test_panel_unico_publicacion_y_persistencia(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            usuarios.registrar_usuario("Luis", "luis", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            amistades.agregar_amistad("ana", "luis")
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            publicaciones.crear_publicacion("luis", "Publicación de amigo")
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            with patch("tkinter.Toplevel", side_effect=AssertionError("Ventana adicional")):
                panel = PanelPrincipal(contenedor, app, ana)
                self.assertEqual(panel.lista_amigos.contador.cget("text"), "1")
                tarjetas = panel.lista_amigos.tarjetas.winfo_children()
                self.assertEqual(len(tarjetas), 1)
                textos = [w.cget("text") for w in tarjetas[0].winfo_children() if isinstance(w, tk.Label)]
                self.assertEqual(textos, ["Luis", "@luis"])
                muro = panel.muro
                self.assertIn("Publicación de amigo", muro.muro_amigos.get("1.0", "end"))
                muro.campo_contenido.insert("1.0", "Mi publicación")
                for seccion in ("Amigos", "Buscar usuarios", "Mi muro", "Inicio", "Mi muro"):
                    panel.botones_navegacion[seccion].invoke()
                    raiz.update_idletasks()
                    self.assertIs(panel.muro, muro)
                    self.assertEqual(panel.seccion_activa, seccion)
                    self.assertEqual(panel.botones_navegacion[seccion].cget("background"), "#FFFFFF")
                    visibles = [frame for frame in panel.secciones.values() if frame.winfo_manager()]
                    self.assertEqual(len(visibles), 1)
                    self.assertEqual(muro.campo_contenido.get("1.0", "end-1c"), "Mi publicación")
                muro._actualizar_formulario()
                muro.boton_publicar.invoke()
                self.assertEqual(muro.campo_contenido.get("1.0", "end-1c"), "")
                self.assertIn("Mi publicación", muro.muro_personal.get("1.0", "end"))
                recargado = GestorPublicaciones(publicaciones.ruta_archivo)
                self.assertEqual(recargado.obtener_publicaciones_usuario("ana")[0].contenido, "Mi publicación")

    def test_amigos_vacios_y_scroll(self):
        from gui.lista_amigos import ListaAmigos

        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        lista = ListaAmigos(raiz)
        lista.pack(fill="both", expand=True)
        lista.mostrar([])
        self.assertEqual(lista.contador.cget("text"), "0")
        self.assertEqual(lista.vacio.winfo_manager(), "place")
        lista.mostrar([("Amigo {}".format(i), "usuario{}".format(i)) for i in range(30)])
        raiz.update_idletasks()
        self.assertEqual(lista.contador.cget("text"), "30")
        self.assertEqual(len(lista.tarjetas.winfo_children()), 30)
        self.assertEqual(lista.vacio.winfo_manager(), "")
        self.assertTrue(lista.canvas.cget("scrollregion"))
        lista.mostrar([])
        self.assertEqual(len(lista.tarjetas.winfo_children()), 0)


if __name__ == "__main__":
    unittest.main()
