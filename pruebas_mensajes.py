import os
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch
from gestores.gestor_usuarios import GestorUsuarios
from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_mensajes import GestorMensajes
from main import CampusConnectApp
from PIL import Image
from gestores.gestor_publicaciones import GestorPublicaciones


class PruebasMensajes(unittest.TestCase):
    def test_compartir_referencia_multiple_y_permisos(self):
        publicaciones = GestorPublicaciones(os.path.join(self.carpeta, "publicaciones.json"))
        original = publicaciones.crear_publicacion("ana", "Contenido original")
        with self.assertRaises(PermissionError):
            self.gestor.compartir(["luis", "maria"], original.identificador, publicaciones)
        self.assertEqual(self.gestor.conversacion("luis"), [])
        self.amistades.agregar_amistad("ana", "maria")
        self.amistades.aceptar_solicitud("maria", "ana")
        self.gestor.compartir(["luis", "maria", "luis"], original.identificador, publicaciones)
        for amigo in ("luis", "maria"):
            mensajes = self.gestor.conversacion(amigo)
            self.assertEqual(len(mensajes), 1)
            self.assertEqual(mensajes[0]["publicacion_id"], original.identificador)
            self.assertEqual(mensajes[0]["contenido"], "")
        publicaciones.eliminar_publicacion(original.identificador, "ana")
        with self.assertRaises(ValueError):
            self.gestor.compartir(["luis"], original.identificador, publicaciones)

    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.carpeta = temporal.name
        self.usuarios = GestorUsuarios(os.path.join(self.carpeta, "usuarios.json"))
        for nombre in ("ana", "luis", "maria"):
            self.usuarios.registrar_usuario(nombre, nombre, "clave")
        self.amistades = GestorAmistades(os.path.join(self.carpeta, "amistades.json"), self.usuarios)
        self.amistades.agregar_amistad("ana", "luis")
        self.amistades.aceptar_solicitud("luis", "ana")
        self.actor = self.usuarios.usuarios_por_nombre["ana"]
        self.ruta = os.path.join(self.carpeta, "privado", "mensajes.json")
        self.gestor = GestorMensajes(self.ruta, self.usuarios, self.amistades, lambda: self.actor)

    def test_mensajes_lectura_persistencia_y_permisos(self):
        primero = self.gestor.enviar("luis", "Hola\nLuis")
        segundo = self.gestor.enviar("luis", "¿Cómo estás?")
        self.assertNotEqual(primero["id"], segundo["id"])
        self.assertEqual(self.gestor.conversacion("luis"), [primero, segundo])
        self.assertEqual(self.gestor.conversaciones()[0]["no_leidos"], 0)
        for destino in ("ana", "maria", "inexistente"):
            with self.assertRaises(PermissionError):
                self.gestor.enviar(destino, "No permitido")
            with self.assertRaises(PermissionError):
                self.gestor.conversacion(destino)
        self.actor = self.usuarios.usuarios_por_nombre["luis"]
        nuevo = GestorMensajes(self.ruta, self.usuarios, self.amistades, lambda: self.actor)
        self.assertEqual(nuevo.conversaciones()[0]["no_leidos"], 2)
        self.assertTrue(all(m["leido"] for m in nuevo.conversacion("ana", marcar=True)))
        self.assertEqual(nuevo.conversaciones()[0]["no_leidos"], 0)
        self.actor = self.usuarios.usuarios_por_nombre["maria"]
        self.assertEqual(nuevo.conversaciones(), [])
        self.actor = None
        with self.assertRaises(PermissionError):
            nuevo.conversaciones()

    def test_fallo_conserva_archivo_y_validacion(self):
        self.gestor.enviar("luis", "Original")
        with open(self.ruta, "rb") as archivo:
            antes = archivo.read()
        with patch("gestores.gestor_mensajes.os.replace", side_effect=OSError("fallo")):
            with self.assertRaises(OSError):
                self.gestor.enviar("luis", "No guardado")
        with open(self.ruta, "rb") as archivo:
            self.assertEqual(archivo.read(), antes)
        for texto in ("", "  ", "x" * 5001):
            with self.assertRaises(ValueError):
                self.gestor.enviar("luis", texto)

    def test_imagenes_formatos_persistencia_y_limpieza(self):
        self.gestor.enviar("luis", "Mensaje anterior sin imagen")
        for extension in ("jpg", "jpeg", "png", "webp", "gif"):
            ruta = os.path.join(self.carpeta, "foto." + extension)
            Image.new("RGB", (40, 80), "red").save(ruta)
            mensaje = self.gestor.enviar("luis", "" if extension == "png" else "Foto", ruta)
            self.assertFalse(os.path.isabs(mensaje["ruta_imagen"]))
            self.assertTrue(os.path.isfile(self.gestor.ruta_imagen(mensaje["ruta_imagen"])))
        nuevo = GestorMensajes(self.ruta, self.usuarios, self.amistades, lambda: self.actor)
        self.assertEqual(len(nuevo.conversacion("luis")), 6)
        imagenes = os.path.join(self.carpeta, "privado", "imagenes")
        antes = os.listdir(imagenes)
        with patch.object(self.gestor, "_guardar", side_effect=OSError("fallo")):
            with self.assertRaises(OSError):
                self.gestor.enviar("luis", "", ruta)
        self.assertEqual(os.listdir(imagenes), antes)
        with self.assertRaises(PermissionError):
            self.gestor.enviar("maria", "", ruta)
        with self.assertRaises(ValueError):
            self.gestor.ruta_imagen("../usuarios.json")
        with open(ruta, "wb") as archivo:
            archivo.truncate(10 * 1024 * 1024 + 1)
        with self.assertRaisesRegex(ValueError, "10 MB"):
            self.gestor.enviar("luis", "", ruta)
        with open(ruta, "wb") as archivo:
            archivo.write(b"no es una imagen")
        with self.assertRaises((ValueError, OSError)):
            self.gestor.enviar("luis", "", ruta)

    def test_interfaz_sesion_perfil_amigos_y_temas(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        app = CampusConnectApp(raiz, self.carpeta)
        ana = app.gestor_usuarios.usuarios_por_nombre["ana"]
        luis = app.gestor_usuarios.usuarios_por_nombre["luis"]
        app.mostrar_vista("panel", ana)
        panel = app.vista_instancia
        panel._mostrar_seccion("Mensajes")
        self.assertEqual(len(panel.mensajes.lista.interior.winfo_children()), 1)
        panel.mensajes.busqueda.insert(0, "inexistente")
        panel.mensajes.recargar()
        self.assertEqual(panel.mensajes.lista.interior.winfo_children()[0].cget("text"), "No se encontraron amigos")
        panel.mensajes.busqueda.delete(0, "end")
        panel.mensajes.recargar()
        fila = panel.mensajes.lista.interior.winfo_children()[0]
        self.assertIn("@luis", fila.winfo_children()[1].cget("text"))
        panel.perfil.mostrar(luis)
        panel.perfil.boton_mensaje.invoke()
        self.assertEqual(panel.seccion_activa, "Mensajes")
        chat = panel.mensajes
        self.assertEqual(chat.cabecera.cget("text"), "@luis")
        self.assertEqual(int(chat.entrada.cget("width")), 1)
        self.assertEqual(chat.boton_adjuntar.cget("text"), "")
        self.assertTrue(chat.boton_adjuntar.cget("image"))
        cuerpo = chat.lista.master
        self.assertEqual(cuerpo.grid_columnconfigure(0)["weight"], 1)
        self.assertEqual(cuerpo.grid_columnconfigure(2)["weight"], 2)
        self.assertEqual(chat.lista.interior.winfo_children()[0].cget("background"), "#FCE7EC")
        self.assertEqual(chat.vacio.winfo_manager(), "")
        self.assertIsNotNone(chat.avatar_cabecera._foto_perfil if hasattr(chat.avatar_cabecera, "_foto_perfil") else chat.avatar_cabecera.find_all())
        chat.entrada.insert("1.0", "Hola")
        self.assertEqual(chat._salto(None), "break")
        chat.entrada.insert("end", "Luis")
        self.assertEqual(chat.enviar(), "break")
        self.assertEqual(chat.entrada.get("1.0", "end-1c"), "")
        self.assertEqual(len(chat.historial.interior.winfo_children()), 1)
        burbuja = chat.historial.interior.winfo_children()[0].winfo_children()[0]
        self.assertEqual(burbuja.pack_info()["anchor"], "e")
        app.alternar_tema()
        self.assertEqual(burbuja.cget("background"), "#e4002b")
        self.assertEqual(chat.lista.interior.winfo_children()[0].cget("background"), "#4A1825")
        self.assertTrue(chat.historial.bind("<MouseWheel>"))
        app.mostrar_vista("panel", luis)
        with self.assertRaises(PermissionError):
            panel.gestor_mensajes.enviar("ana", "Sesión anterior")
        panel = app.vista_instancia
        self.assertEqual(panel.botones_navegacion["Mensajes"].cget("text"), "Mensajes (1)")
        panel._mostrar_seccion("Amigos")
        botones = [b for fila in panel.lista_amigos.tarjetas.winfo_children()
                   for b in fila.winfo_children() if isinstance(b, tk.Button)]
        next(b for b in botones if b.cget("text") == "Mensaje").invoke()
        burbuja = panel.mensajes.historial.interior.winfo_children()[0].winfo_children()[0]
        self.assertEqual(burbuja.pack_info()["anchor"], "w")
        self.assertEqual(panel.botones_navegacion["Mensajes"].cget("text"), "Mensajes (0)")
        original = app.gestor_publicaciones.crear_publicacion("ana", "Publicación compartida")
        panel.perfil.mostrar(ana)
        tarjeta = panel.perfil.publicaciones.tarjetas.winfo_children()[0]
        self.assertNotIn("Me divierte", tarjeta.botones_reacciones)
        corazon = tarjeta.botones_reacciones["Me gusta"]
        corazon.invoke()
        self.assertEqual(corazon.cget("text").strip(), "1")
        self.assertEqual(corazon.cget("background"), corazon.master.cget("background"))
        self.assertEqual(corazon.cget("foreground"), "#AEB4C0")
        tarjeta.boton_compartir.invoke()
        overlay = panel.mensajes.ampliacion
        from gui.mensajes import ZonaScroll
        lista = next(w for w in overlay.winfo_children() if isinstance(w, ZonaScroll))
        lista.interior.winfo_children()[0].invoke()
        acciones = next(w for w in overlay.winfo_children() if type(w) is tk.Frame)
        next(w for w in acciones.winfo_children() if w.cget("text") == "Enviar").invoke()
        self.assertIsNone(panel.mensajes.ampliacion)
        self.assertEqual(panel.gestor_mensajes.conversacion("ana")[-1]["publicacion_id"], original.identificador)
        chat = panel.mensajes
        ruta = os.path.join(self.carpeta, "vertical.png")
        Image.new("RGB", (100, 300), "blue").save(ruta)
        with patch("gui.mensajes.filedialog.askopenfilename", return_value=ruta):
            chat.adjuntar()
        self.assertEqual(chat.preview.winfo_manager(), "pack")
        self.assertAlmostEqual(chat.preview_imagen._foto.width() / chat.preview_imagen._foto.height(),
                               1 / 3, delta=0.02)
        chat.quitar_imagen()
        self.assertIsNone(chat.imagen_pendiente)
        with patch("gui.mensajes.filedialog.askopenfilename", return_value=ruta):
            chat.adjuntar()
        chat.enviar()
        self.assertIsNone(chat.imagen_pendiente)
        self.assertEqual(len(chat.historial.interior.winfo_children()), 3)
        guardada = panel.gestor_mensajes.conversacion("ana")[-1]["ruta_imagen"]
        chat.ampliar(panel.gestor_mensajes.ruta_imagen(guardada))
        self.assertEqual(chat.ampliacion.winfo_manager(), "place")
        chat.cerrar_ampliacion()
        self.assertIsNone(chat.ampliacion)
        chat.ver_publicacion(original)
        self.assertEqual(chat.ampliacion.winfo_manager(), "place")
        chat.cerrar_ampliacion()
        chat._perfil_chat()
        self.assertIs(panel.perfil.usuario, ana)
        app.mostrar_vista("inicio")
        with self.assertRaises(PermissionError):
            panel.gestor_mensajes.enviar("ana", "Sesión cerrada")


if __name__ == "__main__":
    unittest.main()
