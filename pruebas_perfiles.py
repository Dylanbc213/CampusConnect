"""Pruebas de edición, compatibilidad JSON y permisos de perfil."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from gestores.gestor_usuarios import GestorUsuarios


class PruebasPerfiles(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.temporal.name, "usuarios.json")
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump([
                {"nombre": "Ana", "nombre_usuario": "ana", "contrasena": "hash"},
                {"nombre": "Luis", "nombre_usuario": "luis", "contrasena": "hash"},
            ], archivo)
        self.gestor = GestorUsuarios(self.ruta)
        self.ana = self.gestor.usuarios_por_nombre["ana"]
        self.luis = self.gestor.usuarios_por_nombre["luis"]

    def tearDown(self):
        self.temporal.cleanup()

    def test_edicion_persistencia_y_compatibilidad(self):
        self.assertEqual(self.ana.nombre_visible, "Ana")
        self.assertEqual(self.ana.biografia, "")
        self.gestor.actualizar_perfil(self.ana, self.ana, "Ana UNA", "Estudiante de la UNA", "avatares/ana.png")
        recargado = GestorUsuarios(self.ruta).usuarios_por_nombre["ana"]
        self.assertEqual(recargado.nombre_usuario, "ana")
        self.assertEqual(recargado.nombre_visible, "Ana UNA")
        self.assertEqual(recargado.biografia, "Estudiante de la UNA")
        self.assertEqual(recargado.foto_perfil, "avatares/ana.png")
        self.assertEqual(recargado.contrasena, "hash")

    def test_solo_propietario_y_limite_biografia(self):
        with self.assertRaises(PermissionError):
            self.gestor.actualizar_perfil(self.ana, self.luis, "Nombre", "Bio")
        with self.assertRaises(ValueError):
            self.gestor.actualizar_perfil(self.ana, self.ana, "Ana", "x" * 151)
        self.gestor.actualizar_perfil(self.ana, self.ana, "Ana", "x" * 150)
        self.assertEqual(len(self.ana.biografia), 150)

    def test_fallo_de_guardado_conserva_perfil(self):
        antes = self.ana.a_diccionario().copy()
        with patch.object(self.gestor, "_guardar", side_effect=OSError("sin acceso")):
            with self.assertRaises(OSError):
                self.gestor.actualizar_perfil(self.ana, self.ana, "Cambio", "Nueva bio")
        self.assertEqual(self.ana.a_diccionario(), antes)


if __name__ == "__main__":
    unittest.main()
