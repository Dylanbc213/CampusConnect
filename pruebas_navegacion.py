import base64
import binascii
import os
import struct
import tempfile
import tkinter as tk
import unittest
import zlib
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gestores.gestor_usuarios import GestorUsuarios
from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_publicaciones import GestorPublicaciones
from gui.estilo import preparar
from gui.panel_principal import PanelPrincipal


def crear_png(ruta, ancho, alto):
    def bloque(tipo, datos):
        return (struct.pack(">I", len(datos)) + tipo + datos
                + struct.pack(">I", binascii.crc32(tipo + datos) & 0xFFFFFFFF))

    encabezado = struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)
    fila = b"\x00" + b"\xC0\x50\x80" * ancho
    contenido = (b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", encabezado)
                 + bloque(b"IDAT", zlib.compress(fila * alto)) + bloque(b"IEND", b""))
    with open(ruta, "wb") as archivo:
        archivo.write(contenido)


class PruebasNavegacion(unittest.TestCase):
    def test_tarjetas_busqueda_agregar_y_abrir_perfil(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            luis = usuarios.registrar_usuario("Luis Sol", "luis", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            panel.campo_busqueda.insert(0, "luis")
            panel._buscar()
            self.assertEqual(len(panel.tarjetas_resultados), 1)
            self.assertIn("luis", panel.tarjetas_resultados)
            self.assertTrue(panel.tarjetas_resultados["luis"].bind("<MouseWheel>"))
            self.assertTrue(panel.canvas_resultados.cget("yscrollcommand"))
            panel.tarjetas_resultados["luis"].invoke()
            self.assertEqual(amistades.obtener_amistades("ana"), [])
            amistades.aceptar_solicitud("luis", "ana")
            panel._actualizar_amigos()
            panel._buscar()
            self.assertEqual(amistades.obtener_amistades("ana"), ["luis"])
            self.assertEqual(panel.contador_amigos.cget("text"), "1 amigo")
            tarjeta = next(widget for widget in panel.lista_resultados.winfo_children()
                           if widget is not panel.resultado_vacio)
            etiquetas = [widget.cget("text") for widget in tarjeta.winfo_children()
                         if isinstance(widget, tk.Label)]
            self.assertIn("✓ Amigos", etiquetas)
            self.assertIn("@luis", etiquetas)
            self.assertNotIn("Luis Sol", etiquetas)
            panel.abrir_perfil(luis)
            raiz.update_idletasks()
            self.assertEqual(panel.seccion_activa, "Mi perfil")
            self.assertEqual(panel.perfil.nombre.cget("text"), "@luis")
            self.assertEqual(panel.perfil.editor.winfo_manager(), "")
            self.assertEqual(type(panel.perfil.publicaciones).__name__, "ListaPublicaciones")
            panel.abrir_perfil(ana)
            self.assertEqual(panel.perfil.editor.winfo_manager(), "")
            panel.perfil.boton_editar.invoke()
            self.assertNotEqual(panel.perfil.editor.winfo_manager(), "")
            panel.perfil._cancelar()
            panel.volver_perfil()
            self.assertEqual(panel.perfil.usuario, luis)
            panel.volver_perfil()
            self.assertEqual(panel.seccion_activa, "Inicio")
            self.assertEqual(len([frame for frame in panel.secciones.values() if frame.winfo_manager()]), 1)

    def test_editar_perfil_cancelar_guardar_y_refrescar_vistas(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            luis = usuarios.registrar_usuario("Luis", "luis", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            amistades.agregar_amistad("ana", "luis")
            amistades.aceptar_solicitud("luis", "ana")
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            publicaciones.crear_publicacion("ana", "Publicación propia")
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            panel._mostrar_seccion("Mi perfil")
            perfil = panel.perfil
            perfil.boton_editar.invoke()
            self.assertGreater(perfil.campo_bio.winfo_reqheight(), 1)
            self.assertEqual(perfil.campo_bio.winfo_manager(), "pack")
            self.assertEqual(perfil.publicaciones.winfo_manager(), "")
            perfil.campo_nombre.delete(0, "end")
            perfil.campo_nombre.insert(0, "Nombre descartado")
            perfil._cancelar()
            self.assertNotEqual(perfil.publicaciones.winfo_manager(), "")
            self.assertEqual(ana.nombre_visible, "Ana")
            perfil.boton_editar.invoke()
            perfil.campo_nombre.delete(0, "end")
            perfil.campo_nombre.insert(0, "Ana Actualizada")
            perfil.campo_bio.insert("1.0", "Perfil de prueba")
            panel.campo_busqueda.insert(0, "Ana Actualizada")
            perfil.boton_guardar.invoke()
            self.assertEqual(perfil.estado_edicion.cget("text"), "Cambios guardados correctamente.")
            self.assertEqual(usuarios.usuarios_por_nombre["ana"].nombre_usuario, "ana")
            self.assertEqual(amistades.obtener_amistades("ana"), ["luis"])
            autor = panel.muro.lista_inicio.tarjetas.winfo_children()[0].autor
            self.assertEqual(autor.cget("text"), "@ana")
            recargado = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana_guardada = recargado.usuarios_por_nombre["ana"]
            self.assertEqual(ana_guardada.nombre_visible, "Ana Actualizada")
            self.assertEqual(ana_guardada.biografia, "Perfil de prueba")
            self.assertEqual(ana_guardada.contrasena, ana.contrasena)
            self.assertEqual([usuario.nombre_usuario for usuario in panel.resultados], ["ana"])

    def test_foto_perfil_previsualiza_guarda_y_persiste(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            perfil = panel.perfil
            perfil._editar()
            ruta = os.path.join(carpeta, "avatar.png")
            crear_png(ruta, 100, 60)
            with patch("gui.perfil.filedialog.askopenfilename", return_value=ruta):
                perfil._elegir_foto()
            self.assertEqual(perfil.vista_foto_frame.winfo_manager(), "pack")
            self.assertIsNotNone(perfil.vista_foto.original)
            editor = perfil.vista_foto
            self.assertTrue(editor.canvas.bind("<B1-Motion>"))
            self.assertTrue(editor.canvas.bind("<MouseWheel>"))
            self.assertFalse(perfil.bind("<MouseWheel>"))
            editor.slider.set(2)
            editor._iniciar_arrastre(SimpleNamespace(x=100, y=100))
            editor._mover(SimpleNamespace(x=122, y=144))
            self.assertLess(editor.cx, 50)
            self.assertLess(editor.cy, 30)
            editor._rueda(SimpleNamespace(delta=120))
            self.assertAlmostEqual(editor.zoom.get(), 2.2)
            fila = perfil.boton_guardar_foto.master
            next(boton for boton in fila.winfo_children()
                 if boton.cget("text") == "Restablecer").invoke()
            self.assertEqual((editor.cx, editor.cy, editor.zoom.get()), (50, 30, 1))
            editor.slider.set(2)
            raiz.after(30, raiz.quit)
            raiz.mainloop()
            self.assertIsNotNone(editor._foto)
            self.assertEqual(editor._foto.width(), editor.LADO)
            esperado = editor.recortar()
            perfil.boton_guardar_foto.invoke()
            guardada = GestorUsuarios(os.path.join(carpeta, "usuarios.json")).usuarios_por_nombre["ana"]
            self.assertTrue(guardada.foto_perfil.startswith("avatares/ana_"))
            self.assertTrue(os.path.exists(os.path.join(carpeta, guardada.foto_perfil)))
            from PIL import Image, ImageChops
            with Image.open(os.path.join(carpeta, guardada.foto_perfil)) as foto:
                self.assertEqual(foto.size, (512, 512))
                self.assertIsNone(ImageChops.difference(esperado, foto).getbbox())
            self.assertEqual(perfil.foto_estado.cget("text"), os.path.basename(guardada.foto_perfil))
            foto_guardada = guardada.foto_perfil
            with patch("gui.perfil.filedialog.askopenfilename", return_value=ruta):
                perfil._elegir_foto()
            perfil.boton_cancelar_foto.invoke()
            self.assertEqual(ana.foto_perfil, foto_guardada)
            self.assertEqual(perfil.vista_foto_frame.winfo_manager(), "")

    def test_autores_de_publicacion_y_comentario_abren_perfil(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            luis = usuarios.registrar_usuario("Luis", "luis", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            amistades.agregar_amistad("ana", "luis")
            amistades.aceptar_solicitud("luis", "ana")
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            post = publicaciones.crear_publicacion("luis", "Publicación de Luis")
            publicaciones.agregar_comentario(post.identificador, "ana", "Comentario de Ana")
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            raiz.update_idletasks()
            tarjeta = panel.muro.lista_inicio.tarjetas.winfo_children()[0]
            self.assertTrue(tarjeta.autor.bind("<MouseWheel>"))
            tarjeta.autor.event_generate("<Button-1>")
            self.assertEqual(panel.perfil.usuario, luis)
            tarjeta._alternar()
            fila_comentario = tarjeta.comentarios_frame.winfo_children()[0]
            def buscar_autor(widget):
                if isinstance(widget, tk.Label) and widget.cget("text").startswith("@ana"):
                    return widget
                for hijo in widget.winfo_children():
                    encontrado = buscar_autor(hijo)
                    if encontrado:
                        return encontrado
                return None
            autor_comentario = buscar_autor(fila_comentario)
            self.assertTrue(autor_comentario.bind("<Button-1>"))
            self.assertTrue(autor_comentario.bind("<MouseWheel>"))
            raiz.update_idletasks()
            autor_comentario.event_generate("<Button-1>", x=10, y=5)
            raiz.update()
            self.assertEqual(panel.perfil.usuario, ana)

    def test_enter_publica_shift_enter_salta_linea_y_comentarios_no_publican(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            campo = panel.muro.campo_contenido
            self.assertTrue(campo.bind("<Return>"))
            self.assertTrue(campo.bind("<Shift-Return>"))
            campo.insert("1.0", "Línea uno")
            campo.mark_set("insert", "end-1c")
            panel.muro._enter_salto_linea(SimpleNamespace(state=1))
            self.assertIn("\n", campo.get("1.0", "end-1c"))
            campo.insert("end-1c", "Línea dos")
            panel.muro._enter_publicar(SimpleNamespace(state=0))
            propias = publicaciones.obtener_publicaciones_usuario("ana")
            self.assertEqual(len(propias), 1)
            self.assertEqual(propias[0].contenido, "Línea uno\nLínea dos")
            panel.muro._enter_publicar(SimpleNamespace(state=0))
            self.assertEqual(len(publicaciones.obtener_publicaciones_usuario("ana")), 1)
            tarjeta = panel.muro.lista_inicio.tarjetas.winfo_children()[0]
            tarjeta._reaccionar("Me gusta")
            self.assertEqual(publicaciones.publicaciones[0].reacciones, {"ana": "Me gusta"})
            self.assertIn("1", tarjeta.botones_reacciones["Me gusta"].cget("text"))
            tarjeta._reaccionar("No me gusta")
            self.assertEqual(publicaciones.publicaciones[0].reacciones, {"ana": "No me gusta"})
            tarjeta._reaccionar("No me gusta")
            self.assertEqual(publicaciones.publicaciones[0].reacciones, {})
            tarjeta._reaccionar("Me gusta")
            tarjeta._alternar()
            self.assertNotEqual(tarjeta.boton_enviar_respuesta.cget("image"), "")
            self.assertNotEqual(tarjeta.boton_imagen_respuesta.cget("image"), "")
            self.assertEqual(tarjeta.boton_enviar_respuesta.cget("background"),
                             tarjeta.boton_enviar_respuesta.master.cget("background"))
            self.assertEqual(tarjeta.boton_imagen_respuesta.cget("background"),
                             tarjeta.boton_imagen_respuesta.master.cget("background"))
            tarjeta.campo_comentario.insert(0, "Respuesta")
            self.assertTrue(tarjeta.campo_comentario.bind("<Return>"))
            tarjeta._comentar()
            self.assertEqual(len(publicaciones.obtener_publicaciones_usuario("ana")), 1)
            self.assertEqual(len(propias[0].comentarios), 1)
            primera = propias[0].comentarios[0]
            tarjeta._responder_a(primera)
            self.assertIn("@ana", tarjeta.etiqueta_destinatario.cget("text"))
            tarjeta.campo_comentario.insert(0, "Respuesta anidada")
            tarjeta._comentar()
            anidada = propias[0].comentarios[1]
            self.assertEqual(anidada["parent_type"], "respuesta")
            self.assertEqual(anidada["parent_id"], primera["id"])
            tarjeta._ver_conversacion(anidada)
            self.assertEqual(tarjeta.conversacion_id, anidada["id"])
            tarjeta._cerrar_conversacion()
            origen = os.path.join(carpeta, "respuesta.gif")
            with open(origen, "wb") as archivo:
                archivo.write(base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"))
            with patch("gui.lista_publicaciones.filedialog.askopenfilename", return_value=origen):
                tarjeta._seleccionar_imagen_respuesta()
            self.assertIsNotNone(tarjeta.preview_respuesta)
            tarjeta._comentar()
            self.assertEqual(len(propias[0].comentarios), 3)
            self.assertTrue(propias[0].comentarios[2]["ruta_imagen"])
            self.assertTrue(tarjeta.imagenes_respuestas)
            recargadas = GestorPublicaciones(publicaciones.ruta_archivo).publicaciones[0]
            self.assertEqual(recargadas.reacciones["ana"], "Me gusta")
            self.assertEqual(len(recargadas.comentarios), 3)

    def test_publicar_imagen_mostrarla_y_persistir_ruta(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            self.assertEqual(panel.muro.boton_actualizar.pack_info()["side"], "left")
            self.assertEqual(panel.muro.boton_actualizar.cget("background"),
                             panel.muro.boton_actualizar.master.cget("background"))
            muro = panel.muro
            self.assertEqual(muro.compositor.winfo_manager(), "")
            muro.boton_agregar.invoke()
            self.assertEqual(muro.compositor.winfo_manager(), "pack")
            muro.campo_contenido.insert("1.0", "Borrador")
            muro.boton_cancelar.invoke()
            self.assertEqual(muro.compositor.winfo_manager(), "")
            self.assertEqual(muro.campo_contenido.get("1.0", "end-1c"), "")
            origen = os.path.join(carpeta, "prueba.gif")
            with open(origen, "wb") as archivo:
                archivo.write(base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"))
            muro.boton_agregar.invoke()
            muro.imagen_seleccionada = origen
            muro._actualizar_formulario()
            self.assertEqual(muro.boton_publicar.cget("state"), "normal")
            muro._publicar()
            post = publicaciones.obtener_publicaciones_usuario("ana")[0]
            self.assertEqual(post.contenido, "")
            ruta_guardada = os.path.join(carpeta, post.ruta_imagen)
            self.assertTrue(os.path.exists(ruta_guardada))
            tarjeta = panel.muro.lista_inicio.tarjetas.winfo_children()[0]
            self.assertIsNotNone(tarjeta.imagen)
            self.assertEqual(panel.muro.lista_inicio.scroll.winfo_manager(), "")
            self.assertEqual(panel.muro.boton_actualizar.cget("text"), "⟳")
            self.assertEqual(tarjeta.boton_comentarios.winfo_manager(), "")
            tarjeta.boton_responder.invoke()
            self.assertEqual(tarjeta.comentarios_frame.winfo_manager(), "grid")
            tarjeta.campo_comentario.insert(0, "Respuesta desde la tarjeta")
            tarjeta._comentar()
            self.assertEqual(tarjeta.boton_comentarios.winfo_manager(), "")
            self.assertEqual(tarjeta.boton_responder.winfo_manager(), "grid")
            self.assertEqual(tarjeta.boton_responder.grid_info()["column"], 0)
            self.assertEqual(tarjeta.boton_responder.grid_info()["sticky"], "w")
            recargado = GestorPublicaciones(publicaciones.ruta_archivo)
            self.assertEqual(recargado.publicaciones[0].ruta_imagen, post.ruta_imagen)

    def test_vista_previa_vertical_horizontal_y_cuadrada(self):
        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            rutas = []
            for nombre, ancho, alto in (("vertical", 120, 600), ("horizontal", 600, 120), ("cuadrada", 300, 300)):
                ruta = os.path.join(carpeta, nombre + ".png")
                crear_png(ruta, ancho, alto)
                rutas.append((ruta, ancho, alto))
            with patch("gui.ventana_muro.filedialog.askopenfilename", side_effect=[ruta for ruta, _, _ in rutas]):
                for ruta, ancho_original, alto_original in rutas:
                    panel.muro._seleccionar_imagen()
                    foto = panel.muro.preview_imagen
                    self.assertAlmostEqual(foto.width() / foto.height(), ancho_original / alto_original, delta=0.05)
                    self.assertGreater(float(panel.muro.preview_canvas.cget("height")), 1)
                    if alto_original > ancho_original:
                        self.assertGreater(float(panel.muro.preview_canvas.cget("scrollregion").split()[-1]),
                                           float(panel.muro.preview_canvas.cget("height")))
            self.assertEqual(panel.muro.imagen_seleccionada, rutas[-1][0])
            panel.muro._quitar_imagen()
            self.assertIsNone(panel.muro.imagen_seleccionada)
            self.assertEqual(panel.muro.preview_frame.winfo_manager(), "")

    def test_formatos_de_foto_y_publicacion_jpeg(self):
        from PIL import Image

        raiz = tk.Tk()
        self.addCleanup(raiz.destroy)
        raiz.withdraw()
        preparar(raiz)
        with tempfile.TemporaryDirectory() as carpeta:
            usuarios = GestorUsuarios(os.path.join(carpeta, "usuarios.json"))
            ana = usuarios.registrar_usuario("Ana", "ana", "clave")
            amistades = GestorAmistades(os.path.join(carpeta, "amistades.json"), usuarios)
            publicaciones = GestorPublicaciones(os.path.join(carpeta, "publicaciones.json"))
            app = SimpleNamespace(raiz=raiz, gestor_usuarios=usuarios, gestor_amistades=amistades,
                                  gestor_publicaciones=publicaciones, mostrar_vista=Mock())
            contenedor = tk.Frame(raiz)
            contenedor.pack(fill="both", expand=True)
            panel = PanelPrincipal(contenedor, app, ana)
            rutas = []
            for extension, dimensiones in (("jpg", (600, 300)), ("jpeg", (300, 600)),
                                           ("png", (400, 400)), ("webp", (640, 320)),
                                           ("gif", (320, 640))):
                ruta = os.path.join(carpeta, "foto." + extension)
                Image.new("RGB", dimensiones, (180, 70, 100)).save(ruta, format=extension.upper() if extension != "jpg" else "JPEG")
                rutas.append((ruta, dimensiones))
            with patch("gui.ventana_muro.filedialog.askopenfilename", side_effect=[ruta for ruta, _ in rutas]):
                for ruta, (ancho, alto) in rutas:
                    panel.muro._seleccionar_imagen()
                    self.assertEqual(panel.muro.imagen_seleccionada, ruta)
                    self.assertAlmostEqual(panel.muro.preview_imagen.width() / panel.muro.preview_imagen.height(),
                                           ancho / alto, delta=0.03)
            ruta_jpeg = rutas[0][0]
            panel.muro.imagen_seleccionada = ruta_jpeg
            panel.muro._actualizar_formulario()
            panel.muro._publicar()
            post = publicaciones.obtener_publicaciones_usuario("ana")[0]
            self.assertTrue(post.ruta_imagen.endswith(".jpg"))
            tarjeta = panel.muro.lista_inicio.tarjetas.winfo_children()[0]
            self.assertIsNotNone(tarjeta.imagen)
            tarjeta._alternar()
            with patch("gui.lista_publicaciones.filedialog.askopenfilename",
                       side_effect=[ruta for ruta, _ in rutas]):
                for ruta, _ in rutas:
                    tarjeta._seleccionar_imagen_respuesta()
                    self.assertEqual(tarjeta.imagen_respuesta, ruta)
                    self.assertIsNotNone(tarjeta.preview_respuesta)
                    tarjeta._quitar_imagen_respuesta()

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
            amistades.aceptar_solicitud("luis", "ana")
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
                self.assertEqual(textos, ["@luis"])
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
