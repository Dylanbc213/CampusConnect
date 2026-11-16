import os
import json
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
    def insert(self, indice, texto, etiquetas=()):
        self.valor += texto

    def tag_configure(self, etiqueta, **opciones):
        self.opciones[etiqueta] = opciones

    def edit_modified(self, valor=None):
        if valor is not None:
            self.modificado = valor
        return getattr(self, "modificado", False)

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
        self.carpeta_temporal = temporal.name
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

    def test_eliminar_permisos_persistencia_y_fallo(self):
        propia = self.gestor.crear_publicacion("ana", "Propia", "compartida.png")
        otra = self.gestor.crear_publicacion("luis", "Otra", "compartida.png")
        self.gestor.agregar_comentario(propia.identificador, "luis", "Respuesta")
        self.gestor.establecer_reaccion(propia.identificador, "luis", "Me gusta")
        with self.assertRaises(PermissionError):
            self.gestor.eliminar_publicacion(propia.identificador, "luis")
        with patch.object(self.gestor, "_guardar", side_effect=OSError("fallo")):
            with self.assertRaises(OSError):
                self.gestor.eliminar_publicacion(propia.identificador, "ana")
        self.assertEqual(self.gestor.publicaciones, [propia, otra])
        self.assertEqual(len(GestorPublicaciones(self.ruta).publicaciones), 2)
        self.gestor.eliminar_publicacion(propia.identificador, "ana")
        self.assertEqual([p.a_diccionario() for p in GestorPublicaciones(self.ruta).publicaciones],
                         [otra.a_diccionario()])
        with self.assertRaises(ValueError):
            self.gestor.eliminar_publicacion(propia.identificador, "ana")

    def test_cancelar_eliminacion(self):
        from gui.lista_publicaciones import TarjetaPublicacion
        tarjeta = MagicMock()
        with patch("gui.lista_publicaciones.messagebox.askyesno", return_value=False):
            TarjetaPublicacion._eliminar(tarjeta)
        tarjeta.aplicacion.gestor_publicaciones.eliminar_publicacion.assert_not_called()
        tarjeta.winfo_toplevel.assert_not_called()

    def test_reposts_referencias_duplicados_y_persistencia(self):
        original = self.gestor.crear_publicacion("ana", "Original")
        with self.assertRaises(PermissionError):
            self.gestor.repostear(original.identificador, "ana")
        self.gestor.repostear(original.identificador, "luis")
        with self.assertRaises(ValueError):
            self.gestor.repostear(original.identificador, "luis")
        recargado = GestorPublicaciones(self.ruta)
        self.assertEqual(recargado.contar_reposts(original.identificador), 1)
        vista = recargado.obtener_publicaciones_usuario("luis")[0]
        self.assertIs(vista.original, recargado.publicaciones[0])
        self.assertEqual(vista.reposteador, "luis")
        self.amistades.agregar_amistad("maria", "luis")
        self.amistades.aceptar_solicitud("luis", "maria")
        self.assertEqual(recargado.obtener_publicaciones_inicio("maria", self.amistades)[0].reposteador, "luis")
        with open(self.ruta, encoding="utf-8") as archivo:
            registro = json.load(archivo)[-1]
        self.assertEqual(set(registro), {"tipo", "original_id", "nombre_usuario", "fecha"})
        recargado.deshacer_repost(original.identificador, "maria")
        self.assertEqual(recargado.contar_reposts(original.identificador), 1)
        recargado.deshacer_repost(original.identificador, "luis")
        self.assertEqual(len(GestorPublicaciones(self.ruta).publicaciones), 1)
        self.assertEqual(GestorPublicaciones(self.ruta).reposts, [])
        recargado.repostear(original.identificador, "luis")
        with patch.object(recargado, "_guardar", side_effect=OSError("fallo")):
            with self.assertRaises(OSError):
                recargado.eliminar_publicacion(original.identificador, "ana")
        self.assertEqual(recargado.contar_reposts(original.identificador), 1)
        recargado.eliminar_publicacion(original.identificador, "ana")
        self.assertEqual(GestorPublicaciones(self.ruta).reposts, [])

    def test_consultas_propias_y_amigos(self):
        propia = self.gestor.crear_publicacion("ana", "Propia")
        amigo = self.gestor.crear_publicacion("luis", "De Luis")
        self.gestor.crear_publicacion("maria", "De María")
        self.assertEqual(self.gestor.obtener_publicaciones_usuario("ana"), [propia])
        self.assertEqual(self.gestor.obtener_publicaciones_amigos("ana", self.amistades), [])
        self.amistades.agregar_amistad("ana", "luis")
        self.amistades.aceptar_solicitud("luis", "ana")
        self.assertEqual(self.gestor.obtener_publicaciones_amigos("ana", self.amistades), [amigo])
        self.assertEqual(self.gestor.obtener_publicaciones_amigos("luis", self.amistades), [propia])
        recargado = GestorPublicaciones(self.ruta)
        amistades = GestorAmistades(self.amistades.ruta_archivo, self.usuarios)
        self.assertEqual([p.contenido for p in recargado.obtener_publicaciones_amigos("ana", amistades)], ["De Luis"])

    def test_feed_inicio_sin_duplicados_y_comentarios_persistentes(self):
        propia = self.gestor.crear_publicacion("ana", "Propia")
        amiga = self.gestor.crear_publicacion("luis", "De Luis")
        ajena = self.gestor.crear_publicacion("maria", "De María")
        self.amistades.agregar_amistad("ana", "luis")
        self.amistades.aceptar_solicitud("luis", "ana")
        self.gestor.publicaciones.append(propia)
        feed = self.gestor.obtener_publicaciones_inicio("ana", self.amistades)
        self.assertEqual(feed, [amiga, propia])
        self.assertNotIn(ajena, feed)
        with self.assertRaises(ValueError):
            self.gestor.agregar_comentario(propia.identificador, "ana", "  \n")
        comentario = self.gestor.agregar_comentario(propia.identificador, "ana", "  Estoy de acuerdo  ")
        self.assertEqual(comentario["nombre_usuario"], "ana")
        self.assertEqual(comentario["contenido"], "Estoy de acuerdo")
        recargado = GestorPublicaciones(self.ruta)
        self.assertEqual(recargado.publicaciones[0].comentarios, [comentario])
        self.assertEqual(recargado.publicaciones[1].comentarios, [])

    def test_actualizar_recarga_json_externo(self):
        otro_gestor = GestorPublicaciones(self.ruta)
        otro_gestor.crear_publicacion("ana", "Creada en otra sesión")
        self.assertEqual(self.gestor.publicaciones, [])
        self.gestor.recargar()
        self.assertEqual(self.gestor.publicaciones[0].contenido, "Creada en otra sesión")

    def test_orden_cronologico_en_feed_muro_perfil_y_fechas_invalidas(self):
        registros = [
            {"identificador": 1, "nombre_usuario": "ana", "contenido": "Ana anterior",
             "fecha": "2026-02-01T10:00:00"},
            {"identificador": 2, "nombre_usuario": "luis", "contenido": "Luis mismo instante",
             "fecha": "2026-02-03T10:00:00", "comentarios": [{
                 "nombre_usuario": "ana", "fecha": "2026-02-03T10:01:00", "contenido": "Comentario"}]},
            {"identificador": 3, "nombre_usuario": "ana", "contenido": "Ana mismo instante",
             "fecha": "2026-02-03T10:00:00"},
            {"identificador": 4, "nombre_usuario": "luis", "contenido": "Fecha inválida",
             "fecha": "no-es-fecha"},
            {"identificador": 5, "nombre_usuario": "maria", "contenido": "No es del feed",
             "fecha": "2026-02-04T10:00:00"},
        ]
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump(registros, archivo, ensure_ascii=False)
        gestor = GestorPublicaciones(self.ruta)
        self.amistades.agregar_amistad("ana", "luis")
        self.amistades.aceptar_solicitud("luis", "ana")
        with open(self.ruta, "rb") as archivo:
            original = archivo.read()
        self.assertEqual([p.identificador for p in gestor.obtener_publicaciones_inicio("ana", self.amistades)],
                         [3, 2, 1, 4])
        self.assertEqual([p.identificador for p in gestor.obtener_publicaciones_usuario("ana")], [3, 1])
        self.assertEqual([p.identificador for p in gestor.obtener_publicaciones_amigos("ana", self.amistades)],
                         [2, 4])
        self.assertEqual(gestor.publicaciones[1].comentarios[0]["contenido"], "Comentario")
        with open(self.ruta, "rb") as archivo:
            self.assertEqual(archivo.read(), original)
        nueva = gestor.crear_publicacion("ana", "Publicación nueva")
        self.assertEqual(gestor.obtener_publicaciones_inicio("ana", self.amistades)[0], nueva)
        gestor.recargar()
        self.assertEqual(gestor.obtener_publicaciones_inicio("ana", self.amistades)[0].identificador,
                         nueva.identificador)

    def test_publicacion_solo_imagen_y_compatibilidad_json(self):
        antigua = self.gestor.crear_publicacion("ana", "Publicación antigua")
        imagen = self.gestor.crear_publicacion("ana", "", "imagenes_publicaciones/foto.gif")
        con_texto = self.gestor.crear_publicacion("luis", "Comentario de imagen", "imagenes_publicaciones/otra.png")
        recargado = GestorPublicaciones(self.ruta)
        self.assertEqual(recargado.publicaciones[0].ruta_imagen, "")
        self.assertEqual(recargado.publicaciones[1].contenido, "")
        self.assertEqual(recargado.publicaciones[1].ruta_imagen, imagen.ruta_imagen)
        self.assertEqual(recargado.publicaciones[2].contenido, con_texto.contenido)
        self.assertEqual(recargado.publicaciones[2].ruta_imagen, con_texto.ruta_imagen)
        with self.assertRaises(ValueError):
            self.gestor.crear_publicacion("ana", "  ")
        self.assertIsNotNone(antigua)

    def test_reacciones_y_respuestas_con_imagen_persisten(self):
        publicacion = self.gestor.crear_publicacion("ana", "Publicación")
        self.gestor.establecer_reaccion(publicacion.identificador, "ana", "Me gusta")
        self.gestor.establecer_reaccion(publicacion.identificador, "ana", "No me gusta")
        self.gestor.establecer_reaccion(publicacion.identificador, "luis", "Me divierte")
        self.assertEqual(publicacion.reacciones, {"ana": "No me gusta", "luis": "Me divierte"})
        self.assertTrue(self.gestor.quitar_reaccion(publicacion.identificador, "ana"))
        self.assertEqual(publicacion.reacciones, {"luis": "Me divierte"})
        self.gestor.establecer_reaccion(publicacion.identificador, "ana", "Me gusta")
        with self.assertRaises(ValueError):
            self.gestor.agregar_comentario(publicacion.identificador, "ana", "  ")
        texto = self.gestor.agregar_comentario(publicacion.identificador, "ana", "Respuesta")
        imagen = self.gestor.agregar_comentario(
            publicacion.identificador, "luis", "", "imagenes_respuestas/respuesta.gif")
        mixta = self.gestor.agregar_comentario(
            publicacion.identificador, "maria", "Con imagen", "imagenes_respuestas/mixta.png")
        recargada = GestorPublicaciones(self.ruta).publicaciones[0]
        self.assertEqual(recargada.reacciones, {"ana": "Me gusta", "luis": "Me divierte"})
        self.assertEqual(recargada.comentarios, [texto, imagen, mixta])
        self.assertEqual(imagen["contenido"], "")
        self.assertEqual(imagen["ruta_imagen"], "imagenes_respuestas/respuesta.gif")

    def test_hilo_anidado_guarda_ids_y_referencias_y_lee_comentarios_viejos(self):
        publicacion = self.gestor.crear_publicacion("ana", "Tema")
        primera = self.gestor.agregar_comentario(publicacion.identificador, "luis", "Primera")
        anidada = self.gestor.agregar_comentario(
            publicacion.identificador, "ana", "Respuesta a la respuesta", parent_id=primera["id"])
        self.assertEqual(primera["parent_type"], "publicacion")
        self.assertEqual(primera["parent_id"], publicacion.identificador)
        self.assertEqual(anidada["parent_type"], "respuesta")
        self.assertEqual(anidada["parent_id"], primera["id"])
        recargada = GestorPublicaciones(self.ruta).publicaciones[0]
        self.assertEqual(recargada.comentarios, [primera, anidada])

        ruta_vieja = os.path.join(self.carpeta_temporal, "publicaciones_viejas.json")
        with open(ruta_vieja, "w", encoding="utf-8") as archivo:
            json.dump([{
                "identificador": 7, "nombre_usuario": "ana", "contenido": "Antigua",
                "comentarios": [{"nombre_usuario": "luis", "fecha": "2024-01-01T10:00:00",
                                 "contenido": "Comentario viejo"}],
            }], archivo)
        gestor_viejo = GestorPublicaciones(ruta_vieja)
        comentario_viejo = gestor_viejo.publicaciones[0].comentarios[0]
        self.assertEqual(comentario_viejo["id"], 1)
        self.assertEqual(comentario_viejo["parent_id"], 7)
        self.assertEqual(comentario_viejo["parent_type"], "publicacion")

    def test_publicacion_antigua_carga_sin_reacciones_ni_respuestas(self):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write('[{"identificador":1,"nombre_usuario":"ana","contenido":"Antigua","fecha":"2024-01-01T10:00:00"}]')
        antigua = GestorPublicaciones(self.ruta).publicaciones[0]
        self.assertEqual(antigua.reacciones, {})
        self.assertEqual(antigua.comentarios, [])

    def test_reacciones_anteriores_se_conservan_en_json(self):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write('[{"identificador":1,"nombre_usuario":"ana","contenido":"Antigua",'
                          '"fecha":"2024-01-01T10:00:00","reacciones":{"ana":"Me encanta"}}]')
        gestor = GestorPublicaciones(self.ruta)
        publicacion = gestor.publicaciones[0]
        self.assertEqual(publicacion.reacciones["ana"], "Me encanta")
        gestor.establecer_reaccion(1, "ana", "No me gusta")
        self.assertEqual(GestorPublicaciones(self.ruta).publicaciones[0].reacciones["ana"], "No me gusta")

    def test_limite_de_caracteres_y_persistencia(self):
        publicacion = self.gestor.crear_publicacion("ana", "á" * 500)
        for contenido in ("x" * 501, " " + "x" * 500):
            with self.assertRaises(ValueError):
                self.gestor.crear_publicacion("ana", contenido)
        self.assertEqual(self.gestor.publicaciones, [publicacion])
        recargado = GestorPublicaciones(self.ruta)
        self.assertEqual(recargado.publicaciones[0].contenido, "á" * 500)
        self.assertEqual(len(recargado.publicaciones), 1)

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
            self.assertIn("de tus amigos", muro.muro_amigos.valor)
            self.assertEqual(muro.boton_publicar.opciones["state"], "disabled")
            for texto, estado in ((" \n ", "disabled"), ("x" * 500, "normal"), ("x" * 501, "disabled"), ("", "disabled")):
                muro.campo_contenido.valor = texto
                muro.campo_contenido.edit_modified(True)
                muro.campo_contenido.opciones["<<Modified>>"](None)
                self.assertEqual(muro.boton_publicar.opciones["state"], estado)
                self.assertEqual(muro.contador.opciones["text"], "{} / 500 caracteres".format(len(texto)))
            muro._publicar()
            error.assert_not_called()
            exito.assert_not_called()
            muro.campo_contenido.valor = "Texto\ncon dos líneas"
            with patch.object(self.gestor, "_guardar", side_effect=OSError):
                muro._publicar()
            self.assertEqual(muro.campo_contenido.valor, "Texto\ncon dos líneas")
            self.assertEqual(self.gestor.publicaciones, [])
            muro._publicar()
            exito.assert_not_called()
            self.assertEqual(muro.confirmacion.opciones["text"], "Publicación creada correctamente.")
            self.assertEqual(muro.boton_publicar.opciones["state"], "disabled")
            self.assertEqual(muro.contador.opciones["text"], "0 / 500 caracteres")
            self.assertEqual(self.gestor.publicaciones[0].nombre_usuario, "ana")
            self.assertEqual(muro.campo_contenido.valor, "")
            self.assertIn("Ana (@ana)", muro.muro_personal.valor)
            from gui.fechas import fecha_publicacion
            self.assertIn(fecha_publicacion(self.gestor.publicaciones[0].fecha), muro.muro_personal.valor)
            self.assertIn("Texto\ncon dos líneas", muro.muro_personal.valor)
            self.assertEqual(muro.muro_personal.opciones["state"], "disabled")
            self.gestor.crear_publicacion("luis", "Texto de amigo")
            self.gestor.crear_publicacion("maria", "Texto ajeno")
            self.amistades.agregar_amistad("ana", "luis")
            self.amistades.aceptar_solicitud("luis", "ana")
            muro._actualizar()
            self.assertIn("Luis (@luis)", muro.muro_amigos.valor)
            self.assertIn("Texto de amigo", muro.muro_amigos.valor)
            self.assertNotIn("Texto ajeno", muro.muro_amigos.valor)
            app.gestor_publicaciones = GestorPublicaciones(self.ruta)
            reabierto = VentanaMuro(None, app, self.usuarios.usuarios_por_nombre["ana"])
            self.assertEqual(reabierto.muro_personal.valor, muro.muro_personal.valor)
            self.assertEqual(reabierto.muro_amigos.valor, muro.muro_amigos.valor)

    def test_boton_actualizar_recarga_desde_json(self):
        app = SimpleNamespace(gestor_usuarios=self.usuarios, gestor_amistades=self.amistades,
                              gestor_publicaciones=self.gestor)
        with patch("gui.ventana_muro.tk.Label", WidgetSimulado), \
             patch("gui.ventana_muro.tk.Button", WidgetSimulado), \
             patch("gui.ventana_muro.ScrolledText", TextoSimulado):
            muro = VentanaMuro(None, app, self.usuarios.usuarios_por_nombre["ana"])
            otra_sesion = GestorPublicaciones(self.ruta)
            otra_sesion.crear_publicacion("ana", "Recargada desde disco")
            muro.boton_actualizar.invocar()
            self.assertIn("Recargada desde disco", muro.muro_personal.valor)


if __name__ == "__main__":
    unittest.main()
