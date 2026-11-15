"""Pruebas de aceptación de la base de CampusConnect (Fase 1)."""

import os
import json
import tempfile
import unittest
from unittest.mock import patch

import tkinter
from gestores.gestor_amistades import GestorAmistades
from gestores.gestor_publicaciones import GestorPublicaciones
from gestores.gestor_usuarios import GestorUsuarios
import main
from main import CampusConnectApp


class WidgetSimulado:
    """Implementación mínima de widget para probar la navegación sin pantalla."""

    creados = []

    def __init__(self, padre=None, **opciones):
        self.padre = padre
        self.opciones = opciones
        self.texto = opciones.get("text", "")
        self.valor = ""
        self.destruido = False
        self.comando = opciones.get("command")
        if padre is not None and hasattr(padre, "hijos"):
            padre.hijos.append(self)
        self.creados.append(self)

    def pack(self, **opciones):
        """Simula el administrador de geometría pack."""

    def configure(self, **opciones):
        self.opciones.update(opciones)

    def bind(self, evento, accion):
        self.opciones[evento] = accion

    def focus_set(self):
        pass

    def destroy(self):
        """Marca el widget como destruido y lo quita de su padre."""
        self.destruido = True
        if self.padre is not None and self in getattr(self.padre, "hijos", []):
            self.padre.hijos.remove(self)

    def winfo_children(self):
        """Devuelve los hijos actuales del widget."""
        return list(getattr(self, "hijos", []))

    def insert(self, indice, texto):
        """Inserta texto en el campo simulado."""
        self.valor = texto + self.valor if indice == 0 else self.valor + texto

    def get(self):
        """Devuelve el contenido del campo simulado."""
        return self.valor

    def invocar(self):
        """Ejecuta el comando asociado a un botón."""
        if self.comando is not None:
            self.comando()


class MarcoSimulado(WidgetSimulado):
    """Marco con soporte para enumerar sus widgets hijos."""

    def __init__(self, padre=None, **opciones):
        self.hijos = []
        super().__init__(padre, **opciones)


class ListaSimulada(WidgetSimulado):
    def __init__(self, padre=None, **opciones):
        super().__init__(padre, **opciones)
        self.elementos = []
        self.seleccion = ()

    def delete(self, inicio, fin):
        self.elementos.clear()
        self.seleccion = ()

    def insert(self, indice, texto):
        self.elementos.append(texto)

    def curselection(self):
        return self.seleccion


class RaizSimulada:
    """Ventana raíz sin dependencias de un servidor gráfico."""

    def title(self, titulo):
        """Acepta el título de ventana."""

    def geometry(self, geometria):
        """Acepta el tamaño de ventana."""

    def mainloop(self):
        """Simula el ciclo de eventos."""
        self.ciclo_iniciado = True


class PruebasFaseUno(unittest.TestCase):
    """Comprueba persistencia, estructuras, autenticación e interfaz."""

    def setUp(self):
        """Prepara archivos aislados para cada prueba."""
        self.directorio = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Elimina los archivos temporales de la prueba."""
        self.directorio.cleanup()

    def _rutas(self):
        """Devuelve las rutas de datos dentro del directorio temporal."""
        return {
            nombre: os.path.join(self.directorio.name, nombre)
            for nombre in ("usuarios.json", "amistades.json", "publicaciones.json")
        }

    def _iniciar_app_simulada(self, rutas):
        """Crea la aplicación con widgets simulados y rutas de prueba."""
        WidgetSimulado.creados = []
        parches = (
            patch.object(tkinter, "Frame", MarcoSimulado),
            patch.object(tkinter, "Label", WidgetSimulado),
            patch.object(tkinter, "Button", WidgetSimulado),
            patch.object(tkinter, "Entry", WidgetSimulado),
            patch.object(tkinter, "Listbox", ListaSimulada),
        )
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)
        aplicacion = CampusConnectApp(RaizSimulada(), self.directorio.name)
        return aplicacion

    def _boton(self, texto):
        """Encuentra el botón visible más reciente con el texto indicado."""
        for widget in reversed(WidgetSimulado.creados):
            if not widget.destruido and widget.texto == texto:
                return widget
        self.fail("No se encontró el botón {!r}".format(texto))

    def test_punto_de_entrada_inicia_la_aplicacion(self):
        """Comprueba que main crea la ventana y ejecuta el ciclo de eventos."""
        raiz = RaizSimulada()
        with patch("main.tk.Tk", return_value=raiz):
            with patch("main.CampusConnectApp") as aplicacion:
                main.main()
        aplicacion.assert_called_once()
        self.assertTrue(aplicacion.call_args.args[1].endswith("datos"))
        self.assertTrue(raiz.ciclo_iniciado)

    def test_archivos_se_crean_vacios_y_datos_se_recargan(self):
        """Crea archivos iniciales y recarga usuarios, amistades y publicaciones."""
        rutas = self._rutas()
        usuarios = GestorUsuarios(rutas["usuarios.json"])
        amistades = GestorAmistades(rutas["amistades.json"], usuarios)
        publicaciones = GestorPublicaciones(rutas["publicaciones.json"])
        self.assertEqual(usuarios.usuarios, [])
        self.assertEqual(amistades.adyacencias, {})
        self.assertEqual(publicaciones.publicaciones, [])
        for ruta in rutas.values():
            self.assertTrue(os.path.isfile(ruta))

        usuarios.registrar_usuario("Ana Pérez", "ana", "clave")
        usuarios.registrar_usuario("Luis Díaz", "luis", "otra")
        amistades.agregar_amistad("ana", "luis")
        amistades.aceptar_solicitud("luis", "ana")
        publicaciones.crear_publicacion("ana", "Hola campus")

        usuarios_recargados = GestorUsuarios(rutas["usuarios.json"])
        amistades_recargadas = GestorAmistades(rutas["amistades.json"])
        publicaciones_recargadas = GestorPublicaciones(rutas["publicaciones.json"])
        self.assertEqual(list(usuarios_recargados.usuarios_por_nombre), ["ana", "luis"])
        self.assertEqual(amistades_recargadas.obtener_amistades("ana"), ["luis"])
        self.assertEqual(amistades_recargadas.obtener_amistades("luis"), ["ana"])
        self.assertEqual(publicaciones_recargadas.publicaciones[0].contenido, "Hola campus")

    def test_archivos_vacios_o_corruptos_se_manejan(self):
        """Los archivos vacíos y JSON inválido se convierten en colecciones vacías."""
        rutas = self._rutas()
        for ruta in rutas.values():
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write("")
        self.assertEqual(GestorUsuarios(rutas["usuarios.json"]).usuarios, [])
        self.assertEqual(GestorAmistades(rutas["amistades.json"]).adyacencias, {})
        self.assertEqual(GestorPublicaciones(rutas["publicaciones.json"]).publicaciones, [])
        with open(rutas["usuarios.json"], "w", encoding="utf-8") as archivo:
            archivo.write("{JSON dañado")
        self.assertEqual(GestorUsuarios(rutas["usuarios.json"]).usuarios, [])

    def test_registro_inicio_de_sesion_y_navegacion(self):
        """Ejecuta la aplicación simulada y navega registro -> login -> panel."""
        rutas = self._rutas()
        aplicacion = self._iniciar_app_simulada(rutas)
        self.assertEqual(aplicacion.vista_actual, "inicio")

        self._boton("Registrarse").invocar()
        self.assertEqual(aplicacion.vista_actual, "registro")
        campos_registro = [
            widget for widget in WidgetSimulado.creados
            if not widget.destruido and widget in aplicacion.contenedor.hijos
            and widget.comando is None and not widget.texto
        ]
        self.assertEqual(len(campos_registro), 4)
        campos_registro[0].insert(0, "Estudiante Ejemplo")
        campos_registro[1].insert(0, "estudiante")
        campos_registro[2].insert(0, "secreto")
        campos_registro[3].insert(0, "secreto")
        with patch("gui.ventana_registro.messagebox.showinfo"):
            with patch("gui.ventana_registro.messagebox.showerror"):
                self._boton("Crear cuenta").invocar()
        self.assertEqual(aplicacion.vista_actual, "login")

        campos_login = [
            widget for widget in WidgetSimulado.creados
            if not widget.destruido and widget in aplicacion.contenedor.hijos
            and widget.comando is None and not widget.texto
        ]
        campos_login[0].insert(0, "estudiante")
        campos_login[1].insert(0, "secreto")
        with patch("gui.ventana_login.messagebox.showinfo") as exito:
            self._boton("Entrar").invocar()
        exito.assert_called_once()
        self.assertEqual(aplicacion.vista_actual, "panel")
        self.assertEqual(aplicacion.usuario_actual.nombre_usuario, "estudiante")
        self._boton("Cerrar sesión").invocar()
        self.assertEqual(aplicacion.vista_actual, "inicio")
        self.assertIsNone(aplicacion.usuario_actual)

        usuario = GestorUsuarios(rutas["usuarios.json"]).iniciar_sesion(
            "estudiante", "secreto"
        )
        self.assertIsNotNone(usuario)
        self.assertIsNone(
            GestorUsuarios(rutas["usuarios.json"]).iniciar_sesion("estudiante", "incorrecta")
        )


    def test_validaciones_y_persistencia_de_usuarios(self):
        ruta = self._rutas()["usuarios.json"]
        gestor = GestorUsuarios(ruta)
        original = gestor.registrar_usuario("Ana Pérez", "ana", " clave ")
        with open(ruta, "rb") as archivo:
            contenido = archivo.read()
        for campo in range(3):
            for vacio in ("", "   "):
                datos = ["Luis", "luis", "secreto"]
                datos[campo] = vacio
                with self.subTest(campo=campo, vacio=vacio):
                    with self.assertRaises(ValueError):
                        gestor.registrar_usuario(*datos)
        with self.assertRaises(ValueError):
            gestor.registrar_usuario("Otra Ana", " ana ", "otra")
        for usuario, clave in (("", "clave"), ("ana", ""), (" ", "clave"), ("ana", " ")):
            with self.assertRaises(ValueError):
                gestor.iniciar_sesion(usuario, clave)
        self.assertIsNone(gestor.iniciar_sesion("ausente", "clave"))
        self.assertIsNone(gestor.iniciar_sesion("ana", "clave"))
        with open(ruta, "rb") as archivo:
            self.assertEqual(archivo.read(), contenido)
        gestor.registrar_usuario("Luis", "luis", "secreto")
        recargado = GestorUsuarios(ruta)
        self.assertEqual(len(recargado.usuarios), 2)
        self.assertEqual(recargado.iniciar_sesion(" ana ", " clave ").a_diccionario(), original.a_diccionario())

    def test_error_de_guardado_no_registra_usuario(self):
        gestor = GestorUsuarios(self._rutas()["usuarios.json"])
        with patch("gestores.gestor_usuarios.guardar_json", side_effect=OSError):
            with self.assertRaises(OSError):
                gestor.registrar_usuario("Ana", "ana", "clave")
        self.assertEqual(gestor.usuarios, [])
        self.assertIsNone(gestor.iniciar_sesion("ana", "clave"))
        self.assertEqual(GestorUsuarios(gestor.ruta_archivo).usuarios, [])

    def test_mensajes_de_error_en_formularios(self):
        app = self._iniciar_app_simulada(self._rutas())
        for vista, boton in (("registro", "Crear cuenta"), ("login", "Entrar")):
            app.mostrar_vista(vista)
            with patch("tkinter.messagebox.showerror") as error:
                self._boton(boton).invocar()
            error.assert_called_once()
            self.assertEqual(app.vista_actual, vista)
            self.assertIsNone(app.usuario_actual)
        campos = [w for w in app.contenedor.hijos if not w.texto and w.comando is None]
        campos[0].insert(0, "ausente")
        campos[1].insert(0, "incorrecta")
        with patch("tkinter.messagebox.showerror") as error:
            self._boton("Entrar").invocar()
        error.assert_called_once_with("Acceso denegado", "Usuario o contraseña incorrectos.")
        self.assertEqual(app.vista_actual, "login")


    def test_busqueda_por_nombre_y_usuario(self):
        gestor = GestorUsuarios(self._rutas()["usuarios.json"])
        ana = gestor.registrar_usuario("Ana Pérez", "aperez", "clave")
        gestor.registrar_usuario("Luis", "ldiaz", "clave")
        for consulta in (" ANA ", "PÉREZ", "APER"):
            self.assertEqual(gestor.buscar_usuarios(consulta), [ana])
        for consulta in ("", "  ", "ausente"):
            self.assertEqual(gestor.buscar_usuarios(consulta), [])

    def test_amistades_validaciones_y_persistencia(self):
        rutas = self._rutas()
        usuarios = GestorUsuarios(rutas["usuarios.json"])
        for nombre in ("ana", "luis", "maria"):
            usuarios.registrar_usuario(nombre, nombre, "clave")
        gestor = GestorAmistades(rutas["amistades.json"], usuarios)
        gestor.agregar_amistad("ana", "luis")
        gestor.aceptar_solicitud("luis", "ana")
        for pareja in (("ana", "ana"), ("ana", "luis"), ("luis", "ana"), ("ana", "ausente")):
            with self.subTest(pareja=pareja), self.assertRaises(ValueError):
                gestor.agregar_amistad(*pareja)
        copia = gestor.obtener_amistades("ana")
        copia.clear()
        self.assertEqual(gestor.obtener_amistades("ana"), ["luis"])
        with open(rutas["amistades.json"], "rb") as archivo:
            contenido = archivo.read()
        with patch("gestores.gestor_amistades.os.replace", side_effect=OSError):
            with self.assertRaises(OSError):
                gestor.agregar_amistad("ana", "maria")
        with open(rutas["amistades.json"], "rb") as archivo:
            self.assertEqual(archivo.read(), contenido)
        self.assertEqual(gestor.obtener_amistades("maria"), [])
        gestor.agregar_amistad("ana", "maria")
        gestor.aceptar_solicitud("maria", "ana")
        recargado = GestorAmistades(rutas["amistades.json"], usuarios)
        self.assertEqual(recargado.obtener_amistades("ana"), ["luis", "maria"])
        self.assertEqual(recargado.obtener_amistades("luis"), ["ana"])
        self.assertEqual(recargado.obtener_amistades("maria"), ["ana"])

    def test_carga_normaliza_amistades_bidireccionales(self):
        ruta = self._rutas()["amistades.json"]
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump({"ana": ["ana", "luis", "luis"]}, archivo)
        gestor = GestorAmistades(ruta)
        self.assertEqual(gestor.adyacencias, {"ana": ["luis"], "luis": ["ana"]})

    def test_busqueda_y_amistades_en_panel(self):
        from gui.panel_principal import PanelPrincipal

        app = self._iniciar_app_simulada(self._rutas())
        ana = app.gestor_usuarios.registrar_usuario("Ana", "ana", "clave")
        luis = app.gestor_usuarios.registrar_usuario("Luis", "luis", "clave")
        panel = PanelPrincipal(app.contenedor, app, ana)
        with patch("tkinter.messagebox.showerror") as error, patch("tkinter.messagebox.showinfo") as exito:
            self._boton("Agregar amigo").invocar()
            error.assert_called_once()
            error.reset_mock()
            self._boton("Buscar").invocar()
            error.assert_not_called()
            self.assertEqual(panel.estado_busqueda.opciones["text"], "Escribe un nombre o usuario.")
            panel.campo_busqueda.valor = "ausente"
            self._boton("Buscar").invocar()
            self.assertEqual(panel.lista_resultados.elementos, [])
            self.assertEqual(panel.estado_busqueda.opciones["text"], "No se encontraron usuarios.")
            self.assertEqual(panel.contador_amigos.opciones["text"], "Mis amigos (0)")
            self.assertIn("Aún no tienes amigos", panel.estado_amigos.opciones["text"])
            panel.campo_busqueda.valor = "lU"
            panel.campo_busqueda.opciones["<KeyRelease>"](None)
            self.assertEqual(panel.lista_resultados.elementos, ["Luis (@luis)"])
            panel.lista_resultados.seleccion = (0,)
            panel.lista_resultados.opciones["<<ListboxSelect>>"](None)
            self.assertEqual(panel.boton_agregar.opciones["state"], "normal")
            with patch.object(app.gestor_amistades, "_guardar", side_effect=OSError):
                self._boton("Agregar amigo").invocar()
            self.assertEqual(panel.lista_amigos.elementos, [])
            self._boton("Agregar amigo").invocar()
            self.assertEqual(panel.lista_amigos.elementos, ["Luis (@luis)"])
            self.assertEqual(panel.contador_amigos.opciones["text"], "Mis amigos (1)")
            self.assertEqual(panel.estado_amigos.opciones["text"], "")
            self.assertEqual(panel.lista_resultados.elementos, ["Luis (@luis) — Ya son amigos"])
            panel.lista_resultados.seleccion = (0,)
            panel._actualizar_seleccion()
            self.assertEqual(panel.boton_agregar.opciones["state"], "disabled")
            exito.assert_called_with("Amistades", "Amigo agregado correctamente.")
            error.reset_mock()
            self._boton("Agregar amigo").invocar()
            error.assert_called_once()
            panel.campo_busqueda.valor = "ana"
            self._boton("Buscar").invocar()
            panel.lista_resultados.seleccion = (0,)
            panel._actualizar_seleccion()
            self.assertEqual(panel.boton_agregar.opciones["state"], "disabled")
            self.assertEqual(panel.lista_resultados.elementos, ["Ana (@ana) — Tú"])
            error.reset_mock()
            self._boton("Agregar amigo").invocar()
            error.assert_called_once()
        panel_luis = PanelPrincipal(app.contenedor, app, luis)
        self.assertEqual(panel_luis.lista_amigos.elementos, ["Ana (@ana)"])


if __name__ == "__main__":
    unittest.main()
