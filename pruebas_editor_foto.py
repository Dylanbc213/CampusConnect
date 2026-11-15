"""Pruebas del encuadre y persistencia con imágenes y JSON temporales."""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image, ImageChops
from gestores.gestor_usuarios import GestorUsuarios
from gui.editor_foto import EditorFoto
from gui.perfil import Perfil


class PruebasEditorFoto(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.editor = EditorFoto.__new__(EditorFoto)
        self.editor.zoom = Mock()
        self.valor_zoom = 1
        self.editor.zoom.get.side_effect = lambda: self.valor_zoom
        self.editor.zoom.set.side_effect = self._zoom
        self.editor._programar = Mock()
        self.editor.canvas = Mock()
        self.editor._item = 1
        self.editor._tarea = None

    def _zoom(self, valor):
        self.valor_zoom = valor

    def cargar(self, tamano=(400, 200), extension="png"):
        ruta = os.path.join(self.temporal.name, "original." + extension)
        imagen = Image.new("RGB", tamano)
        # Patrón asimétrico para detectar desplazamientos y deformaciones.
        imagen.putdata([(x % 256, y % 256, (x + y) % 256)
                        for y in range(tamano[1]) for x in range(tamano[0])])
        imagen.save(ruta)
        self.editor.cargar(ruta)
        return ruta

    def test_formatos_proporciones_y_limites(self):
        for extension in ("jpg", "jpeg", "png", "webp", "gif"):
            for tamano in ((400, 200), (200, 400), (200, 200)):
                with self.subTest(extension=extension, tamano=tamano):
                    self.cargar(tamano, extension)
                    self.assertEqual((self.editor.cx, self.editor.cy),
                                     (tamano[0] / 2, tamano[1] / 2))
                    self.editor._iniciar_arrastre(SimpleNamespace(x=0, y=0))
                    for x, y in ((10000, -10000), (-10000, 10000)):
                        self.editor._mover(SimpleNamespace(x=x, y=y))
                        a, b, c, d = self.editor._caja()
                        self.assertGreaterEqual(min(a, b), 0)
                        self.assertLessEqual(c, tamano[0])
                        self.assertLessEqual(d, tamano[1])
                        self.assertAlmostEqual(c - a, d - b)
                    self.assertEqual(self.editor.recortar().size, (512, 512))

    def test_arrastre_zoom_y_restablecer(self):
        self.cargar()
        inicial = self.editor.recortar()
        self.editor.zoom.set(2)
        self.editor._cambiar_zoom()
        self.editor._iniciar_arrastre(SimpleNamespace(x=100, y=100))
        self.editor._mover(SimpleNamespace(x=122, y=144))
        self.assertEqual((self.editor.cx, self.editor.cy), (190, 80))
        self.editor._soltar(None)
        self.editor._mover(SimpleNamespace(x=0, y=0))
        self.assertEqual((self.editor.cx, self.editor.cy), (190, 80))
        self.editor._rueda(SimpleNamespace(delta=120))
        self.assertAlmostEqual(self.valor_zoom, 2.2)
        self.editor._rueda(SimpleNamespace(delta=-120))
        self.assertAlmostEqual(self.valor_zoom, 2)
        self.editor.zoom.set(4)
        self.editor._rueda(SimpleNamespace(num=4, delta=0))
        self.assertEqual(self.valor_zoom, 4)
        self.editor.restablecer()
        self.editor._rueda(SimpleNamespace(num=5, delta=0))
        self.assertEqual(self.valor_zoom, 1)
        self.assertIsNone(ImageChops.difference(inicial, self.editor.recortar()).getbbox())

    def perfil(self):
        gestor = GestorUsuarios(os.path.join(self.temporal.name, "usuarios.json"))
        usuario = gestor.registrar_usuario("Ana", "ana", "clave")
        perfil = Perfil.__new__(Perfil)
        perfil.aplicacion = SimpleNamespace(gestor_usuarios=gestor)
        perfil.propietario = usuario
        perfil.usuario = usuario
        perfil.vista_foto = self.editor
        perfil.foto_pendiente = self.cargar()
        perfil.ruta_foto = usuario.foto_perfil
        perfil.vista_foto_frame = Mock()
        perfil.editor = Mock()
        perfil.estado_edicion = Mock()
        perfil.foto_estado = Mock()
        perfil._mostrar_avatar = Mock()
        return perfil, gestor, usuario

    def test_guardar_encuadre_cancelar_y_persistencia(self):
        perfil, gestor, usuario = self.perfil()
        self.editor.zoom.set(2)
        self.editor.cx = 130
        esperado = self.editor.recortar()
        relativa = perfil._persistir_foto("Ana", "Bio")
        destino = os.path.join(self.temporal.name, relativa)
        with Image.open(destino) as guardada:
            self.assertIsNone(ImageChops.difference(esperado, guardada).getbbox())
        recargado = GestorUsuarios(gestor.ruta_archivo).usuarios_por_nombre["ana"]
        self.assertEqual(recargado.foto_perfil, relativa)
        perfil.foto_pendiente = self.cargar((200, 400))
        perfil._cancelar_foto()
        self.assertEqual(usuario.foto_perfil, relativa)
        self.assertTrue(os.path.isfile(destino))
        self.assertIsNone(perfil.foto_pendiente)
        self.assertIsNone(self.editor.original)

    def test_error_json_conserva_foto_y_encuadre(self):
        perfil, gestor, usuario = self.perfil()
        anterior = usuario.foto_perfil
        with patch.object(gestor, "_guardar", side_effect=OSError("sin acceso")):
            with self.assertRaises(OSError):
                perfil._persistir_foto("Ana", "")
        self.assertEqual(usuario.foto_perfil, anterior)
        self.assertIsNotNone(self.editor.original)
        self.assertEqual(os.listdir(os.path.join(self.temporal.name, "avatares")), [])


if __name__ == "__main__":
    unittest.main()
