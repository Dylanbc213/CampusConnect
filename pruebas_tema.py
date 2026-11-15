"""Pruebas de cambio de apariencia, borradores y persistencia."""

import os
import tempfile
import tkinter as tk
import unittest

from gestores.gestor_usuarios import GestorUsuarios
from gui.estilo import preparar
from gui.estilo import aplicar_tema, _hover, _salir_hover, TEMAS
from gui.avatar import foto_circular, dibujar_avatar
from types import SimpleNamespace
from PIL import Image, ImageTk
from main import CampusConnectApp


class PruebasTema(unittest.TestCase):
    def test_avatares_transparentes_y_controles_en_ambos_temas(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        contenedor = tk.Frame(raiz, background="#F3F4F6")
        avatar = tk.Canvas(contenedor, width=48, height=48)
        botones = []
        for rol in ("actualizar", "icono", "reaccion"):
            boton = tk.Button(contenedor, background="#FFFFFF", foreground="#1F2937")
            boton._campus_rol = rol
            if rol == "icono":
                boton._campus_icono = "imagen"
            botones.append(boton)
        lateral = tk.Frame(raiz, background="#E4002B")
        navegacion = tk.Button(lateral)
        navegacion._campus_rol = "navegacion"
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "avatar.png")
            imagen = Image.new("RGBA", (80, 80), (40, 90, 120, 255))
            imagen.putpixel((40, 40), (40, 90, 120, 0))
            imagen.save(ruta)
            foto = foto_circular(ruta, 80)
            resultado = ImageTk.getimage(foto)
            self.assertEqual(resultado.getpixel((0, 0))[3], 0)
            self.assertLess(resultado.getpixel((40, 40))[3], 255)
            self.assertTrue(any(0 < a < 255 for a in resultado.getchannel("A").tobytes()))
            usuario = SimpleNamespace(foto_perfil=ruta, nombre_visible="Ana")
            dibujar_avatar(avatar, usuario, carpeta, 48)
            self.assertEqual(avatar._foto_perfil.width(), 48)
            self.assertEqual([avatar.type(i) for i in avatar.find_all()], ["image"])
            for modo in ("claro", "oscuro", "claro"):
                aplicar_tema(raiz, modo)
                self.assertEqual(avatar.cget("background"), contenedor.cget("background"))
                self.assertEqual(int(avatar.cget("highlightthickness")), 0)
                for boton in botones:
                    self.assertEqual(boton.cget("background"), contenedor.cget("background"))
                    _hover(boton)
                    self.assertEqual(boton.cget("background"), TEMAS[modo]["NEUTRO_HOVER"])
                    _salir_hover(boton)
                    self.assertEqual(boton.cget("background"), contenedor.cget("background"))
                icono = ImageTk.getimage(botones[1]._campus_imagen)
                self.assertEqual(icono.getpixel((0, 0))[3], 0)
                for boton in (navegacion, botones[2]):
                    boton._campus_seleccionado = True
                    aplicar_tema(boton, modo)
                    fondo = boton.cget("background")
                    _hover(boton)
                    _salir_hover(boton)
                    self.assertEqual(boton.cget("background"), fondo)
                    self.assertEqual(boton.cget("activebackground"), fondo)
                    boton._campus_seleccionado = False

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
