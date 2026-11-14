import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from gui.estilo import decorar, encabezado


class VentanaMuro:
    def __init__(self, contenedor, aplicacion, usuario):
        self.aplicacion = aplicacion
        self.usuario = usuario
        self.ventana = contenedor
        contenido = contenedor
        tk.Label(contenido, text="Nueva publicación").pack()
        tk.Label(contenido, text="¿Qué estás pensando?", anchor="w").pack(fill="x", padx=12, pady=(12, 6))
        self.campo_contenido = ScrolledText(contenido, height=5, width=30, wrap="word")
        self.campo_contenido.pack(fill="x", padx=12, pady=(0, 8))
        self.contador = tk.Label(contenido, text="0 / 500 caracteres", anchor="e")
        self.contador.pack(fill="x", padx=10)
        self.boton_publicar = tk.Button(contenido, text="Publicar", command=self._publicar, state="disabled")
        self.boton_publicar.pack(anchor="e", padx=12, pady=4)
        self.confirmacion = tk.Label(contenido, text="", fg="#24663b")
        self.confirmacion.pack()
        self.campo_contenido.bind("<<Modified>>", self._contenido_modificado)
        tk.Button(contenido, text="Actualizar publicaciones", command=self._actualizar).pack(anchor="e", padx=12, pady=4)
        self.titulo_feed = tk.Label(contenido, text="Mi muro", anchor="w")
        self.titulo_feed.pack(fill="x", padx=12, pady=(12, 6))
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
        decorar(contenido)
        encabezado(contenido, "Nueva publicación")
        self.campo_contenido.configure(font=("Segoe UI", 12), background="#F3F4F6", foreground="#1F2937",
                                      insertbackground="#1F2937", relief="solid", borderwidth=1,
                                      highlightthickness=1, highlightbackground="#9CA3AF",
                                      highlightcolor="#E4002B", padx=16, pady=14)
        self._actualizar()

    def mostrar_feed(self, propias=True):
        self.muro_personal.pack_forget()
        self.muro_amigos.pack_forget()
        self.titulo_feed.configure(text="Mi muro" if propias else "Publicaciones de amigos",
                                   font=("Segoe UI", 14, "bold"))
        muro = self.muro_personal if propias else self.muro_amigos
        muro.pack(fill="both", expand=True, padx=10, pady=4)
        self._actualizar()

    def _contenido_modificado(self, evento=None):
        if not self.campo_contenido.edit_modified():
            return
        self.campo_contenido.edit_modified(False)
        self._actualizar_formulario()

    def _actualizar_formulario(self):
        texto = self.campo_contenido.get("1.0", "end-1c")
        limite = self.aplicacion.gestor_publicaciones.LIMITE_CARACTERES
        valido = bool(texto.strip()) and len(texto) <= limite
        self.contador.configure(text="{} / {} caracteres".format(len(texto), limite),
                                fg="#b00020" if len(texto) > limite else "#555555")
        self.boton_publicar.configure(state="normal" if valido else "disabled")
        if texto:
            self.confirmacion.configure(text="")

    def _publicar(self):
        try:
            self.aplicacion.gestor_publicaciones.crear_publicacion(
                self.usuario.nombre_usuario, self.campo_contenido.get("1.0", "end-1c"),
            )
        except ValueError as error:
            messagebox.showerror("Publicaciones", str(error), parent=self.ventana)
            return
        except OSError:
            messagebox.showerror("Publicaciones", "No se pudo guardar la publicación. Inténtalo de nuevo.",
                                 parent=self.ventana)
            return
        self.campo_contenido.delete("1.0", tk.END)
        self._actualizar_formulario()
        self._actualizar()
        self.confirmacion.configure(text="Publicación creada correctamente.")

    def _actualizar(self):
        gestor = self.aplicacion.gestor_publicaciones
        self._mostrar(self.muro_personal, gestor.obtener_publicaciones_usuario(self.usuario.nombre_usuario))
        self._mostrar(self.muro_amigos, gestor.obtener_publicaciones_amigos(
            self.usuario.nombre_usuario, self.aplicacion.gestor_amistades,
        ))

    def _mostrar(self, muro, publicaciones):
        muro.configure(state="normal")
        muro.delete("1.0", tk.END)
        if not publicaciones:
            mensaje = "No hay publicaciones propias todavía." if muro is self.muro_personal else "No hay publicaciones de tus amigos todavía."
            muro.insert(tk.END, mensaje + "\n")
        for publicacion in publicaciones:
            autor = self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(publicacion.nombre_usuario)
            nombre = "{} (@{})".format(autor.nombre, autor.nombre_usuario) if autor else publicacion.nombre_usuario
            muro.insert(tk.END, nombre + "\n", ("tarjeta", "autor"))
            muro.insert(tk.END, publicacion.fecha + "\n", ("tarjeta", "fecha"))
            muro.insert(tk.END, publicacion.contenido + "\n", ("tarjeta", "contenido"))
            muro.insert(tk.END, "\n")
        muro.configure(state="disabled")
