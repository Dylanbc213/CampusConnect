import os
import shutil
import tkinter as tk
import uuid
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from gui.estilo import decorar
from gui.lista_publicaciones import ListaPublicaciones
from gui.avatar import dibujar_avatar
from gui.fechas import fecha_publicacion
from gui.imagenes import validar_imagen, cargar_vista_previa
from gui.videos import validar_video, EXTENSIONES_VIDEO
from gui.reproductor_video import ReproductorVideo


class VentanaMuro:
    def __init__(self, contenedor, aplicacion, usuario):
        self.aplicacion = aplicacion
        self.usuario = usuario
        self.ventana = contenedor
        self.imagen_seleccionada = None
        contenido = contenedor
        self.barra_feed = None
        self.boton_agregar = None
        if contenido is not None:
            self.barra_feed = tk.Frame(contenido, background="#FFFFFF")
            self.barra_feed.pack(fill="x", padx=10, pady=(0, 6))
            self.boton_agregar = tk.Button(
                self.barra_feed, text="+ Agregar publicación", command=self._abrir_compositor,
                background="#E4002B", foreground="#FFFFFF", activebackground="#B80023",
                activeforeground="#FFFFFF", relief="flat", borderwidth=0, padx=14, pady=8,
                cursor="hand2", font=("Segoe UI", 10, "bold"),
            )
            self.boton_agregar.pack(side="left")
            self.boton_actualizar = tk.Button(
                self.barra_feed, text="⟳", command=self._actualizar_desde_json,
                background=self.barra_feed.cget("background"), foreground="#1F2937", activebackground="#E5E7EB",
                activeforeground="#FFFFFF", relief="flat", borderwidth=0, padx=6, pady=3,
                width=2, height=1, cursor="hand2", font=("Segoe UI Symbol", 14, "bold"),
            )
            self.boton_actualizar._campus_rol = "actualizar"
            self.boton_actualizar.pack(side="left", padx=(8, 0))
        if contenido is not None:
            self.compositor = tk.Frame(contenido, background="#FFFFFF", padx=16, pady=12,
                                       highlightbackground="#E5E7EB", highlightthickness=1)
            self.compositor.pack(fill="x", padx=10, pady=(4, 0))
            formulario = self.compositor
            identidad = tk.Frame(formulario, background="#FFFFFF")
            identidad.pack(fill="x", pady=(0, 8))
            avatar = tk.Canvas(identidad, width=42, height=42, background="#FFFFFF", highlightthickness=0)
            avatar.pack(side="left", padx=(0, 10))
            self.avatar_publicador = avatar
            dibujar_avatar(avatar, usuario, os.path.dirname(aplicacion.gestor_usuarios.ruta_archivo), 42)
            self.nombre_publicador = tk.Label(
                identidad, text="{}  (@{})".format(usuario.nombre_visible, usuario.nombre_usuario),
                background="#FFFFFF", foreground="#1F2937", font=("Segoe UI", 11, "bold"),
            )
            self.nombre_publicador.pack(side="left")
        else:
            self.compositor = None
            formulario = contenido
        tk.Label(formulario, text="¿Qué estás pensando?", anchor="w").pack(fill="x", padx=2, pady=(4, 5))
        self.campo_contenido = ScrolledText(formulario, height=3, width=30, wrap="word")
        self.campo_contenido._campus_rol = "texto_publicacion"
        self.campo_contenido.vbar.pack_forget()
        self.campo_contenido.pack(fill="x", padx=2, pady=(0, 7))
        self.preview_frame = None
        self.preview_canvas = None
        if formulario is not None:
            self.preview_frame = tk.Frame(formulario, background="#FFFFFF")
            barra_preview = tk.Frame(self.preview_frame, background="#FFFFFF")
            barra_preview.pack(fill="x", pady=(0, 5))
            self.estado_imagen = tk.Label(barra_preview, text="", background="#FFFFFF",
                                          foreground="#6B7280", anchor="w")
            self.nombre_imagen_preview = self.estado_imagen
            self.estado_imagen.pack(side="left", fill="x", expand=True)
            tk.Button(barra_preview, text="Cambiar", command=self._seleccionar_imagen,
                      background="#E5E7EB", foreground="#1F2937", relief="flat",
                      borderwidth=0, padx=9, pady=5, cursor="hand2").pack(side="right", padx=(5, 0))
            tk.Button(barra_preview, text="Quitar", command=self._quitar_imagen,
                      background="#E5E7EB", foreground="#1F2937", relief="flat",
                      borderwidth=0, padx=9, pady=5, cursor="hand2").pack(side="right")
            self.error_preview = tk.Label(self.preview_frame, text="", background="#FFFFFF",
                                          foreground="#B42318", anchor="w")
            self.error_preview.pack(fill="x")
            self.preview_canvas = tk.Canvas(self.preview_frame, background="#F3F4F6",
                                            highlightthickness=0, height=1)
            self.preview_imagen = None
            self.preview_item = None
            self._ancho_preview = 0
            self.preview_canvas.pack(fill="x")
            self.preview_canvas.bind("<Configure>", self._ajustar_preview)
            self.preview_canvas.bind("<MouseWheel>", self._rueda_preview)
            self.preview_canvas.bind("<Button-4>", lambda evento: self._rueda_preview(evento, -1))
            self.preview_canvas.bind("<Button-5>", lambda evento: self._rueda_preview(evento, 1))
            self.preview_frame.pack_forget()
        fila_acciones = tk.Frame(formulario, background="#FFFFFF") if formulario is not None else formulario
        if fila_acciones is not None:
            fila_acciones.pack(fill="x", padx=2, pady=(0, 3))
            padre_acciones = fila_acciones
        else:
            padre_acciones = formulario
        self.contador = tk.Label(padre_acciones, text="0 / 500 caracteres", anchor="w")
        self.contador.pack(side="left", padx=(0, 8))
        self.boton_imagen = tk.Button(padre_acciones, text="A\u00f1adir foto/video", command=self._seleccionar_imagen)
        self.boton_imagen.pack(side="left", padx=(0, 6))
        self.estado_imagen = tk.Label(padre_acciones, text="", anchor="w", foreground="#6B7280")
        self.estado_imagen.pack(side="left", fill="x", expand=True)
        self.boton_publicar = tk.Button(
            padre_acciones, text="Publicar", command=self._publicar, state="disabled",
            background="#E4002B", foreground="#FFFFFF", activebackground="#B80023",
            activeforeground="#FFFFFF", relief="flat", borderwidth=0, highlightthickness=0,
            padx=12, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold"),
        )
        self.boton_publicar._campus_rol = "publicar"
        self.boton_publicar.pack(side="right")
        self.boton_cancelar = tk.Button(
            padre_acciones, text="Cancelar", command=self._cancelar_compositor,
            background="#E5E7EB", foreground="#1F2937", relief="flat", borderwidth=0,
            padx=14, pady=8, cursor="hand2", font=("Segoe UI", 10, "bold"),
        )
        self.boton_cancelar.pack(side="right", padx=(0, 6))
        if contenido is None:
            self.boton_actualizar = tk.Button(padre_acciones, text="Actualizar", command=self._actualizar_desde_json)
        self.confirmacion = tk.Label(formulario, text="", fg="#24663b", anchor="w")
        self.confirmacion.pack(fill="x", padx=2)
        self.campo_contenido.bind("<<Modified>>", self._contenido_modificado)
        self.campo_contenido.bind("<Return>", self._enter_publicar)
        self.campo_contenido.bind("<KP_Enter>", self._enter_publicar)
        self.campo_contenido.bind("<Shift-Return>", self._enter_salto_linea)
        self.campo_contenido.bind("<Shift-KP_Enter>", self._enter_salto_linea)
        self.titulo_feed = tk.Label(contenido, text="Mi muro", anchor="w")
        self.titulo_feed.pack(fill="x", padx=12, pady=(5, 4))
        self.muro_personal = ScrolledText(contenido, height=6, width=30, wrap="word", state="disabled")
        self.muro_personal.pack(fill="both", expand=True, padx=10, pady=4)
        self.muro_amigos = ScrolledText(contenido, height=6, width=30, wrap="word", state="disabled")
        for muro in (self.muro_personal, self.muro_amigos):
            muro.configure(padx=12, pady=10, background="#FFFFFF")
            muro.tag_configure("tarjeta", background="#F3F4F6", relief="solid", borderwidth=1,
                               lmargin1=8, lmargin2=8, rmargin=8, spacing1=6, spacing3=6)
            muro.tag_configure("autor", font=("Segoe UI", 11, "bold"), foreground="#1F2937")
            muro.tag_configure("fecha", font=("Segoe UI", 9), foreground="#555555")
            muro.tag_configure("contenido", font=("Segoe UI", 11))
        if contenido is not None:
            decorar(contenido)
            self.compositor.pack_forget()
            self.boton_cancelar.configure(background="#E5E7EB", foreground="#1F2937",
                                          activebackground="#D1D5DB", activeforeground="#1F2937")
            self.boton_actualizar.configure(background=self.barra_feed.cget("background"), foreground="#1F2937",
                                            activebackground="#E5E7EB", activeforeground="#1F2937")
        self.campo_contenido.configure(font=("Segoe UI", 12), background="#F3F4F6", foreground="#000000",
                                      insertbackground="#1F2937", relief="solid", borderwidth=1,
                                      highlightthickness=1, highlightbackground="#9CA3AF",
                                      highlightcolor="#E4002B", padx=16, pady=14)
        self.lista_inicio = None
        self.lista_personal = None
        if contenido is not None:
            self.muro_personal.pack_forget()
            self.muro_amigos.pack_forget()
            self.lista_inicio = ListaPublicaciones(contenido, aplicacion, usuario, getattr(self, "abrir_perfil", None))
            self.lista_personal = ListaPublicaciones(contenido, aplicacion, usuario, getattr(self, "abrir_perfil", None))
            self.modo_feed = "inicio"
        self._actualizar()

    def _ocultar_compositor(self):
        if self.compositor is None:
            return
        self.compositor.pack_forget()
        self.boton_agregar.pack(side="left", before=self.boton_actualizar)

    def mostrar_feed(self, propias=True, inicio=False):
        self.modo_feed = "inicio" if inicio else ("propias" if propias else "amigos")
        self.muro_personal.pack_forget()
        self.muro_amigos.pack_forget()
        self.titulo_feed.configure(text="Inicio" if inicio else ("Mi muro" if propias else "Publicaciones de amigos"),
                                   font=("Segoe UI", 14, "bold"))
        if self.lista_inicio is not None:
            self.lista_inicio.pack_forget()
            self.lista_personal.pack_forget()
            lista = self.lista_inicio if inicio else self.lista_personal if propias else self.lista_inicio
            lista.pack(fill="both", expand=True, padx=10, pady=4)
        else:
            muro = self.muro_personal if propias else self.muro_amigos
            muro.pack(fill="both", expand=True, padx=10, pady=4)
        self._actualizar()
        if self.compositor is not None:
            self._ocultar_compositor()

    def _abrir_compositor(self):
        if self.compositor is None:
            return
        self.boton_agregar.pack_forget()
        self.compositor.pack(fill="x", padx=10, pady=(0, 6), before=self.titulo_feed)

    def _cancelar_compositor(self):
        if self.compositor is None:
            return
        self.campo_contenido.delete("1.0", tk.END)
        self._quitar_imagen(actualizar=False)
        self.confirmacion.configure(text="")
        self._actualizar_formulario()
        self._ocultar_compositor()

    def _contenido_modificado(self, evento=None):
        if not self.campo_contenido.edit_modified():
            return
        self.campo_contenido.edit_modified(False)
        self._actualizar_formulario()

    def _enter_publicar(self, evento):
        self._publicar()
        return "break"

    def _enter_salto_linea(self, evento):
        self.campo_contenido.insert(tk.INSERT, "\n")
        self.campo_contenido.edit_modified(True)
        return "break"

    def _actualizar_formulario(self):
        texto = self.campo_contenido.get("1.0", "end-1c")
        limite = self.aplicacion.gestor_publicaciones.LIMITE_CARACTERES
        valido = (bool(texto.strip()) or bool(self.imagen_seleccionada)) and len(texto) <= limite
        self.contador.configure(text="{} / {} caracteres".format(len(texto), limite),
                                fg="#b00020" if len(texto) > limite else "#555555")
        self.boton_publicar.configure(state="normal" if valido else "disabled")
        if texto:
            self.confirmacion.configure(text="")

    def _publicar(self):
        if getattr(self, "_publicando", False):
            return
        contenido = self.campo_contenido.get("1.0", "end-1c")
        origen_imagen = self.imagen_seleccionada
        if (not contenido.strip() and not origen_imagen) or len(contenido) > self.aplicacion.gestor_publicaciones.LIMITE_CARACTERES:
            self._actualizar_formulario()
            return
        self._publicando = True
        destino = None
        try:
            ruta_imagen = ""
            ruta_video = ""
            if origen_imagen:
                extension = os.path.splitext(origen_imagen)[1].lower()
                carpeta = os.path.join(os.path.dirname(self.aplicacion.gestor_publicaciones.ruta_archivo),
                                       "videos_publicaciones" if extension in EXTENSIONES_VIDEO
                                       else "imagenes_publicaciones")
                os.makedirs(carpeta, exist_ok=True)
                nombre_archivo = uuid.uuid4().hex + extension
                destino = os.path.join(carpeta, nombre_archivo)
                shutil.copyfile(origen_imagen, destino)
                if extension in EXTENSIONES_VIDEO:
                    ruta_video = os.path.join("videos_publicaciones", nombre_archivo)
                else:
                    ruta_imagen = os.path.join("imagenes_publicaciones", nombre_archivo)
            self.aplicacion.gestor_publicaciones.crear_publicacion(
                self.usuario.nombre_usuario, contenido, ruta_imagen, ruta_video,
            )
        except ValueError as error:
            self._eliminar_imagen_temporal(destino)
            messagebox.showerror("Publicaciones", str(error), parent=self.ventana)
            return
        except OSError:
            self._eliminar_imagen_temporal(destino)
            messagebox.showerror("Publicaciones", "No se pudo guardar la publicación. Inténtalo de nuevo.",
                                 parent=self.ventana)
            return
        finally:
            self._publicando = False
        self.campo_contenido.delete("1.0", tk.END)
        self._quitar_imagen(actualizar=False)
        self._actualizar_formulario()
        self._actualizar()
        if hasattr(self, "al_actualizar_vistas"):
            self.al_actualizar_vistas()
        self.confirmacion.configure(text="Publicación creada correctamente.")
        if self.compositor is not None:
            self._ocultar_compositor()

    @staticmethod
    def _eliminar_imagen_temporal(ruta):
        if ruta and os.path.exists(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass

    def _seleccionar_imagen(self):
        ruta = filedialog.askopenfilename(
            parent=self.ventana,
            filetypes=[("Fotos y videos", "*.jpg *.jpeg *.png *.webp *.gif *.mp4 *.webm *.mov"),
                       ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return
        try:
            if os.path.splitext(ruta)[1].lower() in EXTENSIONES_VIDEO:
                validar_video(ruta)
            else:
                validar_imagen(ruta)
        except (OSError, ValueError) as error:
            messagebox.showerror("Imagen", str(error), parent=self.ventana)
            return
        self.imagen_seleccionada = ruta
        self.estado_imagen.configure(text=os.path.basename(ruta))
        if self.preview_frame:
            self.nombre_imagen_preview.configure(text=os.path.basename(ruta))
            self.error_preview.configure(text="")
            self._ancho_preview = 0
            self.preview_frame.pack(fill="x", padx=2, pady=(0, 8), before=self.compositor.winfo_children()[-2])
            self.preview_canvas.yview_moveto(0)
            self._actualizar_vista_previa()
        self._actualizar_formulario()

    def _quitar_imagen(self, actualizar=True):
        if getattr(self, "preview_video", None) is not None:
            self.preview_video.destroy()
            self.preview_video = None
        self.imagen_seleccionada = None
        self.estado_imagen.configure(text="")
        if self.preview_frame:
            self.preview_frame.pack_forget()
            self.preview_canvas.delete("all")
            self.preview_item = None
            self.preview_imagen = None
            self._ancho_preview = 0
        if actualizar:
            self._actualizar_formulario()

    def _actualizar_vista_previa(self):
        if not self.imagen_seleccionada or not self.preview_canvas:
            return
        ancho = self.preview_canvas.winfo_width()
        if ancho <= 2:
            ancho = max(240, self.compositor.winfo_width() - 36)
        ancho = min(720, max(180, ancho - 4))
        if abs(ancho - self._ancho_preview) < 8 and self.preview_item is not None:
            return
        try:
            if os.path.splitext(self.imagen_seleccionada)[1].lower() in EXTENSIONES_VIDEO:
                if getattr(self, "preview_video", None) is not None:
                    self.preview_video.destroy()
                self.preview_canvas.delete("all")
                self.preview_canvas.configure(height=340, scrollregion=(0, 0, ancho, 340))
                self.preview_video = ReproductorVideo(self.preview_canvas, self.imagen_seleccionada)
                self.preview_canvas.create_window(0, 0, anchor="nw", window=self.preview_video, width=ancho)
                self.preview_video.bind("<Configure>", lambda e: self.preview_canvas.configure(
                    height=min(520, e.height), scrollregion=(0, 0, e.width, e.height)), add="+")
                self.preview_item = "video"
                self._ancho_preview = ancho
                self.error_preview.configure(text="")
                return
            if getattr(self, "preview_video", None) is not None:
                self.preview_video.destroy()
                self.preview_video = None
                self.preview_item = None
                self.preview_canvas.delete("all")
            self.preview_imagen = cargar_vista_previa(self.imagen_seleccionada, ancho)
            ancho_imagen, alto_imagen = self.preview_imagen.width(), self.preview_imagen.height()
            if self.preview_item is None:
                self.preview_item = self.preview_canvas.create_image(2, 2, anchor="nw", image=self.preview_imagen)
            else:
                self.preview_canvas.itemconfigure(self.preview_item, image=self.preview_imagen)
            self.preview_canvas.configure(
                height=min(360, alto_imagen + 4),
                scrollregion=(0, 0, ancho_imagen + 4, alto_imagen + 4),
            )
            self._ancho_preview = ancho
            self.error_preview.configure(text="")
        except (OSError, tk.TclError, ValueError) as error:
            self.error_preview.configure(text="No se pudo mostrar la vista previa: {}".format(error))

    def _ajustar_preview(self, evento):
        self._actualizar_vista_previa()

    def _rueda_preview(self, evento, unidades=None):
        if unidades is None:
            if getattr(evento, "num", None) == 4:
                unidades = -1
            elif getattr(evento, "num", None) == 5:
                unidades = 1
            else:
                unidades = -1 if evento.delta > 0 else 1
        self.preview_canvas.yview_scroll(unidades, "units")
        return "break"

    def _actualizar(self):
        gestor = self.aplicacion.gestor_publicaciones
        if hasattr(self, "avatar_publicador"):
            self.avatar_publicador.delete("all")
            dibujar_avatar(self.avatar_publicador, self.usuario,
                           os.path.dirname(self.aplicacion.gestor_usuarios.ruta_archivo), 42)
        if hasattr(self, "nombre_publicador"):
            self.nombre_publicador.configure(text="{}  (@{})".format(
                self.usuario.nombre_visible, self.usuario.nombre_usuario,
            ))
        propias = gestor.obtener_publicaciones_usuario(self.usuario.nombre_usuario)
        amigos = gestor.obtener_publicaciones_amigos(self.usuario.nombre_usuario, self.aplicacion.gestor_amistades)
        inicio = gestor.obtener_publicaciones_inicio(self.usuario.nombre_usuario, self.aplicacion.gestor_amistades)
        self._mostrar(self.muro_personal, propias)
        self._mostrar(self.muro_amigos, amigos)
        if self.lista_personal is not None:
            self.lista_personal.abrir_perfil = getattr(self, "abrir_perfil", None)
            self.lista_inicio.abrir_perfil = getattr(self, "abrir_perfil", None)
            self.lista_personal.mostrar(propias, "Aún no has publicado nada.")
            self.lista_inicio.mostrar(inicio, "Aún no hay publicaciones tuyas ni de tus amigos.")

    def _actualizar_desde_json(self):
        self.aplicacion.gestor_publicaciones.recargar()
        self._actualizar()
        if hasattr(self, "al_actualizar_vistas"):
            self.al_actualizar_vistas()

    def _mostrar(self, muro, publicaciones):
        muro.configure(state="normal")
        muro.delete("1.0", tk.END)
        if not publicaciones:
            mensaje = "No hay publicaciones propias todavía." if muro is self.muro_personal else "No hay publicaciones de tus amigos todavía."
            muro.insert(tk.END, mensaje + "\n")
        for publicacion in publicaciones:
            autor = self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(publicacion.nombre_usuario)
            nombre = "{} (@{})".format(autor.nombre_visible, autor.nombre_usuario) if autor else publicacion.nombre_usuario
            tags = ("tarjeta", "autor")
            if autor and hasattr(self, "abrir_perfil"):
                tag_autor = "autor_" + str(publicacion.identificador)
                muro.tag_configure(tag_autor, foreground="#E4002B", underline=True)
                muro.tag_bind(tag_autor, "<Button-1>", lambda evento, persona=autor: self.abrir_perfil(persona))
                muro.tag_bind(tag_autor, "<Enter>", lambda evento: evento.widget.configure(cursor="hand2"))
                muro.tag_bind(tag_autor, "<Leave>", lambda evento: evento.widget.configure(cursor=""))
                tags += (tag_autor,)
            muro.insert(tk.END, nombre + "\n", tags)
            muro.insert(tk.END, fecha_publicacion(publicacion.fecha) + "\n", ("tarjeta", "fecha"))
            muro.insert(tk.END, publicacion.contenido + "\n", ("tarjeta", "contenido"))
            muro.insert(tk.END, "\n")
        muro.configure(state="disabled")
