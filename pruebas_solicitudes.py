import json
import os
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_usuarios import GestorUsuarios
from main import CampusConnectApp


class PruebasSolicitudes(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.carpeta = temporal.name
        self.usuarios = GestorUsuarios(os.path.join(self.carpeta, "usuarios.json"))
        for nombre in ("ana", "luis"):
            self.usuarios.registrar_usuario(nombre, nombre, "clave")
        self.ruta = os.path.join(self.carpeta, "amistades.json")
        self.gestor = GestorAmistades(self.ruta, self.usuarios)

    def test_solicitud_aceptacion_permisos_y_persistencia(self):
        self.gestor.agregar_amistad("ana", "luis")
        self.assertEqual(self.gestor.obtener_amistades("ana"), [])
        recargado = GestorAmistades(self.ruta, self.usuarios)
        self.assertEqual(recargado.estado_solicitud("luis", "ana"), "recibida")
        for a, b in (("ana", "luis"), ("luis", "ana"), ("ana", "ana"), ("ana", "inexistente")):
            with self.assertRaises(ValueError):
                recargado.agregar_amistad(a, b)
        with self.assertRaises(ValueError):
            recargado.aceptar_solicitud("ana", "luis")
        recargado.aceptar_solicitud("luis", "ana")
        final = GestorAmistades(self.ruta, self.usuarios)
        self.assertEqual(final.obtener_amistades("ana"), ["luis"])
        self.assertEqual(final.obtener_amistades("luis"), ["ana"])
        self.assertEqual(final.solicitudes, [])

    def test_rechazo_fallos_y_compatibilidad(self):
        self.gestor.agregar_amistad("ana", "luis")
        with patch.object(self.gestor, "_guardar", side_effect=OSError("fallo")):
            with self.assertRaises(OSError):
                self.gestor.aceptar_solicitud("luis", "ana")
        self.assertEqual(self.gestor.obtener_amistades("ana"), [])
        self.assertEqual(len(self.gestor.solicitudes), 1)
        self.gestor.rechazar_solicitud("luis", "ana")
        self.assertEqual(GestorAmistades(self.ruta).solicitudes, [])
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump({"ana": ["luis"]}, archivo)
        antiguo = GestorAmistades(self.ruta)
        self.assertEqual(antiguo.obtener_amistades("luis"), ["ana"])

    def test_interfaz_enviar_y_aceptar_en_amigos(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        app = CampusConnectApp(raiz, self.carpeta)
        ana = app.gestor_usuarios.usuarios_por_nombre["ana"]
        luis = app.gestor_usuarios.usuarios_por_nombre["luis"]
        app.mostrar_vista("panel", ana)
        panel = app.vista_instancia
        panel._agregar_usuario(luis)
        self.assertEqual(app.gestor_amistades.obtener_amistades("ana"), [])
        panel.campo_busqueda.insert(0, "luis")
        panel._buscar()
        self.assertEqual(panel.tarjetas_resultados["luis"].cget("text"), "Solicitud enviada")
        app.mostrar_vista("panel", luis)
        panel = app.vista_instancia
        panel._mostrar_seccion("Amigos")
        botones = [b for fila in panel.lista_amigos.tarjetas.winfo_children()
                   for b in fila.winfo_children() if isinstance(b, tk.Button)]
        next(b for b in botones if b.cget("text") == "Aceptar").invoke()
        self.assertEqual(app.gestor_amistades.obtener_amistades("luis"), ["ana"])
        self.assertEqual(panel.lista_amigos.contador.cget("text"), "1")


if __name__ == "__main__":
    unittest.main()
