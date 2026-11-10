"""Pruebas de aceptación de la base de CampusConnect (Fase 1)."""

import os
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
        self.assertEqual(len(campos_registro), 3)
        campos_registro[0].insert(0, "Estudiante Ejemplo")
        campos_registro[1].insert(0, "estudiante")
        campos_registro[2].insert(0, "secreto")
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
        self._boton("Entrar").invocar()
        self.assertEqual(aplicacion.vista_actual, "panel")
        self._boton("Cerrar sesión").invocar()
        self.assertEqual(aplicacion.vista_actual, "inicio")

        usuario = GestorUsuarios(rutas["usuarios.json"]).iniciar_sesion(
            "estudiante", "secreto"
        )
        self.assertIsNotNone(usuario)
        self.assertIsNone(
            GestorUsuarios(rutas["usuarios.json"]).iniciar_sesion("estudiante", "incorrecta")
        )


if __name__ == "__main__":
    unittest.main()
