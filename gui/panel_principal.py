"""Panel principal de la cuenta autenticada."""

import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from gui.ventana_muro import VentanaMuro
from gui.estilo import estructura, decorar, encabezado, aplicar_tema_actual, crear_campo_redondeado
from gui.lista_amigos import ListaAmigos
from gui.perfil import Perfil
from gui.avatar import dibujar_avatar
from gui.scroll import enlazar_rueda_descendientes
from gui.mensajes import Mensajes
from gestores.gestor_mensajes import GestorMensajes


class PanelPrincipal:
    """Presenta un saludo y permite cerrar la sesión."""

    def __init__(self, contenedor, aplicacion, usuario):
        """Construye una vista inicial sencilla para una cuenta autenticada."""
        self.aplicacion = aplicacion
        self.usuario = usuario
        self.resultados = []
        self.historial_perfiles = []
        lateral, central = estructura(contenedor)
        self.secciones = {nombre: tk.Frame(central, background="#FFFFFF")
                          for nombre in ("Buscar usuarios", "Amigos", "muro", "Mi perfil", "Mensajes")}
        datos = os.path.dirname(aplicacion.gestor_usuarios.ruta_archivo)
        self.gestor_mensajes = GestorMensajes(os.path.join(datos, "privado", "mensajes.json"),
            aplicacion.gestor_usuarios, aplicacion.gestor_amistades,
            lambda: usuario if getattr(aplicacion, "usuario_actual", usuario) is usuario else None)
        aplicacion.auditoria.conectar(self.gestor_mensajes)
        self.mensajes = Mensajes(self.secciones["Mensajes"], self.gestor_mensajes, datos, self._contar_mensajes)
        self.mensajes.pack(fill="both", expand=True)
        self.mensajes.publicaciones = aplicacion.gestor_publicaciones
        self.mensajes.aplicacion = aplicacion
        self.mensajes.abrir_perfil = self.abrir_perfil
        self.muro = VentanaMuro(self.secciones["muro"], aplicacion, usuario)
        self.perfil = Perfil(self.secciones["Mi perfil"], aplicacion, usuario,
                             self.abrir_perfil, self.volver_perfil, self._actualizar_vistas_perfil)
        self.perfil.pack(fill="both", expand=True)
        self.perfil.abrir_chat = self.abrir_chat
        self.muro.abrir_perfil = self.abrir_perfil
        self.muro.al_actualizar_vistas = self._actualizar_perfil_visible
        self.perfil.winfo_toplevel().bind("<<PublicacionEliminada>>", self._publicacion_eliminada)
        contenedor = self.secciones["Buscar usuarios"]
        tk.Label(contenedor, text="Encuentra tu comunidad", background="#FFFFFF",
                 foreground="#1F2937", font=("Segoe UI", 23, "bold")).pack(anchor="w", pady=(12, 4))
        tk.Label(contenedor, text="Busca estudiantes por nombre o @usuario.", background="#FFFFFF",
                 foreground="#6B7280", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 16))
        barra_busqueda = tk.Frame(contenedor, background="#F3F4F6", padx=10, pady=6)
        barra_busqueda.pack(fill="x", pady=(0, 12))
        self.marco_busqueda_usuarios, self.campo_busqueda = crear_campo_redondeado(
            barra_busqueda, tk.Entry, relief="flat", background="#F3F4F6",
            foreground="#1F2937", font=("Segoe UI", 12))
        self.marco_busqueda_usuarios.pack(side="left", fill="x", expand=True, padx=4)
        self.campo_busqueda.bind("<KeyRelease>", lambda evento: self._buscar())
        for evento in ("<<Paste>>", "<<Cut>>"):
            self.campo_busqueda.bind(evento, lambda evento: self.campo_busqueda.after_idle(self._buscar))
        tk.Button(barra_busqueda, text="Buscar", command=self._buscar, background="#E4002B",
                  foreground="#FFFFFF", activebackground="#B80023", activeforeground="#FFFFFF",
                  relief="flat", borderwidth=0, padx=16, pady=7, cursor="hand2",
                  font=("Segoe UI", 10, "bold")).pack(side="right", padx=(8, 0))
        resumen = tk.Frame(contenedor, background="#FFFFFF")
        resumen.pack(fill="x", pady=(2, 8))
        self.estado_busqueda = tk.Label(resumen, text="Escribe un nombre o usuario para comenzar.",
                                        anchor="w", background="#FFFFFF", foreground="#6B7280")
        self.estado_busqueda.pack(side="left", fill="x", expand=True)
        self.contador_amigos = tk.Label(resumen, text="0 amigos", background="#FCE7EC",
                                        foreground="#E4002B", font=("Segoe UI", 10, "bold"), padx=10, pady=4)
        self.contador_amigos.pack(side="right")
        lista = tk.Frame(contenedor, background="#F3F4F6", padx=8, pady=8)
        lista.pack(fill="both", expand=True)
        self.canvas_resultados = tk.Canvas(lista, background="#F3F4F6", highlightthickness=0)
        self.scroll_resultados = ttk.Scrollbar(lista, orient="vertical", command=self.canvas_resultados.yview)
        self.canvas_resultados.configure(yscrollcommand=self.scroll_resultados.set)
        self.canvas_resultados.pack(side="left", fill="both", expand=True)
        self.lista_resultados = tk.Frame(self.canvas_resultados, background="#F3F4F6")
        self.ventana_resultados = self.canvas_resultados.create_window((0, 0), window=self.lista_resultados, anchor="nw")
        self.lista_resultados.bind("<Configure>", lambda evento: self.canvas_resultados.configure(
            scrollregion=self.canvas_resultados.bbox("all")))
        self.canvas_resultados.bind("<Configure>", lambda evento: self.canvas_resultados.itemconfigure(
            self.ventana_resultados, width=evento.width))
        self.resultado_vacio = tk.Label(self.lista_resultados, text="", background="#F3F4F6",
                                        foreground="#6B7280", font=("Segoe UI", 11), pady=36)
        self.resultado_vacio.pack(fill="x")
        self.tarjetas_resultados = {}
        self._enlazar_scroll_busqueda(self.canvas_resultados)
        contenedor = self.secciones["Amigos"]
        self.lista_amigos = ListaAmigos(
            contenedor, self._abrir_usuario,
            lambda nombre: self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(nombre),
            os.path.dirname(self.aplicacion.gestor_usuarios.ruta_archivo),
        )
        self.lista_amigos.pack(fill="both", expand=True)
        self.lista_amigos.abrir_chat = self.abrir_chat
        self._actualizar_amigos()
        self.botones_navegacion = {}
        self.seccion_activa = None
        for nombre in ("Inicio", "Buscar usuarios", "Amigos", "Mi muro", "Mi perfil", "Mensajes"):
            boton = tk.Button(lateral, text=nombre, anchor="w",
                              command=lambda seccion=nombre: self._mostrar_seccion(seccion))
            boton.pack(fill="x", pady=4)
            self.botones_navegacion[nombre] = boton
        tk.Button(lateral, text="Cerrar sesión",
                  command=lambda: aplicacion.mostrar_vista("inicio")).pack(side="bottom", fill="x", pady=10)
        decorar(self.secciones["Buscar usuarios"])
        decorar(lateral)
        encabezado(self.secciones["Buscar usuarios"], "Encuentra tu comunidad")
        for nombre, boton in self.botones_navegacion.items():
            boton.bind("<Enter>", lambda evento: evento.widget.configure(background="#B80023", foreground="#FFFFFF"))
            boton.bind("<Leave>", lambda evento, seccion=nombre: self._resaltar_navegacion())
        self._mostrar_seccion("Inicio")
        try:
            self._contar_mensajes(sum(c["no_leidos"] for c in self.gestor_mensajes.conversaciones()))
        except (OSError, ValueError, PermissionError):
            self.botones_navegacion["Mensajes"].configure(text="Mensajes (!)")

    def _contar_mensajes(self, cantidad):
        self.botones_navegacion["Mensajes"].configure(text="Mensajes ({})".format(cantidad))

    def abrir_chat(self, nombre_usuario):
        if self.mensajes.abrir(nombre_usuario):
            self._mostrar_seccion("Mensajes")

    def compartir_publicacion(self, identificador):
        self._mostrar_seccion("Mensajes")
        self.mensajes.elegir_destinatarios(identificador)

    def _resaltar_navegacion(self):
        for nombre, boton in self.botones_navegacion.items():
            activo = nombre == self.seccion_activa
            boton._campus_rol = "navegacion"
            boton._campus_seleccionado = activo
            boton.configure(background="#FFFFFF" if activo else "#E4002B",
                            foreground="#E4002B" if activo else "#FFFFFF")
            aplicar_tema_actual(boton)

    def _mostrar_seccion(self, nombre, conservar_historial=False):
        if not conservar_historial:
            self.historial_perfiles.clear()
        for seccion in self.secciones.values():
            seccion.pack_forget()
        self.seccion_activa = nombre
        if nombre in ("Inicio", "Mi muro"):
            self.secciones["muro"].pack(fill="both", expand=True)
            self.muro.mostrar_feed(propias=nombre == "Mi muro", inicio=nombre == "Inicio")
        elif nombre == "Mensajes":
            self.secciones[nombre].pack(fill="both", expand=True)
            self.mensajes.recargar()
        elif nombre == "Mi perfil":
            self.secciones[nombre].pack(fill="both", expand=True)
            if not conservar_historial:
                self.perfil.mostrar(self.usuario)
        else:
            self.secciones[nombre].pack(fill="both", expand=True)
            if nombre == "Amigos":
                self._actualizar_amigos()
            else:
                self._buscar()
                self.campo_busqueda.focus_set()
        self._resaltar_navegacion()

        self.aplicacion.auditoria.registrar("mostrar_seccion", seccion=nombre)

    def _buscar(self):
        consulta = self.campo_busqueda.get()
        self.resultados = self.aplicacion.gestor_usuarios.buscar_usuarios(consulta)
        amigos = self.aplicacion.gestor_amistades.obtener_amistades(self.usuario.nombre_usuario)
        self.contador_amigos.configure(text="{} amigo{}".format(len(amigos), "s" if len(amigos) != 1 else ""))
        for widget in self.lista_resultados.winfo_children():
            if widget is not self.resultado_vacio:
                widget.destroy()
        self.tarjetas_resultados.clear()
        for usuario in self.resultados:
            self._crear_tarjeta_resultado(usuario, amigos)
        if not consulta.strip():
            texto = "Escribe un nombre o usuario para comenzar."
            mensaje_vacio = "Busca por nombre o @usuario y encuentra a tus compañeros."
        elif not self.resultados:
            texto = "Sin resultados para «{}».".format(consulta.strip())
            mensaje_vacio = "No encontramos coincidencias. Prueba con otro nombre o usuario."
        else:
            texto = "{} resultado{}".format(len(self.resultados), "s" if len(self.resultados) != 1 else "")
            mensaje_vacio = ""
        self.estado_busqueda.configure(text=texto)
        self.resultado_vacio.configure(text=mensaje_vacio)
        if mensaje_vacio:
            self.resultado_vacio.pack(fill="x")
        else:
            self.resultado_vacio.pack_forget()
        aplicar_tema_actual(self.secciones["Buscar usuarios"])
        self.canvas_resultados.yview_moveto(0)

    def _crear_tarjeta_resultado(self, usuario, amigos):
        fila = tk.Frame(self.lista_resultados, background="#FFFFFF", padx=14, pady=12,
                        highlightbackground="#E5E7EB", highlightthickness=1)
        fila.pack(fill="x", padx=3, pady=5)
        avatar = tk.Canvas(fila, width=50, height=50, background="#FFFFFF", highlightthickness=0,
                           cursor="hand2")
        avatar.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        datos = os.path.dirname(self.aplicacion.gestor_usuarios.ruta_archivo)
        dibujar_avatar(avatar, usuario, datos, 50)
        handle = tk.Label(fila, text="@" + usuario.nombre_usuario, background="#FFFFFF",
                          foreground="#1F2937", font=("Segoe UI", 12, "bold"),
                          anchor="w", cursor="hand2")
        handle.grid(row=0, column=1, rowspan=2, sticky="ew")
        fila.columnconfigure(1, weight=1)
        for widget in (avatar, handle):
            widget.bind("<Button-1>", lambda evento, persona=usuario: self.abrir_perfil(persona))
        es_mismo = usuario.nombre_usuario == self.usuario.nombre_usuario
        es_amigo = usuario.nombre_usuario in amigos
        if es_mismo or es_amigo:
            estado = "Tú" if es_mismo else "✓ Amigos"
            tk.Label(fila, text=estado, background="#FFFFFF", foreground="#6B7280",
                     font=("Segoe UI", 10, "bold"), padx=10).grid(row=0, column=2, rowspan=2, padx=(8, 0))
        else:
            solicitud = self.aplicacion.gestor_amistades.estado_solicitud(
                self.usuario.nombre_usuario, usuario.nombre_usuario)
            boton = tk.Button(fila, text="Solicitud enviada" if solicitud == "enviada" else
                              "Aceptar solicitud" if solicitud == "recibida" else "Enviar solicitud",
                              state="disabled" if solicitud == "enviada" else "normal",
                              command=lambda persona=usuario: self._agregar_usuario(persona),
                              background="#E4002B", foreground="#FFFFFF", activebackground="#B80023",
                              activeforeground="#FFFFFF", disabledforeground="#FFFFFF", relief="flat",
                              borderwidth=0, padx=13, pady=7, cursor="hand2", font=("Segoe UI", 9, "bold"))
            boton.grid(row=0, column=2, rowspan=2, padx=(8, 0))
            boton.bind("<Enter>", lambda evento: evento.widget.configure(background="#B80023"))
            boton.bind("<Leave>", lambda evento: evento.widget.configure(background="#E4002B"))
            self.tarjetas_resultados[usuario.nombre_usuario] = boton
        enlazar_rueda_descendientes(fila, self._rueda_busqueda)

    def _agregar_usuario(self, amigo):
        try:
            gestor = self.aplicacion.gestor_amistades
            accion = (gestor.aceptar_solicitud if gestor.estado_solicitud(
                self.usuario.nombre_usuario, amigo.nombre_usuario) == "recibida" else gestor.agregar_amistad)
            accion(self.usuario.nombre_usuario, amigo.nombre_usuario)
        except ValueError as error:
            messagebox.showerror("Amistades", str(error), parent=self.secciones["Buscar usuarios"])
            return
        except OSError:
            messagebox.showerror("Amistades", "No se pudo guardar la amistad. Inténtalo de nuevo.",
                                 parent=self.secciones["Buscar usuarios"])
            return
        self._actualizar_amigos()
        self._buscar()
        self.muro._actualizar()
        self.estado_busqueda.configure(text="Ahora son amigos." if amigo.nombre_usuario in
            gestor.obtener_amistades(self.usuario.nombre_usuario) else "Solicitud enviada a @{}.".format(amigo.nombre_usuario))

    def _enlazar_scroll_busqueda(self, widget):
        widget.bind("<MouseWheel>", self._rueda_busqueda)
        widget.bind("<Button-4>", lambda evento: self.canvas_resultados.yview_scroll(-1, "units"))
        widget.bind("<Button-5>", lambda evento: self.canvas_resultados.yview_scroll(1, "units"))

    def _rueda_busqueda(self, evento):
        if getattr(evento, "num", None) == 4:
            unidades = -1
        elif getattr(evento, "num", None) == 5:
            unidades = 1
        else:
            unidades = -1 if evento.delta > 0 else 1
        self.canvas_resultados.yview_scroll(unidades, "units")
        return "break"

    def _actualizar_seleccion(self, evento=None):
        self._buscar()

    def _agregar_amigo(self):
        self._buscar()

    def _ver_perfil(self):
        if self.resultados:
            self.abrir_perfil(self.resultados[0])

    def _abrir_usuario(self, nombre_usuario):
        usuario = self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(nombre_usuario)
        if usuario:
            self.abrir_perfil(usuario)

    def abrir_perfil(self, usuario):
        self.aplicacion.auditoria.registrar("abrir_perfil", perfil=usuario.nombre_usuario)
        self.historial_perfiles.append((
            self.seccion_activa or "Inicio",
            self.perfil.usuario if self.seccion_activa == "Mi perfil" else None,
        ))
        self.perfil.mostrar(usuario)
        self._mostrar_seccion("Mi perfil", conservar_historial=True)

    def volver_perfil(self):
        seccion, usuario = self.historial_perfiles.pop() if self.historial_perfiles else ("Inicio", None)
        if seccion == "Mi perfil":
            self.perfil.mostrar(usuario or self.usuario)
        self._mostrar_seccion(seccion, conservar_historial=True)

    def _actualizar_amigos(self):
        amigos = self.aplicacion.gestor_amistades.obtener_amistades(self.usuario.nombre_usuario)
        tarjetas = []
        for nombre_usuario in amigos:
            amigo = self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(nombre_usuario)
            tarjetas.append((amigo.nombre_visible if amigo else nombre_usuario, nombre_usuario))
        pendientes = [r["emisor"] for r in self.aplicacion.gestor_amistades.solicitudes
                      if r["receptor"] == self.usuario.nombre_usuario]
        self.lista_amigos.mostrar(tarjetas, pendientes, self._responder_solicitud)

    def _responder_solicitud(self, emisor, aceptar):
        gestor = self.aplicacion.gestor_amistades
        try:
            accion = gestor.aceptar_solicitud if aceptar else gestor.rechazar_solicitud
            accion(self.usuario.nombre_usuario, emisor)
        except (ValueError, OSError) as error:
            messagebox.showerror("Solicitudes de amistad", str(error), parent=self.lista_amigos)
            return
        self._actualizar_vistas_perfil()
        self._actualizar_perfil_visible()

    def _actualizar_perfil_visible(self):
        usuario = self.perfil.usuario
        self.perfil.mostrar(usuario)

    def _actualizar_vistas_perfil(self):
        self._buscar()
        self._actualizar_amigos()
        self.muro._actualizar()

    def _publicacion_eliminada(self, evento=None):
        if self.perfil.winfo_exists():
            self.muro._actualizar()
            self._actualizar_perfil_visible()
