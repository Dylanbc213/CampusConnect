"""Conversaciones locales: se actualizan al abrir, enviar o recargar."""
import tkinter as tk
import os
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
from gui.avatar import dibujar_avatar
from gui.estilo import aplicar_tema_actual
from gui.scroll import enlazar_rueda_descendientes
from gui.imagenes import validar_imagen, cargar_vista_previa


class ZonaScroll(tk.Canvas):
    def __init__(self, padre):
        super().__init__(padre, background="#FFFFFF", highlightthickness=0, width=1)
        self.interior = tk.Frame(self, background="#FFFFFF")
        self.item = self.create_window(0, 0, window=self.interior, anchor="nw")
        self.bind("<Configure>", lambda e: self.itemconfigure(self.item, width=e.width))
        self.interior.bind("<Configure>", lambda e: self.configure(scrollregion=self.bbox("all")))

    def rueda(self, evento):
        if self.interior.winfo_height() > self.winfo_height():
            arriba = getattr(evento, "num", None) == 4 or getattr(evento, "delta", 0) > 0
            self.yview_scroll(-3 if arriba else 3, "units")
        return "break"

    def limpiar(self):
        for hijo in self.interior.winfo_children():
            hijo.destroy()

    def terminar(self):
        for widget in (self, self.interior):
            for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                widget.unbind(evento)
        enlazar_rueda_descendientes(self, self.rueda)
        aplicar_tema_actual(self)


class Mensajes(tk.Frame):
    def __init__(self, padre, gestor, carpeta, al_contar):
        super().__init__(padre, background="#FFFFFF")
        self.gestor, self.carpeta, self.al_contar = gestor, carpeta, al_contar
        self.destino = None
        self.borradores = {}
        self.imagen_pendiente = None
        self.ampliacion = None
        barra = tk.Frame(self, background="#FFFFFF")
        barra.pack(fill="x")
        self.titulo = tk.Label(barra, text="Mensajes", background="#FFFFFF", foreground="#1F2937",
                               font=("Segoe UI", 20, "bold"))
        self.titulo.pack(side="left")
        tk.Button(barra, text="Recargar", command=self.recargar, background="#FFFFFF",
                  foreground="#E4002B", relief="flat").pack(side="right")
        cuerpo = tk.Frame(self, background="#FFFFFF")
        cuerpo.pack(fill="both", expand=True, pady=12)
        cuerpo.columnconfigure(0, weight=1, uniform="chat")
        cuerpo.columnconfigure(2, weight=2, uniform="chat")
        cuerpo.rowconfigure(1, weight=1)
        buscar = tk.Frame(cuerpo, background="#F3F4F6", padx=8, pady=8)
        buscar.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))
        lupa = tk.Canvas(buscar, width=22, height=22, background="#F3F4F6", highlightthickness=0)
        lupa.pack(side="left", padx=(0, 6))
        lupa.create_oval(3, 3, 14, 14, outline="#E4002B", width=2)
        lupa.create_line(13, 13, 20, 20, fill="#E4002B", width=2)
        self.busqueda = tk.Entry(buscar, relief="flat", font=("Segoe UI", 10), width=12)
        self.busqueda.pack(fill="x", expand=True)
        self.busqueda.configure(background="#F3F4F6", insertbackground="#E4002B")
        self.busqueda.bind("<KeyRelease>", lambda e: self.recargar())
        self.lista = ZonaScroll(cuerpo)
        self.lista.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        ttk.Separator(cuerpo, orient="vertical").grid(row=0, column=1, rowspan=2, sticky="ns")
        derecha = tk.Frame(cuerpo, background="#FFFFFF")
        derecha.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(12, 0))
        cabecera = tk.Frame(derecha, background="#FFFFFF", pady=8)
        cabecera.pack(fill="x")
        self.avatar_cabecera = tk.Canvas(cabecera, width=40, height=40, background="#FFFFFF", highlightthickness=0)
        self.avatar_cabecera.pack(side="left", padx=(0, 10))
        self.cabecera = tk.Label(cabecera, text="Tus mensajes", background="#FFFFFF",
                                 foreground="#1F2937", font=("Segoe UI", 12, "bold"))
        self.cabecera.pack(side="left")
        for widget in (self.avatar_cabecera, self.cabecera):
            widget.bind("<Button-1>", self._perfil_chat)
        ttk.Separator(derecha, orient="horizontal").pack(fill="x")
        pie = tk.Frame(derecha, background="#FFFFFF")
        pie.pack(side="bottom", fill="x")
        ttk.Separator(pie, orient="horizontal").pack(fill="x", pady=(0, 8))
        self.preview = tk.Frame(pie, background="#FFFFFF")
        self.preview_imagen = tk.Label(self.preview, background="#FFFFFF")
        self.preview_imagen.pack()
        controles = tk.Frame(self.preview, background="#FFFFFF")
        controles.pack()
        for texto, accion in (("Cambiar", self.adjuntar), ("Quitar", self.quitar_imagen),
                              ("Cancelar imagen", self.quitar_imagen)):
            tk.Button(controles, text=texto, command=accion, background="#FFFFFF",
                      foreground="#E4002B", relief="flat").pack(side="left")
        self.entrada = tk.Text(pie, width=1, height=3, wrap="word", font=("Segoe UI", 11), state="disabled",
                               relief="flat", padx=12, pady=10)
        self.entrada.pack(fill="x")
        self.entrada.bind("<Return>", self.enviar)
        self.entrada.bind("<Shift-Return>", self._salto)
        self.boton = tk.Button(pie, text="", command=self.enviar, background="#FFFFFF",
                               foreground="#E4002B", relief="flat", state="disabled")
        self.boton._campus_icono = "enviar"
        self.boton._campus_rol = "icono"
        self.boton.pack(side="right", pady=6)
        self.boton_adjuntar = tk.Button(pie, text="Adjuntar imagen", command=self.adjuntar,
                                        background="#FFFFFF", foreground="#E4002B",
                                        relief="flat", state="disabled")
        self.boton_adjuntar.pack(side="left", pady=6)
        self.boton_adjuntar._campus_icono = "imagen"
        self.boton_adjuntar._campus_rol = "icono"
        self.boton_adjuntar.configure(text="", padx=10)
        self.historial = ZonaScroll(derecha)
        self.historial.pack(fill="both", expand=True)
        self.vacio = tk.Label(self.historial, text="Tus conversaciones, en un solo lugar\n\nSelecciona un chat o un amigo para comenzar",
                              background="#FFFFFF", foreground="#6B7280", wraplength=280, justify="center")
        self.vacio.place(relx=0.5, rely=0.5, anchor="center")
        self.historial.bind("<Configure>", self._ajustar_historial, add="+")

    def _ajustar_historial(self, evento):
        self.vacio.configure(wraplength=max(100, evento.width - 32))
        for fila in self.historial.interior.winfo_children():
            for burbuja in fila.winfo_children():
                if isinstance(burbuja, tk.Label):
                    burbuja.configure(wraplength=max(100, min(360, int(evento.width * 0.75) - 24)))

    def _perfil_chat(self, evento=None):
        if self.destino and hasattr(self, "abrir_perfil"):
            self.abrir_perfil(self.gestor.usuarios.usuarios_por_nombre[self.destino])

    def _salto(self, evento):
        self.entrada.insert("insert", "\n")
        return "break"

    def abrir(self, destino):
        try:
            self.gestor._validar(destino)
        except (ValueError, PermissionError) as error:
            messagebox.showerror("Mensajes", str(error), parent=self)
            return False
        if self.destino:
            self.borradores[self.destino] = self.entrada.get("1.0", "end-1c")
        if destino != self.destino:
            self.quitar_imagen()
            self.cerrar_ampliacion()
        self.destino = destino
        self.entrada.configure(state="normal")
        self.entrada.delete("1.0", "end")
        self.entrada.insert("1.0", self.borradores.get(destino, ""))
        self.boton.configure(state="normal")
        self.boton_adjuntar.configure(state="normal")
        self.cabecera.configure(text="@" + destino)
        self.vacio.place_forget()
        self.avatar_cabecera.delete("all")
        dibujar_avatar(self.avatar_cabecera, self.gestor.usuarios.usuarios_por_nombre[destino], self.carpeta, 40)
        self.avatar_cabecera.configure(cursor="hand2")
        self.cabecera.configure(cursor="hand2")
        self.recargar()
        self.entrada.focus_set()
        return True

    def recargar(self):
        try:
            mensajes = self.gestor.conversacion(self.destino, marcar=True) if self.destino else []
            conversaciones = self.gestor.conversaciones()
        except (OSError, ValueError, PermissionError) as error:
            messagebox.showerror("Mensajes", str(error), parent=self)
            return
        self.lista.limpiar()
        total = sum(c["no_leidos"] for c in conversaciones)
        self.titulo.configure(text="Mensajes ({})".format(total))
        self.al_contar(total)
        existentes = {c["usuario"] for c in conversaciones}
        conversaciones.extend({"usuario": u, "no_leidos": 0,
                               "ultimo": {"contenido": "Iniciar conversación", "fecha": ""}}
            for u in sorted(self.gestor.amistades.obtener_amistades(self.gestor._usuario()))
            if u not in existentes)
        consulta = self.busqueda.get().strip().lstrip("@").casefold()
        conversaciones = [c for c in conversaciones if consulta in c["usuario"].casefold()]
        if not conversaciones:
            tk.Label(self.lista.interior, text="No se encontraron amigos" if consulta else "Agrega amigos para conversar", background="#FFFFFF",
                     foreground="#6B7280").pack(pady=12)
        for c in conversaciones:
            usuario = c["usuario"]
            fila = tk.Frame(self.lista.interior, background="#FCE7EC" if usuario == self.destino else "#FFFFFF", pady=10)
            fila.pack(fill="x")
            avatar = tk.Canvas(fila, width=36, height=36, highlightthickness=0)
            avatar.pack(side="left", padx=5)
            dibujar_avatar(avatar, self.gestor.usuarios.usuarios_por_nombre[usuario], self.carpeta, 36)
            m = c["ultimo"]
            texto = "@{}{}\n{}".format(usuario,
                " · {} sin leer".format(c["no_leidos"]) if c["no_leidos"] else "",
                ("Publicación compartida" if m.get("publicacion_id") is not None else
                 ("Imagen · " if m.get("ruta_imagen") else "") + m["contenido"].replace("\n", " ")[:55]))
            etiqueta = tk.Label(fila, text=texto, background="#FFFFFF", foreground="#1F2937",
                               justify="left", wraplength=150, cursor="hand2")
            etiqueta.pack(side="left", fill="x", expand=True)
            fecha = tk.Label(fila, text=datetime.fromisoformat(m["fecha"]).strftime("%d/%m\n%H:%M") if m["fecha"] else "",
                             background="#FFFFFF", foreground="#6B7280", font=("Segoe UI", 8))
            fecha.pack(side="right", padx=4)
            fecha.pack_configure(before=etiqueta)
            fila.bind("<Configure>", lambda e, texto=etiqueta, fecha=fecha:
                      texto.configure(wraplength=max(60, e.width - 56 - fecha.winfo_reqwidth())))
            ttk.Separator(fila, orient="horizontal").place(relx=0, rely=1, relwidth=1, anchor="sw")
            for widget in (fila, avatar, etiqueta, fecha):
                widget.bind("<Button-1>", lambda e, u=usuario: self.abrir(u))
        self.historial.limpiar()
        for m in mensajes:
            propio = m["remitente"] == self.gestor._usuario()
            fila = tk.Frame(self.historial.interior, background="#FFFFFF")
            fila.pack(fill="x", pady=4)
            texto = m["contenido"] + "\n" + datetime.fromisoformat(m["fecha"]).strftime("%d/%m/%Y %H:%M")
            burbuja = tk.Label(fila, text=texto, justify="left", wraplength=240, padx=12, pady=8,
                               background="#E4002B" if propio else "#F3F4F6",
                               foreground="#FFFFFF" if propio else "#1F2937")
            burbuja.pack(anchor="e" if propio else "w", padx=5)
            if m.get("publicacion_id") is not None:
                original = next((p for p in self.publicaciones.publicaciones
                                 if p.identificador == m["publicacion_id"]), None)
                if original is None:
                    burbuja.configure(text="Publicación no disponible\n" + texto)
                else:
                    burbuja.configure(text="@{}\n{}\nVer publicación →".format(original.nombre_usuario, original.contenido[:140]),
                                      cursor="hand2", relief="flat")
                    if original.ruta_imagen:
                        try:
                            ruta = os.path.join(self.carpeta, original.ruta_imagen)
                            foto = cargar_vista_previa(ruta, 240, 200)
                            burbuja.configure(image=foto, compound="top", cursor="hand2")
                            burbuja._foto = foto
                        except (OSError, ValueError, tk.TclError):
                            pass
                    burbuja.bind("<Button-1>", lambda e, p=original: self.ver_publicacion(p))
            if m.get("ruta_imagen"):
                try:
                    ruta = self.gestor.ruta_imagen(m["ruta_imagen"])
                    foto = cargar_vista_previa(ruta, 240, 200)
                    burbuja.configure(image=foto, compound="top", cursor="hand2")
                    burbuja._foto = foto
                    burbuja.bind("<Button-1>", lambda e, r=ruta: self.ampliar(r))
                except (OSError, ValueError, tk.TclError):
                    burbuja.configure(text="Imagen no disponible\n" + texto)
        self.lista.terminar()
        self.historial.terminar()
        aplicar_tema_actual(self)
        self.historial.update_idletasks()
        self.historial.yview_moveto(1)

    def enviar(self, evento=None):
        if self.destino is None:
            return "break"
        try:
            self.gestor.enviar(self.destino, self.entrada.get("1.0", "end-1c"), self.imagen_pendiente)
        except (OSError, ValueError, PermissionError) as error:
            messagebox.showerror("Mensajes", str(error), parent=self)
            return "break"
        self.entrada.delete("1.0", "end")
        self.quitar_imagen()
        self.borradores.pop(self.destino, None)
        self.recargar()
        return "break"

    def adjuntar(self):
        if self.destino is None:
            return
        ruta = filedialog.askopenfilename(parent=self,
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp *.gif")])
        if not ruta:
            return
        try:
            validar_imagen(ruta, 10 * 1024 * 1024)
            foto = cargar_vista_previa(ruta, 180, 110)
        except (OSError, ValueError, tk.TclError) as error:
            messagebox.showerror("Adjuntar imagen", str(error), parent=self)
            return
        self.imagen_pendiente = ruta
        self.preview_imagen.configure(image=foto)
        self.preview_imagen._foto = foto
        self.preview.pack(fill="x", before=self.entrada, pady=4)
        aplicar_tema_actual(self.preview)

    def elegir_destinatarios(self, identificador):
        self.cerrar_ampliacion()
        self.ampliacion = tk.Frame(self, background="#FFFFFF", padx=20, pady=16)
        self.ampliacion.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Label(self.ampliacion, text="Enviar publicación a amigos", background="#FFFFFF",
                 foreground="#1F2937", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        acciones = tk.Frame(self.ampliacion, background="#FFFFFF")
        acciones.pack(side="bottom", fill="x", pady=12)
        tk.Button(acciones, text="Cancelar", command=self.cerrar_ampliacion,
                  background="#FFFFFF", foreground="#6B7280", relief="flat").pack(side="left")
        lista = ZonaScroll(self.ampliacion)
        lista.pack(fill="both", expand=True)
        seleccion = {}
        try:
            recientes = [c["usuario"] for c in self.gestor.conversaciones()]
            amigos = self.gestor.amistades.obtener_amistades(self.gestor._usuario())
        except (OSError, ValueError, PermissionError) as error:
            self.cerrar_ampliacion()
            messagebox.showerror("Compartir", str(error), parent=self)
            return
        for usuario in dict.fromkeys(recientes + sorted(amigos)):
            variable = tk.BooleanVar(value=False)
            seleccion[usuario] = variable
            tk.Checkbutton(lista.interior, text="@{}{}".format(usuario, " · Chat reciente" if usuario in recientes else ""),
                           variable=variable, background="#FFFFFF", foreground="#1F2937",
                           anchor="w").pack(fill="x", pady=6)
        if not seleccion:
            tk.Label(lista.interior, text="Agrega amigos para compartir publicaciones.",
                     background="#FFFFFF", foreground="#6B7280").pack(pady=20)
        def enviar():
            try:
                self.gestor.compartir([u for u, v in seleccion.items() if v.get()], identificador, self.publicaciones)
            except (OSError, ValueError, PermissionError) as error:
                messagebox.showerror("Compartir", str(error), parent=self)
                return
            self.cerrar_ampliacion()
            self.recargar()
            self.titulo.configure(text="Publicación enviada")
        tk.Button(acciones, text="Enviar", command=enviar, background="#E4002B",
                  foreground="#FFFFFF", relief="flat", state="normal" if seleccion else "disabled").pack(side="right")
        lista.terminar()
        aplicar_tema_actual(self.ampliacion)

    def quitar_imagen(self):
        self.imagen_pendiente = None
        self.preview.pack_forget()
        self.preview_imagen.configure(image="")
        self.preview_imagen._foto = None

    def ver_publicacion(self, publicacion):
        from gui.lista_publicaciones import TarjetaPublicacion
        self.cerrar_ampliacion()
        self.ampliacion = tk.Frame(self, background="#FFFFFF", padx=12, pady=12)
        self.ampliacion.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Button(self.ampliacion, text="Volver al chat", command=self.cerrar_ampliacion,
                  background="#FFFFFF", foreground="#E4002B", relief="flat").pack(anchor="w")
        zona = ZonaScroll(self.ampliacion)
        zona.pack(fill="both", expand=True)
        TarjetaPublicacion(zona.interior, self.aplicacion, self.gestor.sesion(), publicacion,
                           self.abrir_perfil, zona.rueda).pack(fill="x")
        zona.terminar()
        aplicar_tema_actual(self.ampliacion)

    def cerrar_ampliacion(self):
        if self.ampliacion is not None:
            self.ampliacion.destroy()
            self.ampliacion = None

    def ampliar(self, ruta):
        try:
            foto = cargar_vista_previa(ruta, max(100, self.winfo_width() - 40),
                                      max(100, self.winfo_height() - 80))
        except (OSError, ValueError, tk.TclError) as error:
            messagebox.showerror("Imagen", str(error), parent=self)
            return
        self.cerrar_ampliacion()
        self.ampliacion = tk.Frame(self, background="#FFFFFF")
        self.ampliacion.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Button(self.ampliacion, text="Cerrar imagen", command=self.cerrar_ampliacion,
                  background="#E4002B", foreground="#FFFFFF", relief="flat").pack(anchor="e", pady=8)
        etiqueta = tk.Label(self.ampliacion, image=foto, background="#FFFFFF")
        etiqueta._foto = foto
        etiqueta.pack(expand=True)
        aplicar_tema_actual(self.ampliacion)
