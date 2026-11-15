"""Tarjetas compartidas para feeds y perfiles, con comentarios integrados."""

import os
import re
import shutil
import tkinter as tk
import uuid
import webbrowser
from tkinter import filedialog, messagebox, ttk

from gui.estilo import BLANCO, GRIS, ROJO, TEXTO, aplicar_tema_actual
from gui.avatar import dibujar_avatar
from gui.scroll import enlazar_rueda_descendientes
from gui.imagenes import cargar_vista_previa, validar_imagen
from gui.iconos import crear_icono
from gui.fechas import fecha_publicacion


class ListaPublicaciones(tk.Frame):
    def __init__(self, padre, aplicacion, usuario_actual, abrir_perfil=None):
        super().__init__(padre, background=GRIS)
        self.aplicacion = aplicacion
        self.usuario_actual = usuario_actual
        self.abrir_perfil = abrir_perfil
        self.canvas = tk.Canvas(self, background=GRIS, highlightthickness=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        # La lista mantiene su scrollbar funcional para yview, pero no lo muestra.
        self.tarjetas = tk.Frame(self.canvas, background=GRIS, padx=5, pady=5)
        self.ventana = self.canvas.create_window((0, 0), window=self.tarjetas, anchor="nw")
        self.tarjetas.bind("<Configure>", lambda evento: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda evento: self.canvas.itemconfigure(self.ventana, width=evento.width))
        enlazar_rueda_descendientes(self.canvas, self._rueda)

    def mostrar(self, publicaciones, mensaje="Aún no hay publicaciones."):
        for widget in self.tarjetas.winfo_children():
            widget.destroy()
        if not publicaciones:
            tk.Label(self.tarjetas, text=mensaje, background=GRIS, foreground="#6B7280",
                     font=("Segoe UI", 11), pady=32, wraplength=520).pack(fill="x")
        for publicacion in publicaciones:
            tarjeta = TarjetaPublicacion(self.tarjetas, self.aplicacion, self.usuario_actual,
                                         publicacion, self.abrir_perfil, self._rueda)
            tarjeta.pack(fill="x", padx=5, pady=6)
            enlazar_rueda_descendientes(tarjeta, self._rueda)
        aplicar_tema_actual(self)
        self.canvas.yview_moveto(0)

    def _rueda(self, evento):
        if getattr(evento, "num", None) == 4:
            unidades = -1
        elif getattr(evento, "num", None) == 5:
            unidades = 1
        else:
            unidades = -1 if evento.delta > 0 else 1
        self.canvas.yview_scroll(unidades, "units")
        return "break"


class TarjetaPublicacion(tk.Frame):
    def __init__(self, padre, aplicacion, usuario_actual, publicacion, abrir_perfil=None,
                 al_desplazar=None):
        super().__init__(padre, background=BLANCO, padx=16, pady=14,
                         highlightbackground="#E5E7EB", highlightthickness=1)
        self.aplicacion = aplicacion
        self.usuario_actual = usuario_actual
        self.publicacion = publicacion
        self.abrir_perfil = abrir_perfil
        self.al_desplazar = al_desplazar
        self.expandida = False
        self.responder_abierto = False
        self.imagen_respuesta = None
        self.parent_respuesta = None
        self.conversacion_id = None
        autor = aplicacion.gestor_usuarios.usuarios_por_nombre.get(publicacion.nombre_usuario)
        nombre = "@" + publicacion.nombre_usuario
        avatar = tk.Canvas(self, width=42, height=42, background=BLANCO, highlightthickness=0,
                           cursor="hand2" if autor and abrir_perfil else "")
        avatar.grid(row=0, column=0, rowspan=2, padx=(0, 11))
        if autor:
            carpeta_datos = os.path.dirname(aplicacion.gestor_usuarios.ruta_archivo)
            dibujar_avatar(avatar, autor, carpeta_datos, 42)
        else:
            iniciales = "".join(p[0] for p in nombre.split()[:2]).upper() or "?"
            avatar.create_oval(1, 1, 41, 41, fill="#FCE7EC", outline="")
            avatar.create_text(21, 21, text=iniciales, fill=ROJO, font=("Segoe UI", 11, "bold"))
        texto_autor = nombre
        self.autor = tk.Label(self, text=texto_autor, background=BLANCO, foreground=TEXTO,
                              font=("Segoe UI", 11, "bold"), anchor="w",
                              cursor="hand2" if autor and abrir_perfil else "")
        self.autor.grid(row=0, column=1, sticky="w")
        self.fecha = tk.Label(self, text=fecha_publicacion(publicacion.fecha), background=BLANCO,
                              foreground="#6B7280", font=("Segoe UI", 9), anchor="w")
        self.fecha.grid(row=1, column=1, sticky="w")
        self.menu_publicacion = tk.Menu(self, tearoff=False, background=BLANCO,
                                        foreground=TEXTO, activebackground=ROJO,
                                        activeforeground=BLANCO)
        if usuario_actual.nombre_usuario == publicacion.nombre_usuario:
            self.menu_publicacion.add_command(label="Eliminar publicación", command=self._eliminar)
        self.boton_menu = tk.Button(self, text="...", command=self._abrir_menu,
                                    background=BLANCO, foreground=TEXTO, relief="flat",
                                    borderwidth=0, cursor="hand2", font=("Segoe UI", 12, "bold"))
        self.boton_menu.grid(row=0, column=2, sticky="ne")
        if autor and abrir_perfil:
            for widget in (avatar, self.autor):
                widget.bind("<Button-1>", lambda evento, persona=autor: abrir_perfil(persona))
        self.columnconfigure(1, weight=1)
        self.contenido = tk.Text(self, background=BLANCO, foreground=TEXTO,
                                 font=("Segoe UI", 11), wrap="word", height=1,
                                 relief="flat", borderwidth=0, highlightthickness=0,
                                 padx=0, pady=0, cursor="arrow")
        self.contenido.insert("1.0", publicacion.contenido)
        for numero, coincidencia in enumerate(re.finditer(
                r"https?://[^\s<>()]+|www\.[^\s<>()]+", publicacion.contenido)):
            inicio, fin = coincidencia.span()
            while fin > inicio and publicacion.contenido[fin - 1] in ".,!?;:":
                fin -= 1
            if fin == inicio:
                continue
            etiqueta = "enlace_publicacion_{}".format(numero)
            comienzo_tk = "1.0 + {} chars".format(inicio)
            fin_tk = "1.0 + {} chars".format(fin)
            self.contenido.tag_add(etiqueta, comienzo_tk, fin_tk)
            self.contenido.tag_configure(etiqueta, foreground=ROJO, underline=True)
            url = publicacion.contenido[inicio:fin]
            destino = url if url.lower().startswith(("http://", "https://")) else "https://" + url
            self.contenido.tag_bind(
                etiqueta, "<Button-1>", lambda evento, enlace=destino: webbrowser.open(enlace))
            self.contenido.tag_bind(etiqueta, "<Enter>",
                                    lambda evento: self.contenido.configure(cursor="hand2"))
            self.contenido.tag_bind(etiqueta, "<Leave>",
                                    lambda evento: self.contenido.configure(cursor="arrow"))
        self.contenido.configure(state="disabled")
        self.contenido.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(14, 10))
        self.contenido.bind("<Configure>", self._ajustar_alto_contenido)
        self.imagen = None
        if publicacion.ruta_imagen:
            carpeta_datos = os.path.dirname(aplicacion.gestor_usuarios.ruta_archivo)
            ruta_imagen = (publicacion.ruta_imagen if os.path.isabs(publicacion.ruta_imagen)
                           else os.path.join(carpeta_datos, publicacion.ruta_imagen))
            try:
                self.imagen = cargar_vista_previa(ruta_imagen, 640, 420)
                self.vista_imagen = tk.Label(self, image=self.imagen, background=BLANCO)
                self.vista_imagen.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 12))
            except (tk.TclError, OSError):
                self.imagen = None
                self.aviso_imagen = tk.Label(
                    self, text="No se pudo cargar la imagen de esta publicación.",
                    background=BLANCO, foreground="#B42318", font=("Segoe UI", 10), anchor="w",
                )
                self.aviso_imagen.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 10))
        acciones = tk.Frame(self, background=BLANCO)
        acciones.grid(row=4, column=1, columnspan=2, sticky="e", pady=(6, 0))
        self.boton_comentarios = tk.Button(
            acciones, text=self._texto_boton(), command=self._alternar,
            background=BLANCO, foreground=ROJO, activeforeground=ROJO,
            relief="flat", borderwidth=0, cursor="hand2", font=("Segoe UI", 10, "bold"),
        )
        self.boton_comentarios._campus_icono = "responder"
        self.boton_comentarios._campus_rol = "reaccion"
        self.boton_comentarios.configure(compound="top")
        self.boton_responder = tk.Button(
            self, text="", command=self._abrir_respuesta,
            background=BLANCO, foreground="#6B7280", activebackground="#E5E7EB",
            activeforeground=ROJO, relief="flat", borderwidth=0,
            padx=11, pady=5, cursor="hand2", font=("Segoe UI", 9, "bold"),
        )
        self.boton_responder.configure(compound="top")
        self.boton_responder.grid(row=4, column=0, sticky="w", pady=(6, 0))
        self.boton_responder._campus_icono = "responder"
        self.boton_responder._campus_rol = "reaccion"
        self.botones_reacciones = {}
        self.etiquetas_reacciones = {
            "Me gusta": "Me gusta",
        }
        for reaccion in reversed(tuple(self.etiquetas_reacciones)):
            boton = tk.Button(
                acciones, text="", command=lambda valor=reaccion: self._reaccionar(valor),
                background=BLANCO, foreground="#6B7280", activeforeground=ROJO,
                relief="flat", borderwidth=0, padx=7, cursor="hand2",
                font=("Segoe UI", 9, "bold"),
            )
            boton._campus_icono = "corazon" if reaccion == "Me gusta" else "sonrisa"
            boton._campus_contador_neutro = True
            boton.configure(compound="top")
            boton.pack(side="left", padx=5, pady=5)
            self.botones_reacciones[reaccion] = boton
        self._actualizar_reacciones()
        self._actualizar_boton_respuestas()
        self.comentarios_frame = tk.Frame(self, background=BLANCO)
        self.comentarios_frame.columnconfigure(0, weight=1)
        self.comentarios_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.comentarios_frame.grid_remove()
        self._dibujar_comentarios()

        gestor = self.aplicacion.gestor_publicaciones
        propio_repost = gestor.tiene_repost(publicacion.identificador, usuario_actual.nombre_usuario)
        self.boton_repost = tk.Button(
            acciones, text=str(gestor.contar_reposts(publicacion.identificador)),
            compound="top", padx=9,
            command=self._repostear, background=BLANCO, foreground=ROJO,
            relief="flat", borderwidth=0, cursor="hand2",
            state="disabled" if publicacion.nombre_usuario == usuario_actual.nombre_usuario else "normal")
        self.boton_repost._campus_icono = "repost"
        if publicacion.nombre_usuario != usuario_actual.nombre_usuario:
            self.boton_repost.pack(side="left", padx=5, pady=5)
        self.boton_repost._campus_rol = "reaccion"
        self.boton_repost._campus_seleccionado = propio_repost
        self.boton_repost._campus_contador_neutro = True
        self.boton_compartir = tk.Button(acciones, text="", command=self._compartir,
            background=BLANCO, foreground="#6B7280", relief="flat", borderwidth=0, padx=10, cursor="hand2")
        self.boton_compartir._campus_icono = "enviar"
        self.boton_compartir._campus_rol = "reaccion"
        self.boton_compartir.pack(side="left", padx=5, pady=5)
        reposteador = getattr(publicacion, "reposteador", None)
        if reposteador:
            # Reserva una fila sobre toda la tarjeta sin alterar su contenido.
            for widget in self.grid_slaves():
                widget.grid_configure(row=int(widget.grid_info()["row"]) + 1)
            self.comentarios_frame.grid_configure(row=7)
            self.comentarios_frame.grid_remove()
            etiqueta = tk.Label(self, text="@{} reposteó".format(reposteador),
                                background=BLANCO, foreground="#6B7280", cursor="hand2")
            etiqueta.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
            persona = aplicacion.gestor_usuarios.usuarios_por_nombre.get(reposteador)
            if persona and abrir_perfil:
                etiqueta.bind("<Button-1>", lambda evento: abrir_perfil(persona))

    def _ajustar_alto_contenido(self, evento=None):
        try:
            resultado = self.contenido.count("1.0", "end-1c", "displaylines")
            alto = max(1, int(resultado[0])) if resultado else 1
            if int(self.contenido.cget("height")) != alto:
                self.contenido.configure(height=alto)
        except (tk.TclError, ValueError, TypeError):
            pass

    def _repostear(self):
        gestor = self.aplicacion.gestor_publicaciones
        identificador = self.publicacion.identificador
        usuario = self.usuario_actual.nombre_usuario
        try:
            if gestor.tiene_repost(identificador, usuario):
                gestor.deshacer_repost(identificador, usuario)
            else:
                gestor.repostear(identificador, usuario)
        except (ValueError, PermissionError, OSError) as error:
            messagebox.showerror("Repost", str(error), parent=self)
            return
        self.winfo_toplevel().event_generate("<<PublicacionEliminada>>", when="tail")

    def _compartir(self):
        self.aplicacion.vista_instancia.compartir_publicacion(self.publicacion.identificador)

    def _texto_boton(self):
        cantidad = len(self.publicacion.comentarios)
        return str(cantidad)

    def _abrir_menu(self):
        if self.menu_publicacion.index("end") is None:
            return
        self.menu_publicacion.configure(background=self.cget("background"),
                                        foreground=self.autor.cget("foreground"),
                                        activebackground=ROJO, activeforeground=BLANCO)
        try:
            self.menu_publicacion.tk_popup(self.boton_menu.winfo_rootx(),
                                           self.boton_menu.winfo_rooty() + self.boton_menu.winfo_height())
        finally:
            self.menu_publicacion.grab_release()

    def _eliminar(self):
        if not messagebox.askyesno("Eliminar publicación",
                                  "¿Eliminar esta publicación y sus respuestas y reacciones?",
                                  parent=self):
            return
        try:
            self.aplicacion.gestor_publicaciones.eliminar_publicacion(
                self.publicacion.identificador, self.usuario_actual.nombre_usuario)
        except (ValueError, PermissionError, OSError) as error:
            messagebox.showerror("Eliminar publicación", str(error), parent=self)
            return
        self.winfo_toplevel().event_generate("<<PublicacionEliminada>>", when="tail")

    def _actualizar_reacciones(self):
        activas = self.publicacion.reacciones
        propia = activas.get(self.usuario_actual.nombre_usuario)
        for reaccion, boton in self.botones_reacciones.items():
            cantidad = sum(valor == reaccion for valor in activas.values())
            seleccionado = propia == reaccion
            boton._campus_rol = "reaccion"
            boton._campus_seleccionado = seleccionado
            boton.configure(
                text="  {}".format(cantidad),
                background="#FCE7EC" if seleccionado else BLANCO,
                foreground=ROJO if seleccionado else "#6B7280",
            )
            aplicar_tema_actual(boton)

    def _actualizar_boton_respuestas(self):
        cantidad = len(self.publicacion.comentarios)
        self.boton_comentarios.pack_forget()
        self.boton_responder.configure(text=str(cantidad) if cantidad else "")

    def _reaccionar(self, reaccion):
        try:
            usuario = self.usuario_actual.nombre_usuario
            if self.publicacion.reacciones.get(usuario) == reaccion:
                self.aplicacion.gestor_publicaciones.quitar_reaccion(
                    self.publicacion.identificador, usuario,
                )
            else:
                self.aplicacion.gestor_publicaciones.establecer_reaccion(
                    self.publicacion.identificador, usuario, reaccion,
                )
        except ValueError as error:
            messagebox.showerror("Reacciones", str(error), parent=self)
            return
        except OSError:
            messagebox.showerror("Reacciones", "No se pudo guardar la reacción.", parent=self)
            return
        self._actualizar_reacciones()

    def _alternar(self):
        self.expandida = not self.expandida
        if not self.expandida and self.responder_abierto:
            self.responder_abierto = False
            self.boton_responder.configure(text="")
        self._actualizar_boton_respuestas()
        if self.expandida or self.responder_abierto:
            self.comentarios_frame.grid()
        else:
            self.comentarios_frame.grid_remove()

    def _abrir_respuesta(self):
        self.responder_abierto = not self.responder_abierto
        self.parent_respuesta = None
        self.etiqueta_destinatario.configure(
            text="Respondiendo a @{}".format(self.publicacion.nombre_usuario))
        self.expandida = self.responder_abierto and bool(self.publicacion.comentarios)
        self.boton_responder.configure(text="")
        self._actualizar_boton_respuestas()
        if self.expandida or self.responder_abierto:
            self.comentarios_frame.grid()
        else:
            self.comentarios_frame.grid_remove()
        if self.responder_abierto:
            self.campo_comentario.focus_set()

    def _dibujar_comentarios(self):
        self.imagenes_respuestas = []
        for widget in self.comentarios_frame.winfo_children():
            widget.destroy()
        comentarios = self.publicacion.comentarios
        por_id = {item["id"]: item for item in comentarios}
        hijos = {None: []}
        for comentario in comentarios:
            padre = comentario.get("parent_id")
            if (comentario.get("parent_type") != "respuesta" or padre not in por_id
                    or padre == comentario["id"]):
                padre = None
            hijos.setdefault(padre, []).append(comentario)

        permitidos = None
        if self.conversacion_id in por_id:
            permitidos = {self.conversacion_id}
            cursor = por_id[self.conversacion_id].get("parent_id")
            while (por_id.get(cursor, {}).get("id") is not None
                   and por_id[cursor].get("parent_type") == "respuesta"
                   and cursor not in permitidos):
                permitidos.add(cursor)
                cursor = por_id[cursor].get("parent_id")
            pendientes = [self.conversacion_id]
            while pendientes:
                actual = pendientes.pop()
                for hijo in hijos.get(actual, []):
                    if hijo["id"] not in permitidos:
                        permitidos.add(hijo["id"])
                        pendientes.append(hijo["id"])
            tk.Button(self.comentarios_frame, text="? Todas las respuestas",
                      command=self._cerrar_conversacion, background=BLANCO, foreground=ROJO,
                      relief="flat", borderwidth=0, cursor="hand2").pack(anchor="w", padx=8)
            tk.Label(self.comentarios_frame, text="Conversaci?n", background=BLANCO,
                     foreground=TEXTO, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8)

        def dibujar(comentario, padre_widget, profundidad=0):
            if permitidos is not None and comentario["id"] not in permitidos:
                return
            item = tk.Frame(padre_widget, background=BLANCO)
            item.pack(fill="x", pady=(7, 0))
            fila = tk.Frame(item, background=BLANCO)
            fila.pack(fill="x")
            usuario = self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(comentario["nombre_usuario"])
            if usuario:
                avatar = tk.Canvas(fila, width=28, height=28, background=BLANCO,
                                   highlightthickness=0, cursor="hand2" if self.abrir_perfil else "")
                avatar.pack(side="left", padx=(0, 7))
                dibujar_avatar(avatar, usuario,
                               os.path.dirname(self.aplicacion.gestor_usuarios.ruta_archivo), 28)
                if self.abrir_perfil:
                    avatar.bind("<Button-1>", lambda evento, persona=usuario: self.abrir_perfil(persona))
            autor = tk.Label(
                fila, text="@{}  \u00b7  {}".format(
                    comentario["nombre_usuario"], fecha_publicacion(comentario["fecha"])),
                background=BLANCO, foreground="#6B7280", font=("Segoe UI", 9, "bold"),
                anchor="w", cursor="hand2" if usuario and self.abrir_perfil else "",
            )
            autor.pack(side="left", fill="x", expand=True)
            if usuario and self.abrir_perfil:
                autor.bind("<Button-1>", lambda evento, persona=usuario: self.abrir_perfil(persona))
            if comentario["contenido"]:
                tk.Label(item, text=comentario["contenido"], background=BLANCO,
                         foreground=TEXTO, font=("Segoe UI", 10), anchor="w", justify="left",
                         wraplength=500).pack(fill="x", padx=(35, 0), pady=(1, 0))
            if comentario.get("ruta_imagen"):
                self._dibujar_imagen_respuesta(comentario, item)
            acciones = tk.Frame(item, background=BLANCO)
            acciones.pack(fill="x", padx=(35, 0))
            tk.Button(acciones, text="Responder", command=lambda c=comentario: self._responder_a(c),
                      background=BLANCO, foreground=ROJO, relief="flat", borderwidth=0,
                      cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="left")
            if profundidad >= 2 and self.conversacion_id is None:
                tk.Button(acciones, text="Ver conversaci?n", command=lambda c=comentario: self._ver_conversacion(c),
                          background=BLANCO, foreground="#6B7280", relief="flat", borderwidth=0,
                          cursor="hand2", font=("Segoe UI", 9)).pack(side="left", padx=6)
            descendientes = [h for h in hijos.get(comentario["id"], [])
                             if permitidos is None or h["id"] in permitidos]
            if descendientes and (profundidad < 2 or permitidos is not None):
                grupo = tk.Frame(item, background=BLANCO)
                grupo.pack(fill="x", padx=(14 if profundidad < 4 else 0, 0), pady=(2, 0))
                tk.Frame(grupo, width=2, background="#D1D5DB").pack(side="left", fill="y", padx=(0, 10))
                contenido_hilo = tk.Frame(grupo, background=BLANCO)
                contenido_hilo.pack(side="left", fill="x", expand=True)
                for hijo in descendientes:
                    dibujar(hijo, contenido_hilo, profundidad + 1)

        for raiz in hijos[None]:
            if permitidos is None or raiz["id"] in permitidos:
                dibujar(raiz, self.comentarios_frame)

        destino = "@" + self.publicacion.nombre_usuario
        if self.parent_respuesta is not None:
            parent = por_id.get(self.parent_respuesta)
            if parent:
                destino = "@" + parent["nombre_usuario"]
        self.etiqueta_destinatario = tk.Label(
            self.comentarios_frame, text="Respondiendo a {}".format(destino),
            background=BLANCO, foreground="#6B7280", font=("Segoe UI", 9, "bold"), anchor="w",
        )
        self.etiqueta_destinatario.pack(fill="x", padx=8, pady=(10, 3))
        entrada = tk.Frame(self.comentarios_frame, background=GRIS, padx=7, pady=6)
        entrada.pack(fill="x", pady=(4, 2))
        self.campo_comentario = tk.Entry(entrada, relief="flat", font=("Segoe UI", 10))
        self.campo_comentario.pack(side="left", fill="x", expand=True, padx=(2, 8))
        self.campo_comentario.bind("<Return>", lambda evento: self._comentar())
        self.icono_imagen_respuesta = crear_icono("imagen")
        self.boton_imagen_respuesta = tk.Button(
            entrada, text="▧" if self.icono_imagen_respuesta is None else "",
            image=self.icono_imagen_respuesta, command=self._seleccionar_imagen_respuesta,
            background="#111318", foreground=BLANCO, activebackground="#343943",
            activeforeground=BLANCO, relief="flat", borderwidth=0,
            padx=8, pady=5, cursor="hand2", font=("Segoe UI Symbol", 12),
        )
        self.boton_imagen_respuesta.pack(side="right", padx=(0, 5))
        self.boton_imagen_respuesta._campus_icono = "imagen"
        self.boton_imagen_respuesta._campus_rol = "icono"
        self.icono_enviar_respuesta = crear_icono("enviar")
        self.boton_enviar_respuesta = tk.Button(
            entrada, text="➤" if self.icono_enviar_respuesta is None else "",
            image=self.icono_enviar_respuesta, command=self._comentar,
            background="#111318", foreground=BLANCO, activebackground="#343943",
            activeforeground=BLANCO, relief="flat", borderwidth=0,
            padx=8, pady=5, cursor="hand2", font=("Segoe UI Symbol", 12),
        )
        self.boton_enviar_respuesta.pack(side="right")
        self.boton_enviar_respuesta._campus_icono = "enviar"
        self.boton_enviar_respuesta._campus_rol = "icono"
        self.preview_respuesta_frame = tk.Frame(self.comentarios_frame, background=BLANCO)
        self.preview_respuesta_frame.pack(fill="x", padx=8, pady=(4, 0))
        self.preview_respuesta_frame.pack_forget()
        self.preview_respuesta = None
        if self.imagen_respuesta:
            self._mostrar_vista_previa_respuesta()
        if self.al_desplazar:
            enlazar_rueda_descendientes(self.comentarios_frame, self.al_desplazar)
        aplicar_tema_actual(self.comentarios_frame)

    def _responder_a(self, comentario):
        self.parent_respuesta = comentario["id"]
        self.responder_abierto = True
        self.boton_responder.configure(text="")
        self.etiqueta_destinatario.configure(text="Respondiendo a @{}".format(comentario["nombre_usuario"]))
        self.expandida = True
        self._actualizar_boton_respuestas()
        self.comentarios_frame.grid()
        self.campo_comentario.focus_set()

    def _ver_conversacion(self, comentario):
        self.conversacion_id = comentario["id"]
        self._dibujar_comentarios()

    def _cerrar_conversacion(self):
        self.conversacion_id = None
        self._dibujar_comentarios()

    def _dibujar_imagen_respuesta(self, respuesta, padre):
        ruta = respuesta["ruta_imagen"]
        if not os.path.isabs(ruta):
            ruta = os.path.join(os.path.dirname(self.aplicacion.gestor_usuarios.ruta_archivo), ruta)
        try:
            imagen = cargar_vista_previa(ruta, 520, 340)
            self.imagenes_respuestas.append(imagen)
            tk.Label(padre, image=imagen, background=BLANCO).pack(
                anchor="w", padx=(35, 0), pady=(3, 5))
        except (tk.TclError, OSError, ValueError):
            tk.Label(padre, text="No se pudo cargar la imagen de esta respuesta.",
                     background=BLANCO, foreground="#B42318", font=("Segoe UI", 9),
                     anchor="w").pack(fill="x", padx=(35, 0), pady=(3, 5))

    def _seleccionar_imagen_respuesta(self):
        ruta = filedialog.askopenfilename(
            parent=self, filetypes=[("Im?genes", "*.jpg *.jpeg *.png *.webp *.gif")],
        )
        if not ruta:
            return
        try:
            validar_imagen(ruta)
        except (OSError, ValueError) as error:
            messagebox.showerror("Imagen de respuesta", str(error), parent=self)
            return
        self.imagen_respuesta = ruta
        self._mostrar_vista_previa_respuesta()

    def _mostrar_vista_previa_respuesta(self):
        for widget in self.preview_respuesta_frame.winfo_children():
            widget.destroy()
        self.preview_respuesta_frame.pack(fill="x", padx=8, pady=(4, 0))
        barra = tk.Frame(self.preview_respuesta_frame, background=BLANCO)
        barra.pack(fill="x")
        tk.Label(barra, text=os.path.basename(self.imagen_respuesta), background=BLANCO,
                 foreground="#6B7280", anchor="w").pack(side="left", fill="x", expand=True)
        tk.Button(barra, text="Cambiar", command=self._seleccionar_imagen_respuesta,
                  background="#E5E7EB", foreground=TEXTO, relief="flat", borderwidth=0,
                  padx=8, pady=4, cursor="hand2").pack(side="right", padx=(4, 0))
        tk.Button(barra, text="Quitar", command=self._quitar_imagen_respuesta,
                  background="#E5E7EB", foreground=TEXTO, relief="flat", borderwidth=0,
                  padx=8, pady=4, cursor="hand2").pack(side="right")
        try:
            self.preview_respuesta = cargar_vista_previa(self.imagen_respuesta, 520, 360)
            tk.Label(self.preview_respuesta_frame, image=self.preview_respuesta,
                     background=BLANCO).pack(anchor="w", pady=4)
        except (OSError, tk.TclError, ValueError) as error:
            tk.Label(self.preview_respuesta_frame, text="No se pudo mostrar la imagen: {}".format(error),
                     background=BLANCO, foreground="#B42318", anchor="w").pack(fill="x")

    def _quitar_imagen_respuesta(self):
        self.imagen_respuesta = None
        self.preview_respuesta = None
        self.preview_respuesta_frame.pack_forget()

    def _comentar(self):
        archivo_copiado = None
        ruta_guardada = ""
        try:
            if self.imagen_respuesta:
                extension = os.path.splitext(self.imagen_respuesta)[1].lower()
                carpeta = os.path.join(os.path.dirname(self.aplicacion.gestor_publicaciones.ruta_archivo),
                                       "imagenes_respuestas")
                os.makedirs(carpeta, exist_ok=True)
                nombre = uuid.uuid4().hex + extension
                archivo_copiado = os.path.join(carpeta, nombre)
                shutil.copyfile(self.imagen_respuesta, archivo_copiado)
                ruta_guardada = "imagenes_respuestas/" + nombre
            self.aplicacion.gestor_publicaciones.agregar_comentario(
                self.publicacion.identificador, self.usuario_actual.nombre_usuario,
                self.campo_comentario.get(), ruta_guardada, self.parent_respuesta,
            )
        except ValueError as error:
            self._eliminar_archivo(archivo_copiado)
            messagebox.showerror("Respuestas", str(error), parent=self)
            return
        except OSError:
            self._eliminar_archivo(archivo_copiado)
            messagebox.showerror("Respuestas", "No se pudo guardar la respuesta.", parent=self)
            return
        self.imagen_respuesta = None
        self.parent_respuesta = None
        self.conversacion_id = None
        self.expandida = True
        self.responder_abierto = False
        self.boton_responder.configure(text="")
        self._actualizar_boton_respuestas()
        self._dibujar_comentarios()
        self.comentarios_frame.grid()

    @staticmethod
    def _eliminar_archivo(ruta):
        if ruta and os.path.exists(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass
