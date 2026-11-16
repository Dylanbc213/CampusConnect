"""Conversaciones locales: se actualizan al abrir, enviar o recargar."""
import tkinter as tk
import tkinter.font as tkfont
import re
import webbrowser
try:
    from PIL import Image, ImageDraw, ImageOps, ImageTk
except ImportError:
    Image = ImageDraw = ImageOps = ImageTk = None
import os
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
from gui.avatar import dibujar_avatar
from gui.estilo import aplicar_tema_actual, crear_campo_redondeado
from gui.scroll import enlazar_rueda_descendientes
from gui.imagenes import validar_imagen, cargar_vista_previa
from gui.videos import validar_video, abrir_video, EXTENSIONES_VIDEO


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
        self.video_pendiente = None
        self.ampliacion = None
        barra = tk.Frame(self, background="#FFFFFF")
        barra.pack(fill="x")
        self.titulo = tk.Label(barra, text="Mensajes", background="#FFFFFF", foreground="#1F2937",
                               font=("Segoe UI", 20, "bold"))
        self.titulo.pack(side="left")
        cuerpo = tk.Frame(self, background="#FFFFFF")
        cuerpo.pack(fill="both", expand=True, pady=12)
        cuerpo.columnconfigure(0, weight=1, uniform="chat")
        cuerpo.columnconfigure(2, weight=3, uniform="chat")
        cuerpo.rowconfigure(1, weight=1)
        buscar = tk.Frame(cuerpo, background="#F3F4F6", padx=8, pady=8)
        buscar.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))
        lupa = tk.Canvas(buscar, width=22, height=22, background="#F3F4F6", highlightthickness=0)
        lupa.pack(side="left", padx=(0, 6))
        if Image is not None:
            escala = 4
            icono = Image.new("RGBA", (22 * escala, 22 * escala), (0, 0, 0, 0))
            dibujo = ImageDraw.Draw(icono)
            dibujo.ellipse((3 * escala, 2 * escala, 14 * escala, 13 * escala),
                           outline="#E4002B", width=2 * escala)
            dibujo.line((12 * escala, 12 * escala, 20 * escala, 20 * escala),
                        fill="#E4002B", width=2 * escala)
            icono = icono.resize((22, 22), Image.Resampling.LANCZOS)
            lupa._imagen_lupa = ImageTk.PhotoImage(icono)
            lupa.create_image(0, 0, image=lupa._imagen_lupa, anchor="nw")
        else:
            lupa.create_oval(3, 3, 14, 14, outline="#E4002B", width=2)
            lupa.create_line(13, 13, 20, 20, fill="#E4002B", width=2)
        self.marco_busqueda, self.busqueda = crear_campo_redondeado(
            buscar, tk.Entry, relief="flat", font=("Segoe UI", 10), width=12,
            background="#171A20", foreground="#1F2937", insertbackground="#E4002B")
        self.marco_busqueda.pack(fill="x", expand=True)
        self.busqueda.configure(background="#F3F4F6", insertbackground="#E4002B")
        self.busqueda.bind("<KeyRelease>", lambda e: self.recargar())
        self.lista = ZonaScroll(cuerpo)
        self.lista.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        ttk.Separator(cuerpo, orient="vertical").grid(row=0, column=1, rowspan=2, sticky="ns")
        derecha = tk.Frame(cuerpo, background="#FFFFFF")
        derecha.grid(row=0, column=2, rowspan=2, sticky="nsew")
        cabecera = tk.Frame(derecha, background="#FFFFFF", pady=8)
        cabecera.pack(fill="x", padx=(12, 0))
        self.avatar_cabecera = tk.Canvas(cabecera, width=40, height=40, background="#FFFFFF", highlightthickness=0)
        self.avatar_cabecera.pack(side="left", padx=(0, 10))
        self.cabecera = tk.Label(cabecera, text="Tus mensajes", background="#FFFFFF",
                                 foreground="#1F2937", font=("Segoe UI", 12, "bold"))
        self.cabecera.pack(side="left")
        for widget in (self.avatar_cabecera, self.cabecera):
            widget.bind("<Button-1>", self._perfil_chat)
        ttk.Separator(derecha, orient="horizontal").pack(fill="x")
        pie = tk.Frame(derecha, background="#FFFFFF")
        self.pie = pie
        pie.pack(side="bottom", fill="x", padx=(12, 0))
        self.preview = tk.Frame(pie, background="#FFFFFF")
        self.preview_imagen = tk.Label(self.preview, background="#FFFFFF")
        self.preview_imagen.pack()
        controles = tk.Frame(self.preview, background="#FFFFFF")
        controles.pack()
        for texto, accion in (("Cambiar", self.adjuntar), ("Quitar", self.quitar_imagen),
                              ("Cancelar imagen", self.quitar_imagen)):
            tk.Button(controles, text=texto, command=accion, background="#FFFFFF",
                      foreground="#E4002B", relief="flat").pack(side="left")
        self.marco_entrada, self.entrada = crear_campo_redondeado(
            pie, tk.Text, width=1, height=3, wrap="word", font=("Segoe UI", 11),
            state="disabled", relief="flat", padx=12, pady=8,
            background="#171A20", foreground="#000000", insertbackground="#000000")
        self.entrada._campus_rol = "texto_mensaje"
        self.marco_entrada.pack(fill="x")
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
        self.historial.configure(background="#0B141A")
        self.historial.interior.configure(background="#0B141A")
        self.historial.pack(fill="both", expand=True, padx=(12, 0))
        pie.pack_forget()
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

    def _burbuja_texto(self, padre, contenido, fecha, propio):
        fuente = tkfont.Font(family="Segoe UI", size=10)
        fuente_fecha = tkfont.Font(family="Segoe UI", size=7)
        max_texto = 280
        lineas = []
        for parrafo in contenido.splitlines() or [""]:
            actual = ""
            for palabra in parrafo.split(" "):
                candidato = (actual + " " + palabra).strip()
                if actual and fuente.measure(candidato) > max_texto:
                    lineas.append(actual)
                    actual = palabra
                else:
                    actual = candidato
            lineas.append(actual)
        texto = "\n".join(lineas)
        ancho_texto = min(max_texto, max((fuente.measure(linea) for linea in lineas), default=0))
        ancho = max(145, ancho_texto + 32)
        alto = max(30, (len(lineas) - 1) * fuente.metrics("linespace") + 24)
        color = "#E4002B" if propio else "#343943"
        frente = "#F1F5F6"
        ancho_canvas = ancho + (8 if propio else 0)
        bloque = tk.Frame(padre, background="#0B141A")
        bloque.pack(anchor="e" if propio else "w", padx=8)
        tk.Label(bloque, text=fecha, background="#0B141A", foreground="#AEBAC1",
                 font=("Segoe UI", 8), anchor="e", justify="right").pack(
                     fill="x", pady=(2, 4))
        canvas = tk.Canvas(bloque, width=ancho_canvas, height=alto,
                           background="#0B141A", highlightthickness=0)
        x_derecha = ancho_canvas - 1
        if Image is not None:
            escala = 4
            imagen = Image.new("RGBA", (ancho_canvas * escala, alto * escala), (0, 0, 0, 0))
            dibujo = ImageDraw.Draw(imagen)
            relleno = tuple(bytes.fromhex(color[1:])) + (255,)
            if propio:
                dibujo.rounded_rectangle((0, 0, (ancho_canvas - 10) * escala,
                                          (alto - 1) * escala), radius=12 * escala, fill=relleno)
                dibujo.polygon(((ancho_canvas - 24) * escala, 0,
                                ancho_canvas * escala, 0,
                                (ancho_canvas - 24) * escala, 19 * escala), fill=relleno)
            else:
                dibujo.rounded_rectangle((8 * escala, 0, (ancho_canvas - 1) * escala,
                                          (alto - 1) * escala), radius=12 * escala, fill=relleno)
                dibujo.polygon((0, 0, 24 * escala, 0, 24 * escala, 19 * escala), fill=relleno)
            imagen = imagen.resize((ancho_canvas, alto), Image.Resampling.LANCZOS)
            canvas._burbuja_imagen = ImageTk.PhotoImage(imagen)
            canvas.create_image(0, 0, image=canvas._burbuja_imagen, anchor="nw")
        else:
            if propio:
                puntos = [7, 0, x_derecha - 7, 0, x_derecha, 0, x_derecha - 8, 8,
                          x_derecha - 8, alto - 7, x_derecha - 7, alto, 7, alto,
                          0, alto - 7, 0, 7]
            else:
                puntos = [8, 0, x_derecha - 7, 0, x_derecha, 7, x_derecha, alto - 7,
                          x_derecha - 7, alto, 8, alto, 0, alto - 7, 0, 7,
                          7, 0, 0, 0, 8, 8]
            canvas.create_polygon(puntos, smooth=True, splinesteps=24, fill=color, outline=color)
        x_texto = 22 if not propio else 12
        alto_linea = fuente.metrics("linespace")
        for indice, linea in enumerate(lineas):
            x = x_texto
            inicio = 0
            for enlace in re.finditer(r"https?://[^\s<>()]+|www\.[^\s<>()]+", linea):
                prefijo = linea[inicio:enlace.start()]
                if prefijo:
                    canvas.create_text(x, 8 + indice * alto_linea, text=prefijo,
                                       anchor="nw", font=fuente, fill=frente)
                    x += fuente.measure(prefijo)
                url = enlace.group(0)
                url_limpia = url.rstrip(".,!?;:")
                sobrante = url[len(url_limpia):]
                etiqueta = "enlace_{}_{}".format(indice, enlace.start())
                canvas.create_text(x, 8 + indice * alto_linea, text=url_limpia,
                                   anchor="nw", font=fuente, fill="#FFE1E7" if propio else "#9CCBFF",
                                   underline=True, tags=(etiqueta,))
                canvas.tag_bind(etiqueta, "<Button-1>",
                                lambda evento, destino=url_limpia: webbrowser.open(
                                    destino if destino.lower().startswith(("http://", "https://"))
                                    else "https://" + destino))
                canvas.tag_bind(etiqueta, "<Enter>", lambda evento: canvas.configure(cursor="hand2"))
                canvas.tag_bind(etiqueta, "<Leave>", lambda evento: canvas.configure(cursor=""))
                x += fuente.measure(url_limpia)
                if sobrante:
                    canvas.create_text(x, 8 + indice * alto_linea, text=sobrante,
                                       anchor="nw", font=fuente, fill=frente)
                    x += fuente.measure(sobrante)
                inicio = enlace.end()
            resto = linea[inicio:]
            if resto:
                canvas.create_text(x, 8 + indice * alto_linea, text=resto,
                                   anchor="nw", font=fuente, fill=frente)
        marca = "  âœ“âœ“" if propio else ""
        canvas.pack()

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
        self.pie.pack(side="bottom", fill="x", padx=(12, 0), before=self.historial)
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
                               "ultimo": {"contenido": "Iniciar conversaci\u00f3n", "fecha": ""}}
            for u in sorted(self.gestor.amistades.obtener_amistades(self.gestor._usuario()))
            if u not in existentes)
        consulta = self.busqueda.get().strip().lstrip("@").casefold()
        conversaciones = [c for c in conversaciones if consulta in c["usuario"].casefold()]
        if not conversaciones:
            tk.Label(self.lista.interior, text="No se encontraron amigos" if consulta else "Agrega amigos para conversar", background="#FFFFFF",
                     foreground="#6B7280").pack(pady=12)
        for c in conversaciones:
            usuario = c["usuario"]
            seleccionado = usuario == self.destino
            fondo_fila = "#F3F4F6" if seleccionado else "#FFFFFF"
            fila = tk.Frame(self.lista.interior, background=fondo_fila, pady=10, padx=8)
            fila.pack(fill="x")
            avatar = tk.Canvas(fila, width=36, height=36, highlightthickness=0)
            avatar.pack(side="left", padx=5)
            dibujar_avatar(avatar, self.gestor.usuarios.usuarios_por_nombre[usuario], self.carpeta, 36)
            m = c["ultimo"]
            texto = "@{}{}\n{}".format(usuario,
                " Â· {} sin leer".format(c["no_leidos"]) if c["no_leidos"] else "",
                ("Publicaci\u00f3n compartida" if m.get("publicacion_id") is not None else
                 ("Imagen Â· " if m.get("ruta_imagen") else "") + m["contenido"].replace("\n", " ")[:55]))
            nombre, _, previo = texto.partition("\n")
            bloque = tk.Frame(fila, background=fondo_fila)
            bloque.pack(side="left", fill="x", expand=True, padx=(8, 4))
            etiqueta = tk.Label(bloque, text=nombre, background=fondo_fila, foreground="#1F2937",
                               justify="left", anchor="w", font=("Segoe UI", 10, "bold"), cursor="hand2")
            etiqueta.pack(fill="x")
            resumen = tk.Label(bloque, text=previo, background=fondo_fila, foreground="#6B7280",
                               justify="left", anchor="w", font=("Segoe UI", 9), cursor="hand2",
                               wraplength=180)
            resumen.pack(fill="x")
            fila.bind("<Configure>", lambda e, r=resumen:
                      r.configure(wraplength=max(90, e.width - 100)))
            fecha = tk.Label(fila, text=datetime.fromisoformat(m["fecha"]).strftime("%d/%m") if m["fecha"] else "",
                             background=fondo_fila, foreground="#6B7280", font=("Segoe UI", 8))
            fecha.pack(side="right", padx=4)
            tk.Frame(fila, height=1, background="#D1D5DB").pack(
                side="bottom", fill="x", padx=(0, 0))
            for widget in (fila, avatar, bloque, etiqueta, resumen, fecha):
                widget.bind("<Button-1>", lambda e, u=usuario: self.abrir(u))
        self.historial.limpiar()
        for m in mensajes:
            propio = m["remitente"] == self.gestor._usuario()
            fila = tk.Frame(self.historial.interior, background="#0B141A")
            fila.pack(fill="x", pady=4)
            texto = m["contenido"] + "\n" + datetime.fromisoformat(m["fecha"]).strftime("%d/%m/%Y %H:%M")
            color_burbuja = "#E4002B" if propio else "#343943"
            color_texto = "#F1F5F6"
            if m.get("publicacion_id") is None and not m.get("ruta_imagen"):
                fecha = datetime.fromisoformat(m["fecha"]).strftime("%H:%M")
                self._burbuja_texto(fila, m["contenido"], fecha, propio)
            elif m.get("ruta_imagen") and m.get("publicacion_id") is None:
                bloque_imagen = tk.Frame(fila, background="#0B141A")
                if m["contenido"].strip():
                    fecha = datetime.fromisoformat(m["fecha"]).strftime("%H:%M")
                    self._burbuja_texto(fila, m["contenido"], fecha, propio)
                else:
                    tk.Label(bloque_imagen,
                             text=datetime.fromisoformat(m["fecha"]).strftime("%H:%M"),
                             background="#0B141A", foreground="#AEBAC1",
                             font=("Segoe UI", 8), anchor="e", justify="right").pack(
                                 fill="x", pady=(2, 5))
                burbuja = tk.Label(bloque_imagen, background="#FFFFFF", borderwidth=0,
                                   cursor="hand2")
                burbuja.pack()
                bloque_imagen.pack(anchor="e" if propio else "w", padx=8)
            elif m.get("ruta_video") and m.get("publicacion_id") is None:
                bloque_video = tk.Frame(fila, background="#0B141A")
                if m["contenido"].strip():
                    self._burbuja_texto(fila, m["contenido"],
                                        datetime.fromisoformat(m["fecha"]).strftime("%H:%M"), propio)
                else:
                    tk.Label(bloque_video, text=datetime.fromisoformat(m["fecha"]).strftime("%H:%M"),
                             background="#0B141A", foreground="#AEBAC1",
                             font=("Segoe UI", 8)).pack(anchor="e", pady=(2, 4))
                tk.Button(bloque_video, text="▶  Reproducir video corto",
                          command=lambda ruta=m["ruta_video"]: abrir_video(self.gestor.ruta_video(ruta)),
                          background="#343943", foreground="#F9FAFB", relief="flat",
                          padx=18, pady=16, cursor="hand2").pack()
                bloque_video.pack(anchor="e" if propio else "w", padx=8, pady=3)
            else:
                burbuja = tk.Label(fila, text=texto, justify="left", wraplength=240, padx=12, pady=8,
                                   background=color_burbuja, foreground=color_texto,
                                   font=("Segoe UI", 10), relief="flat")
                burbuja.pack(anchor="e" if propio else "w", padx=5)
            if m.get("publicacion_id") is not None:
                original = next((p for p in self.publicaciones.publicaciones
                                 if p.identificador == m["publicacion_id"]), None)
                if original is None:
                    burbuja.destroy()
                    self._burbuja_texto(
                        fila, "Publicaci\u00f3n no disponible",
                        datetime.fromisoformat(m["fecha"]).strftime("%H:%M"), propio)
                else:
                    burbuja.configure(text="@{}\n{}\nVer publicaci\u00f3n".format(original.nombre_usuario, original.contenido[:140]),
                                      cursor="hand2", relief="flat")
                    if original.ruta_imagen:
                        try:
                            ruta = os.path.join(self.carpeta, original.ruta_imagen)
                            foto = cargar_vista_previa(ruta, 240, 200)
                            burbuja.configure(image=foto, compound="top", cursor="hand2")
                            burbuja._foto = foto
                        except (OSError, ValueError, tk.TclError):
                            pass
                    elif original.ruta_video:
                        burbuja.configure(text="Video corto\nVer publicaci\u00f3n", cursor="hand2")
                    burbuja.bind("<Button-1>", lambda e, p=original: self.ver_publicacion(p))
            if m.get("ruta_imagen"):
                try:
                    ruta = self.gestor.ruta_imagen(m["ruta_imagen"])
                    if Image is not None:
                        with Image.open(ruta) as origen:
                            imagen = ImageOps.exif_transpose(origen).convert("RGBA")
                            imagen = ImageOps.fit(imagen, (240, 260), method=Image.Resampling.LANCZOS)
                            mascara = Image.new("L", imagen.size, 0)
                            ImageDraw.Draw(mascara).rounded_rectangle(
                                (0, 0, imagen.width - 1, imagen.height - 1), radius=18, fill=255)
                            imagen.putalpha(mascara)
                            foto = ImageTk.PhotoImage(imagen)
                    else:
                        foto = cargar_vista_previa(ruta, 240, 260)
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
            self.gestor.enviar(self.destino, self.entrada.get("1.0", "end-1c"),
                               self.imagen_pendiente, self.video_pendiente)
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
            filetypes=[("Fotos y videos", "*.jpg *.jpeg *.png *.webp *.gif *.mp4 *.webm *.mov"),
                       ("Todos los archivos", "*.*")])
        if not ruta:
            return
        es_video = os.path.splitext(ruta)[1].lower() in EXTENSIONES_VIDEO
        try:
            if es_video:
                validar_video(ruta)
                foto = None
            else:
                validar_imagen(ruta, 10 * 1024 * 1024)
                foto = cargar_vista_previa(ruta, 180, 110)
        except (OSError, ValueError, tk.TclError) as error:
            messagebox.showerror("Adjuntar archivo", str(error), parent=self)
            return
        self.imagen_pendiente = None if es_video else ruta
        self.video_pendiente = ruta if es_video else None
        if es_video:
            self.preview_imagen.configure(image="", text="Video corto: " + os.path.basename(ruta),
                                          foreground="#1F2937", font=("Segoe UI", 10, "bold"))
            self.preview_imagen._foto = None
        else:
            self.preview_imagen.configure(image=foto, text="")
            self.preview_imagen._foto = foto
        self.preview.pack(fill="x", before=self.marco_entrada, pady=4)
        aplicar_tema_actual(self.preview)

    def elegir_destinatarios(self, identificador):
        self.cerrar_ampliacion()
        self.ampliacion = tk.Frame(self, background="#FFFFFF", padx=20, pady=16)
        self.ampliacion.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Label(self.ampliacion, text="Enviar publicaci\u00f3n a", background="#FFFFFF",
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
            tarjeta = tk.Frame(lista.interior, background="#FFFFFF", highlightbackground="#E5E7EB",
                               highlightthickness=1, padx=14, pady=12)
            tarjeta.pack(fill="x", padx=4, pady=5)
            tarjeta.columnconfigure(1, weight=1)
            avatar = tk.Canvas(tarjeta, width=44, height=44, background="#FFFFFF", highlightthickness=0)
            avatar.grid(row=0, column=0, rowspan=2, padx=(0, 12))
            dibujar_avatar(avatar, self.gestor.usuarios.usuarios_por_nombre[usuario], self.carpeta, 44)
            tk.Label(tarjeta, text="@" + usuario, background="#FFFFFF", foreground="#1F2937",
                     font=("Segoe UI", 11, "bold"), anchor="w").grid(row=0, column=1, sticky="ew")
            subtitulo = "Chat reciente" if usuario in recientes else "Amigo"
            tk.Label(tarjeta, text=subtitulo, background="#FFFFFF", foreground="#6B7280",
                     font=("Segoe UI", 9), anchor="w").grid(row=1, column=1, sticky="ew")
            def alternar(evento=None, usuario_seleccionado=usuario, fila=tarjeta):
                valor = not seleccion[usuario_seleccionado].get()
                seleccion[usuario_seleccionado].set(valor)
                fondo = "#FCE7EC" if valor else "#FFFFFF"
                borde = "#E4002B" if valor else "#E5E7EB"
                fila.configure(background=fondo, highlightbackground=borde)
                for hijo in fila.winfo_children():
                    try:
                        hijo.configure(background=fondo)
                    except tk.TclError:
                        pass
                return "break"
            for widget in (tarjeta, avatar) + tuple(tarjeta.winfo_children()):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", alternar)
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
            self.titulo.configure(text="PublicaciÃ³n enviada")
        tk.Button(acciones, text="Enviar", command=enviar, background="#E4002B",
                  foreground="#FFFFFF", relief="flat", state="normal" if seleccion else "disabled").pack(side="right")
        lista.terminar()
        aplicar_tema_actual(self.ampliacion)

    def quitar_imagen(self):
        self.imagen_pendiente = None
        self.video_pendiente = None
        self.preview.pack_forget()
        self.preview_imagen.configure(image="", text="")
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
