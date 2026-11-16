"""Prueba local con video y audio sintéticos, sin archivos del usuario."""
import io
import math
import os
import struct
import tempfile
import time
import tkinter as tk
import unittest
from PIL import Image
from gui.reproductor_video import ReproductorVideo


def video_prueba(ruta):
    def chunk(tipo, datos):
        return tipo + struct.pack("<I", len(datos)) + datos + b"\0" * (len(datos) % 2)
    def lista(tipo, datos):
        return chunk(b"LIST", tipo + datos)
    def stream(tipo, codec, escala, tasa, cantidad, tamano, formato):
        cabecera = struct.pack("<4s4sIHHIIIIIIIIhhhh", tipo, codec, 0, 0, 0, 0,
                               escala, tasa, 0, cantidad, 20000, 0xffffffff, tamano, 0, 0, 64, 48)
        return lista(b"strl", chunk(b"strh", cabecera) + chunk(b"strf", formato))
    avih = struct.pack("<14I", 100000, 100000, 0, 0x100, 40, 0, 2, 20000, 64, 48, 0, 0, 0, 0)
    formato = struct.pack("<IiiHH4sIiiII", 40, 64, 48, 1, 24, b"MJPG", 64*48*3, 0, 0, 0, 0)
    audio = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    hdrl = lista(b"hdrl", chunk(b"avih", avih) + stream(b"vids", b"MJPG", 1, 10, 40, 0, formato)
                 + stream(b"auds", b"\0"*4, 1, 8000, 32000, 2, audio))
    frames = []
    for i in range(40):
        foto = io.BytesIO()
        Image.new("RGB", (64, 48), (i * 6, 80, 100)).save(foto, format="JPEG")
        frames.append(chunk(b"00dc", foto.getvalue()))
        sonido = b"".join(struct.pack("<h", int(1200 * math.sin(2*math.pi*440*n/8000)))
                          for n in range(i*800, (i+1)*800))
        frames.append(chunk(b"01wb", sonido))
    with open(ruta, "wb") as archivo:
        archivo.write(chunk(b"RIFF", b"AVI " + hdrl + lista(b"movi", b"".join(frames))))


class PruebasVideo(unittest.TestCase):
    def test_orientacion_vertical_y_pixeles(self):
        from types import SimpleNamespace
        video = SimpleNamespace(width=1024, height=576, sar_num=1, sar_den=1, orientation=6)
        self.assertEqual(ReproductorVideo._dimensiones_video(video), (576, 1024))
        video.orientation = 0
        video.width, video.height = 576, 1024
        self.assertEqual(ReproductorVideo._dimensiones_video(video), (576, 1024))
    def test_reproduccion_integrada_audio_pausa_volumen_y_salida(self):
        import vlc
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.geometry("520x400")
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "prueba.avi")
            video_prueba(ruta)
            reproductor = ReproductorVideo(raiz, ruta, ampliado=True)
            self.addCleanup(lambda: reproductor.destroy() if reproductor.winfo_exists() else None)
            reproductor.pack(fill="both", expand=True)
            raiz.update()
            def esperar(condicion):
                limite = time.monotonic() + 20
                while not condicion() and time.monotonic() < limite:
                    raiz.update()
                    time.sleep(0.03)
                self.assertTrue(condicion(), reproductor.estado.cget("text"))
            esperar(lambda: reproductor.player.get_state() == vlc.State.Playing)
            esperar(lambda: reproductor.player.video_get_size() == (64, 48))
            self.assertEqual(reproductor.player.get_hwnd(), reproductor.pantalla.winfo_id())
            esperar(lambda: reproductor.player.audio_get_track_count() > 1)
            reproductor.volumen.set(30)
            esperar(lambda: reproductor.player.audio_get_volume() == 30)
            reproductor.alternar()
            esperar(lambda: reproductor.player.get_state() == vlc.State.Paused)
            reproductor.alternar()
            esperar(lambda: reproductor.player.get_state() == vlc.State.Playing)
            reproductor.pack_forget()
            raiz.update()
            self.assertFalse(reproductor.player.is_playing())
            reproductor.destroy()
            self.assertIsNone(reproductor.player)
            self.assertIsNone(reproductor.motor)

    def test_preview_silenciosa_proporcion_y_ampliacion(self):
        import vlc
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.geometry("520x600")
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "preview.avi")
            video_prueba(ruta)
            vista = ReproductorVideo(raiz, ruta)
            self.addCleanup(lambda: vista.destroy() if vista.winfo_exists() else None)
            vista.pack(fill="both", expand=True)
            def esperar(condicion):
                limite = time.monotonic() + 20
                while not condicion() and time.monotonic() < limite:
                    raiz.update()
                    time.sleep(.03)
                self.assertTrue(condicion())
            esperar(lambda: vista.player is not None and vista.player.get_state() == vlc.State.Playing)
            esperar(lambda: abs(vista.proporcion - 4/3) < .01)
            self.assertAlmostEqual(vista.pantalla.winfo_width()/vista.pantalla.winfo_height(), 4/3, delta=.02)
            self.assertEqual(vista.pantalla.place_info()["anchor"], "nw")
            self.assertEqual(vista._tamano_redondeado[:2],
                             (vista.pantalla.winfo_width(), vista.pantalla.winfo_height()))
            self.assertEqual(vista.duracion.winfo_manager(), "place")
            self.assertEqual(vista.silencio.winfo_manager(), "place")
            from gui.estilo import aplicar_tema
            for modo in ("claro", "oscuro"):
                aplicar_tema(raiz, modo)
                vista._ajustar()
                self.assertEqual(vista.area.cget("background"), raiz.cget("background"))
                self.assertEqual(vista.duracion.cget("foreground"), "#F9FAFB")
            self.assertEqual(vista.player.audio_get_volume(), 0)
            esperar(lambda: vista.player.audio_get_mute())
            vista.alternar_sonido()
            esperar(lambda: vista.player.audio_get_volume() == 80 and not vista.player.audio_get_mute())
            from unittest.mock import patch
            with patch.object(vista, "_aplicar_sonido", wraps=vista._aplicar_sonido) as sonido:
                limite = time.monotonic() + 1
                while time.monotonic() < limite:
                    raiz.update()
                    time.sleep(.03)
                sonido.assert_not_called()
            self.assertTrue(vista.player.is_playing())
            with Image.open(os.path.join(vista._mascaras.name, str(vista._numero_mascara) + ".png")) as mascara:
                self.assertTrue(any(0 < a < 255 for a in mascara.getchannel("A").tobytes()))
            self.assertIsNone(vista.overlay)
            vista.alternar_sonido()
            esperar(lambda: vista.player.audio_get_mute())
            self.assertEqual(vista.player.audio_get_volume(), 0)
            esperar(lambda: vista.player.get_time() > 2500)
            esperar(lambda: vista.player.is_playing() and 0 <= vista.player.get_time() < 1000)
            self.assertEqual(vista.boton.winfo_viewable(), 0)
            vista.ampliar()
            esperar(lambda: vista.grande.player is not None and vista.grande.player.is_playing())
            esperar(lambda: vista.grande.player.audio_get_track_count() > 1)
            esperar(lambda: vista.grande.player.video_get_size() == (64, 48))
            self.assertFalse(vista.player.is_playing())
            self.assertEqual(int(vista.grande.volumen.cget("length")), 85)
            vista.cerrar_ampliacion()
            esperar(lambda: vista.player.is_playing())
            self.assertIsNone(vista.overlay)
            vista.destroy()


if __name__ == "__main__":
    unittest.main()
