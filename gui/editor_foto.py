"""Encuadre circular: las coordenadas del original gobiernan vista y guardado."""

import tkinter as tk
from tkinter import ttk

from gui.imagenes import Image, ImageOps, ImageTk
from gui.estilo import BLANCO, TEXTO


class EditorFoto(tk.Frame):
    LADO = 220

    def __init__(self, padre):
        super().__init__(padre, background=BLANCO)
        self.original = None
        self._tarea = None
        self._arrastre = None
        self.canvas = tk.Canvas(self, width=self.LADO, height=self.LADO,
                                background=BLANCO, highlightthickness=0, cursor="fleur")
        self.canvas.pack()
        self._item = self.canvas.create_image(0, 0, anchor="nw")
        tk.Label(self, text="Arrastra para encuadrar · Rueda para acercar",
                 background=BLANCO, foreground=TEXTO).pack()
        self.zoom = tk.DoubleVar(value=1)
        self.slider = ttk.Scale(self, from_=1, to=4, variable=self.zoom,
                                command=self._cambiar_zoom)
        self.slider.pack(fill="x", padx=25, pady=6)
        self.canvas.bind("<ButtonPress-1>", self._iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self._mover)
        self.canvas.bind("<ButtonRelease-1>", self._soltar)
        for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind(evento, self._rueda)
        self.bind("<Destroy>", self._destruir)

    def cargar(self, ruta):
        if Image is None:
            raise ValueError("El editor de fotos requiere Pillow (requirements.txt).")
        with Image.open(ruta) as imagen:
            imagen.seek(0)
            original = ImageOps.exif_transpose(imagen).convert("RGBA")
        # Los formatos transparentes se componen sobre blanco también al guardar.
        fondo = Image.new("RGBA", original.size, "white")
        self.original = Image.alpha_composite(fondo, original).convert("RGB")
        self.restablecer()

    def restablecer(self):
        if self.original is None:
            return
        self.zoom.set(1)
        self.cx, self.cy = self.original.width / 2, self.original.height / 2
        self._arrastre = None
        self._programar()

    def _caja(self):
        lado = min(self.original.size) / self.zoom.get()
        mitad = lado / 2
        self.cx = max(mitad, min(self.original.width - mitad, self.cx))
        self.cy = max(mitad, min(self.original.height - mitad, self.cy))
        return (self.cx - mitad, self.cy - mitad, self.cx + mitad, self.cy + mitad)

    def recortar(self, lado=512):
        return self.original.resize((lado, lado), Image.Resampling.LANCZOS,
                                    box=self._caja())

    def _cambiar_zoom(self, valor=None):
        if self.original is not None:
            self._caja()
            self._programar()

    def _rueda(self, evento):
        if self.original is not None:
            delta = getattr(evento, "delta", 0)
            numero = getattr(evento, "num", None)
            if delta or numero in (4, 5):
                factor = 1.1 if delta > 0 or numero == 4 else 1 / 1.1
                self.zoom.set(max(1, min(4, self.zoom.get() * factor)))
                self._cambiar_zoom()
        return "break"

    def _iniciar_arrastre(self, evento):
        self._arrastre = (evento.x, evento.y)

    def _mover(self, evento):
        if self.original is None or self._arrastre is None:
            return
        escala = min(self.original.size) / self.zoom.get() / self.LADO
        self.cx -= (evento.x - self._arrastre[0]) * escala
        self.cy -= (evento.y - self._arrastre[1]) * escala
        self._arrastre = (evento.x, evento.y)
        self._caja()
        self._programar()

    def _soltar(self, evento):
        self._arrastre = None

    def _programar(self):
        if self._tarea is None:
            self._tarea = self.after(16, self._dibujar)

    def _dibujar(self):
        from PIL import ImageDraw
        self._tarea = None
        if self.original is None:
            return
        imagen = self.recortar(self.LADO).convert("RGBA")
        mascara = Image.new("L", (self.LADO * 4, self.LADO * 4), 0)
        ImageDraw.Draw(mascara).ellipse((0, 0, mascara.width - 1, mascara.height - 1), fill=255)
        imagen.putalpha(mascara.resize(imagen.size, Image.Resampling.LANCZOS))
        self._foto = ImageTk.PhotoImage(imagen, master=self.canvas)
        self.canvas.itemconfigure(self._item, image=self._foto)

    def limpiar(self):
        if self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
        self.original = None
        self._arrastre = None
        self.canvas.itemconfigure(self._item, image="")
        self._foto = None

    def _destruir(self, evento):
        if evento.widget is self and self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
