"""Reproducción con sonido sobre una superficie Tk, sin abrir VLC externamente."""
import os
import tempfile
import weakref
import tkinter as tk
from tkinter import ttk


class ReproductorVideo(tk.Frame):
    _instancias = weakref.WeakSet()

    def __init__(self, padre, ruta, ampliado=False):
        super().__init__(padre, background="#FFFFFF")
        self.ruta = os.path.abspath(ruta)
        self.motor = self.player = None
        self._tarea = None
        self._cerrando = False
        self.ampliado = ampliado
        self.silenciado = not ampliado
        self.overlay = None
        self.grande = None
        self.proporcion = 16 / 9
        self._tamano_redondeado = None
        self._geometria = None
        self._video_dimensiones = None
        self._video_codificado = None
        self._mascaras = tempfile.TemporaryDirectory(prefix="campus_video_")
        self._numero_mascara = 0
        self._sonido_pendiente = False
        self.area = tk.Frame(self, background="#FFFFFF", height=280, width=1)
        self.area.pack(fill="x")
        self.pantalla = tk.Frame(self.area, background="#111318", cursor="hand2")
        self.pantalla.place(relx=0.5 if ampliado else 0, x=0, y=0,
                            anchor="n" if ampliado else "nw", width=360, height=203)
        self.area.bind("<Configure>", self._ajustar)
        controles = tk.Frame(self, background="#FFFFFF")
        if ampliado:
            controles.pack(fill="x", pady=5)
        self.boton = tk.Button(controles, text="▶ Reproducir", command=self.alternar,
                               background="#E4002B", foreground="#FFFFFF", relief="flat")
        self.boton.pack(side="left")
        tk.Button(controles, text="Detener", command=self.detener, background="#FFFFFF",
                  foreground="#6B7280", relief="flat").pack(side="left", padx=6)
        tk.Label(controles, text="Volumen", background="#FFFFFF").pack(side="left")
        self.volumen = ttk.Scale(controles, from_=0, to=100, length=85, command=self._volumen)
        self.volumen.set(80)
        self.volumen.pack(side="left", padx=6)
        if not ampliado:
            self.pantalla.bind("<Button-1>", lambda e: self.ampliar())
            self.duracion = tk.Label(self.area, text="0:00", background="#111318", foreground="#F9FAFB",
                                     padx=5, pady=2, font=("Segoe UI", 9), cursor="hand2")
            self.silencio = tk.Label(self.area, text="🔇", background="#111318", foreground="#F9FAFB",
                                     padx=6, pady=2, font=("Segoe UI Symbol", 11), cursor="hand2")
            self.duracion.bind("<Button-1>", lambda e: self.ampliar())
            self.silencio.bind("<Button-1>", self.alternar_sonido)
        self.estado = tk.Label(self, text="", background="#FFFFFF", foreground="#6B7280")
        self.pantalla.bind("<Map>", lambda e: self._automatico())
        self.pantalla.bind("<Unmap>", lambda e: self._ocultar())
        self.bind("<Destroy>", self._destruir)
        from gui.estilo import aplicar_tema_actual
        aplicar_tema_actual(self)
        self._instancias.add(self)

    def _iniciar(self):
        if self.player is not None:
            return
        if not os.path.isfile(self.ruta):
            raise OSError("El video ya no está disponible.")
        import vlc
        opciones = ["--no-video-title-show", "--no-fullscreen", "--no-video-on-top",
                    "--file-caching=500", "--audio-time-stretch"]
        self.motor = vlc.Instance(*opciones)
        if self.motor is None:
            raise OSError("No se pudo iniciar VLC.")
        self.player = self.motor.media_player_new()
        media = self.motor.media_new(self.ruta)
        self.player.set_media(media)
        media.release()
        self.update_idletasks()
        if os.name == "nt":
            self.player.set_hwnd(self.pantalla.winfo_id())
        else:
            self.player.set_xwindow(self.pantalla.winfo_id())
        self.player.video_set_mouse_input(False)
        self.player.video_set_key_input(False)
        self._aplicar_sonido()

    def alternar(self):
        try:
            self._iniciar()
            if self.player.is_playing():
                self.player.set_pause(1)
                self.boton.configure(text="▶ Continuar")
            else:
                if self.player.play() == -1:
                    raise OSError("No se pudo reproducir este video.")
                self.player.set_rate(1.0)
                self._aplicar_sonido()
                self._sonido_pendiente = True
                self.boton.configure(text="❚❚ Pausar")
                self.estado.configure(text="")
                self.estado.pack_forget()
                if self._tarea is None:
                    self._tarea = self.after(300, self._comprobar)
        except (ImportError, OSError, NameError, AttributeError) as error:
            self.estado.configure(text="No se pudo iniciar el video. Comprueba VLC y python-vlc. " + str(error))
            self.estado.pack(anchor="w")

    def _comprobar(self):
        self._tarea = None
        if self.player is None:
            return
        estado = str(self.player.get_state())
        if self._sonido_pendiente and estado.endswith("Playing"):
            self._aplicar_sonido()
            self._sonido_pendiente = False
        if not self.ampliado:
            segundos = max(0, (self.player.get_length() - max(0, self.player.get_time())) // 1000)
            self.duracion.configure(text="{}:{:02d}".format(segundos // 60, segundos % 60))
        ancho, alto = self.player.video_get_size()
        # VLC puede devolver el tamaño codificado, anterior a la rotación del móvil.
        if self._video_dimensiones is None:
            media = self.player.get_media()
            try:
                dimensiones = self._dimensiones_media(media)
                if dimensiones and min(dimensiones) > 0:
                    self._video_dimensiones = dimensiones
                    self._video_codificado = self._dimensiones_media(media, codificado=True)
            finally:
                if media is not None:
                    media.release()
        if self._video_dimensiones:
            ancho, alto = self._video_dimensiones
        if ancho > 0 and alto > 0:
            self.proporcion = ancho / alto
            self._ajustar()
        if estado.endswith("Error"):
            self.estado.configure(text="No se puede reproducir este archivo de video.")
            self.estado.pack(anchor="w")
            self.detener()
        elif estado.endswith("Ended"):
            self.detener()
            if not self.ampliado and self.winfo_viewable() and self.overlay is None:
                self.alternar()
        else:
            self._tarea = self.after(300, self._comprobar)

    def _volumen(self, valor):
        if self.player is not None and self.ampliado:
            self.player.audio_set_volume(int(float(valor)))

    @staticmethod
    def _dimensiones_media(media, codificado=False):
        if media is None:
            return None
        import ctypes
        import vlc
        pistas = ctypes.POINTER(vlc.MediaTrack)()
        cantidad = vlc.libvlc_media_tracks_get(media, ctypes.byref(pistas))
        if not cantidad:
            return None
        try:
            tabla = ctypes.cast(pistas, ctypes.POINTER(ctypes.POINTER(vlc.MediaTrack)))
            for i in range(cantidad):
                pista = tabla[i].contents
                if pista.type.value == 1 and pista.audio:
                    # En libvlc audio/video/subtitle son una unión; python-vlc
                    # 3.0.21203 los declara como campos consecutivos.
                    video = ctypes.cast(pista.audio, ctypes.POINTER(vlc.VideoTrack)).contents
                    if codificado:
                        girado = getattr(video.orientation, "value", video.orientation) in (4, 5, 6, 7)
                        return video.width, video.height, girado
                    return ReproductorVideo._dimensiones_video(video)
        finally:
            vlc.libvlc_media_tracks_release(
                ctypes.cast(pistas, ctypes.POINTER(ctypes.POINTER(vlc.MediaTrack))), cantidad)

    @staticmethod
    def _dimensiones_video(video):
        ancho, alto = video.width, video.height
        if video.sar_num and video.sar_den:
            ancho *= video.sar_num / video.sar_den
        if getattr(video.orientation, "value", video.orientation) in (4, 5, 6, 7):
            ancho, alto = alto, ancho
        return ancho, alto

    def _aplicar_sonido(self):
        if not self.silenciado:
            # Solo el video elegido puede emitir audio, incluso entre vistas.
            for otro in tuple(self._instancias):
                if otro is self or otro._cerrando or otro.silenciado:
                    continue
                otro.silenciado = True
                otro._aplicar_sonido()
                if not otro.ampliado:
                    otro.silencio.configure(text="🔇")
        if self.player is not None:
            self.player.audio_set_volume(0 if self.silenciado else int(self.volumen.get()))
            self.player.audio_set_mute(self.silenciado)

    def alternar_sonido(self, evento=None):
        self.silenciado = not self.silenciado
        self._aplicar_sonido()
        self.silencio.configure(text="🔇" if self.silenciado else "🔊")
        return "break"

    def _ajustar(self, evento=None):
        fondo = self.master.cget("background")
        self.configure(background=fondo)
        self.area.configure(background=fondo)
        ancho = max(1, self.area.winfo_width())
        if not self.ampliado:
            ancho = min(ancho, 520)
        alto_max = max(100, self.winfo_toplevel().winfo_height() - 160) if self.ampliado else 500
        alto = min(alto_max, max(1, round(ancho / self.proporcion)))
        ancho = min(ancho, max(1, round(alto * self.proporcion)))
        if self._geometria == (ancho, alto, fondo) and (self.ampliado or self._tamano_redondeado is not None):
            return
        self._geometria = (ancho, alto, fondo)
        self.area.configure(height=alto)
        self.pantalla.place_configure(width=ancho, height=alto)
        if not self.ampliado:
            self.duracion.place(x=12, y=alto - 12, anchor="sw")
            self.silencio.place(x=ancho - 12, y=alto - 12, anchor="se")
            self.duracion.lift()
            self.silencio.lift()
            self._redondear(ancho, alto)

    def _redondear(self, ancho, alto):
        fondo = self.area.cget("background")
        clave = (ancho, alto, fondo)
        if os.name == "nt":
            if self._tamano_redondeado == clave:
                return
            # Recortar la superficie visible, independientemente de la
            # orientación y resolución internas del video en VLC.
            import ctypes
            from ctypes import wintypes
            gdi = ctypes.WinDLL("gdi32", use_last_error=True)
            user = ctypes.WinDLL("user32", use_last_error=True)
            gdi.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
            gdi.CreateRoundRectRgn.restype = wintypes.HANDLE
            gdi.DeleteObject.argtypes = [wintypes.HANDLE]
            gdi.DeleteObject.restype = wintypes.BOOL
            user.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HANDLE, wintypes.BOOL]
            user.SetWindowRgn.restype = ctypes.c_int
            diametro = min(28, ancho, alto)
            region = gdi.CreateRoundRectRgn(0, 0, ancho + 1, alto + 1, diametro, diametro)
            if region:
                if user.SetWindowRgn(self.pantalla.winfo_id(), region, True):
                    # Windows pasa a ser propietario de la región.
                    self._tamano_redondeado = clave
                else:
                    gdi.DeleteObject(region)
            return
        if self.player is None or self._video_dimensiones is None or self._tamano_redondeado == clave:
            return
        from PIL import Image, ImageDraw
        import vlc
        mascara = Image.new("L", (ancho * 4, alto * 4), 255)
        ImageDraw.Draw(mascara).rounded_rectangle((0, 0, ancho * 4 - 1, alto * 4 - 1), radius=56, fill=0)
        tamano = tuple(max(1, round(v)) for v in self._video_dimensiones)
        if self._video_codificado:
            ancho_original, alto_original, girado = self._video_codificado
            # El filtro de VLC aplica la máscara antes de rotar el video.
            if girado:
                mascara = mascara.transpose(Image.Transpose.ROTATE_90)
            tamano = (ancho_original, alto_original)
        mascara = mascara.resize(tamano, Image.Resampling.LANCZOS)
        color = tuple(v // 257 for v in self.winfo_rgb(fondo))
        esquinas = Image.new("RGBA", tamano, color + (255,))
        esquinas.putalpha(mascara)
        self._numero_mascara += 1
        ruta = os.path.join(self._mascaras.name, str(self._numero_mascara) + ".png")
        esquinas.save(ruta)
        self.player.video_set_logo_string(vlc.VideoLogoOption.logo_file, ruta)
        self.player.video_set_logo_int(vlc.VideoLogoOption.logo_position, 0)
        self.player.video_set_logo_int(vlc.VideoLogoOption.logo_opacity, 255)
        self.player.video_set_logo_int(vlc.VideoLogoOption.logo_enable, 1)
        self._tamano_redondeado = clave

    def _automatico(self):
        if not self._cerrando and self.overlay is None and (self.player is None or not self.player.is_playing()):
            self.alternar()

    def _ocultar(self):
        if self._cerrando:
            return
        self.cerrar_ampliacion(reanudar=False)
        self.detener()

    def ampliar(self):
        if self.ampliado or self.overlay is not None:
            return
        from gui.estilo import aplicar_tema_actual
        self.detener()
        self.overlay = tk.Frame(self.winfo_toplevel(), background="#FFFFFF", padx=20, pady=12)
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.overlay.lift()
        tk.Button(self.overlay, text="Cerrar video", command=self.cerrar_ampliacion,
                  background="#E4002B", foreground="#FFFFFF", relief="flat").pack(anchor="e", pady=8)
        self.grande = ReproductorVideo(self.overlay, self.ruta, ampliado=True)
        self.grande.proporcion = self.proporcion
        self.grande.pack(fill="both", expand=True)
        aplicar_tema_actual(self.overlay)

    def cerrar_ampliacion(self, reanudar=True):
        overlay = self.overlay
        self.overlay = None
        if overlay is not None:
            if self.grande is not None:
                self.grande.detener()
            overlay.destroy()
            self.grande = None
            if reanudar and self.winfo_viewable():
                self._automatico()

    def detener(self):
        if self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
        if self.player is not None:
            self.player.stop()
        self.boton.configure(text="▶ Reproducir")

    def _destruir(self, evento):
        if evento.widget is not self:
            return
        self._cerrando = True
        self.cerrar_ampliacion(reanudar=False)
        if self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
        if self.player is not None:
            self.player.stop()
            self.player.release()
            self.player = None
        if self.motor is not None:
            self.motor.release()
            self.motor = None
        self._mascaras.cleanup()

    def destroy(self):
        # LibVLC debe soltar el HWND antes de que Tk destruya la superficie.
        from types import SimpleNamespace
        self._destruir(SimpleNamespace(widget=self))
        super().destroy()
