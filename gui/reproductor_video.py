"""Reproducción con sonido sobre una superficie Tk, sin abrir VLC externamente."""
import os
import tkinter as tk
from tkinter import ttk


class ReproductorVideo(tk.Frame):
    def __init__(self, padre, ruta):
        super().__init__(padre, background="#FFFFFF")
        self.ruta = os.path.abspath(ruta)
        self.motor = self.player = None
        self._tarea = None
        self.pantalla = tk.Frame(self, background="#111318", height=280, width=1)
        self.pantalla.pack(fill="x")
        controles = tk.Frame(self, background="#FFFFFF")
        controles.pack(fill="x", pady=5)
        self.boton = tk.Button(controles, text="▶ Reproducir", command=self.alternar,
                               background="#E4002B", foreground="#FFFFFF", relief="flat")
        self.boton.pack(side="left")
        tk.Button(controles, text="Detener", command=self.detener, background="#FFFFFF",
                  foreground="#6B7280", relief="flat").pack(side="left", padx=6)
        tk.Label(controles, text="Volumen", background="#FFFFFF").pack(side="left")
        self.volumen = ttk.Scale(controles, from_=0, to=100, command=self._volumen)
        self.volumen.set(80)
        self.volumen.pack(side="left", fill="x", expand=True)
        self.estado = tk.Label(self, text="", background="#FFFFFF", foreground="#6B7280")
        self.estado.pack(anchor="w")
        self.pantalla.bind("<Unmap>", lambda e: self.detener())
        self.bind("<Destroy>", self._destruir)

    def _iniciar(self):
        if self.player is not None:
            return
        if not os.path.isfile(self.ruta):
            raise OSError("El video ya no está disponible.")
        import vlc
        self.motor = vlc.Instance("--no-video-title-show", "--no-fullscreen", "--no-video-on-top")
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
        self.player.audio_set_volume(int(self.volumen.get()))

    def alternar(self):
        try:
            self._iniciar()
            if self.player.is_playing():
                self.player.set_pause(1)
                self.boton.configure(text="▶ Continuar")
            else:
                if self.player.play() == -1:
                    raise OSError("No se pudo reproducir este video.")
                self.boton.configure(text="❚❚ Pausar")
                self.estado.configure(text="")
                if self._tarea is None:
                    self._tarea = self.after(300, self._comprobar)
        except (ImportError, OSError, NameError, AttributeError) as error:
            self.estado.configure(text="No se pudo iniciar el video. Comprueba VLC y python-vlc. " + str(error))

    def _comprobar(self):
        self._tarea = None
        if self.player is None:
            return
        estado = str(self.player.get_state())
        if estado.endswith("Error"):
            self.estado.configure(text="No se puede reproducir este archivo de video.")
            self.detener()
        elif estado.endswith("Ended"):
            self.detener()
        else:
            self._tarea = self.after(300, self._comprobar)

    def _volumen(self, valor):
        if self.player is not None:
            self.player.audio_set_volume(int(float(valor)))

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
