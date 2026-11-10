import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gestores.gestor_usuarios import GestorUsuarios
from gui.ventana_login import VentanaLogin
from gui.ventana_registro import VentanaRegistro
from pruebas_fase1 import WidgetSimulado, MarcoSimulado


class PruebasAutenticacion(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.ruta = os.path.join(temporal.name, "usuarios.json")
        self.gestor = GestorUsuarios(self.ruta)

    def test_registro_hash_validaciones_y_persistencia(self):
        ana = self.gestor.registrar_usuario("Ana", "Ana", "contraseña")
        otra = self.gestor.registrar_usuario("Otra", "Otra", "contraseña")
        self.assertTrue(ana.contrasena.startswith("pbkdf2_sha256$600000$"))
        self.assertNotEqual(ana.contrasena, otra.contrasena)
        for nombre in ("ana", "ANA", "con espacio", "tab\tusuario", " Ana"):
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                self.gestor.registrar_usuario("Nombre", nombre, "clave")
        recargado = GestorUsuarios(self.ruta)
        self.assertIsNotNone(recargado.iniciar_sesion("aNA", "contraseña"))
        self.assertIsNone(recargado.iniciar_sesion("Ana", "incorrecta"))
        with open(self.ruta, encoding="utf-8") as archivo:
            self.assertNotIn("contraseña", archivo.read())

    def test_migracion_solo_tras_acceso_correcto(self):
        datos = [{"nombre": "Ana", "nombre_usuario": "Ana", "contrasena": "clave antigua", "fecha_registro": "2020-01-01"}]
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo)
        gestor = GestorUsuarios(self.ruta)
        self.assertIsNone(gestor.iniciar_sesion("ana", "incorrecta"))
        with open(self.ruta, encoding="utf-8") as archivo:
            self.assertEqual(json.load(archivo), datos)
        with patch("gestores.gestor_usuarios.os.replace", side_effect=OSError):
            with self.assertRaises(OSError):
                gestor.iniciar_sesion("ana", "clave antigua")
        self.assertEqual(gestor.usuarios[0].contrasena, "clave antigua")
        with open(self.ruta, encoding="utf-8") as archivo:
            self.assertEqual(json.load(archivo), datos)
        usuario = gestor.iniciar_sesion("ANA", "clave antigua")
        self.assertTrue(usuario.contrasena.startswith("pbkdf2_sha256$"))
        recargado = GestorUsuarios(self.ruta)
        self.assertEqual(recargado.iniciar_sesion("ana", "clave antigua").fecha_registro, "2020-01-01")
        self.assertIsNone(recargado.iniciar_sesion("ana", usuario.contrasena))

    def test_formularios_confirmacion_visibilidad_y_enter(self):
        app = SimpleNamespace(raiz=Mock(), gestor_usuarios=self.gestor, mostrar_vista=Mock())
        with patch("tkinter.Label", WidgetSimulado), patch("tkinter.Entry", WidgetSimulado), \
             patch("tkinter.Button", WidgetSimulado), patch("tkinter.messagebox.showerror") as error, \
             patch("tkinter.messagebox.showinfo"):
            registro = VentanaRegistro(MarcoSimulado(), app)
            registro.campo_nombre.valor = "Ana"
            registro.campo_usuario.valor = "Ana"
            registro.campo_contrasena.valor = "clave"
            registro.campo_confirmacion.valor = "distinta"
            registro._registrar(app)
            error.assert_called_once()
            self.assertEqual(self.gestor.usuarios, [])
            registro._alternar_contrasena()
            self.assertEqual(registro.campo_confirmacion.opciones["show"], "")
            registro._alternar_contrasena()
            self.assertEqual(registro.campo_contrasena.opciones["show"], "*")
            registro.campo_confirmacion.valor = "clave"
            registro._registrar(app)
            app.mostrar_vista.assert_called_with("login")
            login = VentanaLogin(MarcoSimulado(), app)
            login.campo_usuario.valor = "ANA"
            login.campo_contrasena.valor = "clave"
            login._alternar_contrasena()
            self.assertEqual(login.campo_contrasena.opciones["show"], "")
            login._alternar_contrasena()
            self.assertEqual(login.campo_contrasena.opciones["show"], "*")
            for campo in (login.campo_usuario, login.campo_contrasena):
                campo.opciones["<Return>"](None)
                app.mostrar_vista.assert_called_with("panel", self.gestor.usuarios[0])


if __name__ == "__main__":
    unittest.main()
