import os
import tempfile
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gestores.gestor_usuarios import GestorUsuarios
from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_publicaciones import GestorPublicaciones
from gui.ventana_muro import VentanaMuro
from pruebas_fase1 import WidgetSimulado


class TextoSimulado(WidgetSimulado):
    def get(self, *indices):
        return self.valor

    def delete(self, *indices):
        self.valor = ""

    def configure(self, **opciones):
        self.opciones.update(opciones)


class PruebasPublicaciones(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.ruta = os.path.join(temporal.name, "publicaciones.json")
        self.usuarios = GestorUsuarios(os.path.join(temporal.name, "usuarios.json"))
        for nombre in ("ana", "luis", "maria"):
            self.usuarios.registrar_usuario(nombre.title(), nombre, "clave")
        self.amistades = GestorAmistades(os.path.join(temporal.name, "amistades.json"), self.usuarios)
        self.gestor = GestorPublicaciones(self.ruta)

    def test_creacion_validacion_y_recarga(self):
        antes = datetime.now().replace(microsecond=0)
        primera = self.gestor.crear_publicacion("ana", "  Hola\n¡Campus!  ")
        self.assertEqual(primera.nombre_usuario, "ana")
        self.assertEqual(primera.contenido, "Hola\n¡Campus!")
        self.assertLessEqual(antes, datetime.fromisoformat(primera.fecha))
        self.assertLessEqual(datetime.fromisoformat(primera.fecha), datetime.now())
        for contenido in ("", " \n\t "):
            with self.assertRaises(ValueError):
                self.gestor.crear_publicacion("ana", contenido)
        recargado = GestorPublicaciones(self.ruta)
        self.assertEqual([p.a_diccionario() for p in recargado.publicaciones], [primera.a_diccionario()])
        segunda = recargado.crear_publicacion("luis", "Otra publicación")
        self.assertGreater(segunda.identificador, primera.identificador)
        self.assertEqual(len(GestorPublicaciones(self.ruta).publicaciones), 2)

    def test_consultas_propias_y_amigos(self):
        propia = self.gestor.crear_publicacion("ana", "Propia")
        amigo = self.gestor.crear_publicacion("luis", "De Luis")
        self.gestor.crear_publicacion("maria", "De María")
        self.assertEqual(self.gestor.obtener_publicaciones_usuario("ana"), [propia])
        self.assertEqual(self.gestor.obtener_publicaciones_amigos("ana", self.amistades), [])
        self.amistades.agregar_amistad("ana", "luis")
        self.assertEqual(self.gestor.obtener_publicaciones_amigos("ana", self.amistades), [amigo])
        self.assertEqual(self.gestor.obtener_publicaciones_amigos("luis", self.amistades), [propia])
        recargado = GestorPublicaciones(self.ruta)
        amistades = GestorAmistades(self.amistades.ruta_archivo, self.usuarios)
        self.assertEqual([p.contenido for p in recargado.obtener_publicaciones_amigos("ana", amistades)], ["De Luis"])

    def test_fallo_guardado_conserva_datos(self):
        original = self.gestor.crear_publicacion("ana", "Anterior")
        with open(self.ruta, "rb") as archivo:
            contenido = archivo.read()
        with patch("gestores.gestor_publicaciones.os.replace", side_effect=OSError):
            with self.assertRaises(OSError):
                self.gestor.crear_publicacion("ana", "Nueva")
        self.assertEqual(self.gestor.publicaciones, [original])
        with open(self.ruta, "rb") as archivo:
            self.assertEqual(archivo.read(), contenido)

    def test_publicacion_y_actualizacion_en_interfaz(self):
        app = SimpleNamespace(gestor_usuarios=self.usuarios, gestor_amistades=self.amistades,
                              gestor_publicaciones=self.gestor)
        with patch("gui.ventana_muro.tk.Toplevel", return_value=MagicMock()), \
             patch("gui.ventana_muro.tk.Label", WidgetSimulado), \
             patch("gui.ventana_muro.tk.Button", WidgetSimulado), \
             patch("gui.ventana_muro.ScrolledText", TextoSimulado), \
             patch("gui.ventana_muro.messagebox.showerror") as error, \
             patch("gui.ventana_muro.messagebox.showinfo") as exito:
            muro = VentanaMuro(None, app, self.usuarios.usuarios_por_nombre["ana"])
            self.assertIn("No hay publicaciones", muro.muro_personal.valor)
            muro._publicar()
            error.assert_called_once()
            exito.assert_not_called()
            muro.campo_contenido.valor = "Texto\ncon dos líneas"
            with patch.object(self.gestor, "_guardar", side_effect=OSError):
                muro._publicar()
            self.assertEqual(muro.campo_contenido.valor, "Texto\ncon dos líneas")
            self.assertEqual(self.gestor.publicaciones, [])
            muro._publicar()
            exito.assert_called_once()
            self.assertEqual(muro.campo_contenido.valor, "")
            self.assertIn("Ana (@ana)", muro.muro_personal.valor)
            self.assertIn(self.gestor.publicaciones[0].fecha, muro.muro_personal.valor)
            self.assertIn("Texto\ncon dos líneas", muro.muro_personal.valor)
            self.assertEqual(muro.muro_personal.opciones["state"], "disabled")
            self.gestor.crear_publicacion("luis", "Texto de amigo")
            self.gestor.crear_publicacion("maria", "Texto ajeno")
            self.amistades.agregar_amistad("ana", "luis")
            muro._actualizar()
            self.assertIn("Luis (@luis)", muro.muro_amigos.valor)
            self.assertIn("Texto de amigo", muro.muro_amigos.valor)
            self.assertNotIn("Texto ajeno", muro.muro_amigos.valor)
            app.gestor_publicaciones = GestorPublicaciones(self.ruta)
            reabierto = VentanaMuro(None, app, self.usuarios.usuarios_por_nombre["ana"])
            self.assertEqual(reabierto.muro_personal.valor, muro.muro_personal.valor)
            self.assertEqual(reabierto.muro_amigos.valor, muro.muro_amigos.valor)


if __name__ == "__main__":
    unittest.main()
