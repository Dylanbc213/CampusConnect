import tkinter as tk
from tkinter import ttk

ROJO = "#E4002B"
BLANCO = "#FFFFFF"
GRIS = "#F3F4F6"
TEXTO = "#1F2937"


class CampoRedondeado(tk.Frame):
    """Entrada con fondo redondeado y un campo Tk estándar en su interior."""

    def __init__(self, padre, clase, **opciones):
        fondo = padre.cget("background")
        super().__init__(padre, background=fondo, highlightthickness=0, bd=0)
        self.canvas = tk.Canvas(self, background=fondo, highlightthickness=0, bd=0,
                                width=220, height=36)
        self.canvas.pack(fill="both", expand=True)
        self.campo = clase(self.canvas, **opciones)
        self.campo.update_idletasks()
        self.canvas.configure(height=max(36, self.campo.winfo_reqheight() + 8))
        for opcion in ("relief", "borderwidth", "highlightthickness"):
            try:
                self.campo.configure(**{opcion: "flat" if opcion == "relief" else 0})
            except tk.TclError:
                pass
        self.ventana = self.canvas.create_window(4, 4, window=self.campo, anchor="nw")
        self.canvas.bind("<Configure>", self._ajustar)
        self.campo.bind("<FocusIn>", self._foco, add="+")
        self.campo.bind("<FocusOut>", self._foco, add="+")
        self._campus_redibujar_campo = self._dibujar
        self._enfocado = False
        self.after_idle(self._dibujar)

    def _ajustar(self, evento):
        self.canvas.coords(self.ventana, 4, 4)
        self.canvas.itemconfigure(self.ventana, width=max(1, evento.width - 8),
                                  height=max(1, evento.height - 8))
        self._dibujar()

    def _foco(self, evento=None):
        self._enfocado = self.campo.focus_get() == self.campo
        self._dibujar()

    def _dibujar(self):
        try:
            from PIL import Image, ImageDraw, ImageTk
            ancho, alto = max(12, self.canvas.winfo_width()), max(12, self.canvas.winfo_height())
            modo = getattr(self.winfo_toplevel(), "_campus_modo_tema", "claro")
            paleta = TEMAS[modo]
            fondo = self.campo.cget("background")
            fondo_padre = self.master.cget("background")
            borde = paleta["ACENTO"] if self._enfocado else paleta["BORDE"]
            escala = 3
            imagen = Image.new("RGBA", (ancho * escala, alto * escala), fondo_padre)
            dibujo = ImageDraw.Draw(imagen)
            dibujo.rounded_rectangle((0, 0, (ancho - 1) * escala, (alto - 1) * escala),
                                     radius=9 * escala, fill=fondo, outline=borde, width=escala)
            imagen = imagen.resize((ancho, alto), Image.Resampling.LANCZOS)
            self._campus_imagen_campo = ImageTk.PhotoImage(imagen)
            self.canvas.delete("campo")
            self.canvas.create_image(0, 0, image=self._campus_imagen_campo,
                                     anchor="nw", tags="campo")
            self.canvas.tag_lower("campo")
        except (ImportError, tk.TclError, ValueError):
            pass


def crear_campo_redondeado(padre, clase, **opciones):
    marco = CampoRedondeado(padre, clase, **opciones)
    return marco, marco.campo


def preparar(ventana):
    ventana.configure(background=BLANCO)
    ancho = min(1000, ventana.winfo_screenwidth() - 40)
    alto = min(760, ventana.winfo_screenheight() - 80)
    ventana.geometry("{}x{}".format(ancho, alto))
    ventana.minsize(min(640, ancho), min(560, alto))
    ventana.option_add("*Font", "{Segoe UI} 10")
    ventana.option_add("*Background", BLANCO)
    ventana.option_add("*Foreground", TEXTO)
    estilo = ttk.Style(ventana)
    estilo.theme_use("clam")
    estilo.configure("TScrollbar", background=GRIS, troughcolor=BLANCO, borderwidth=0)


def estructura(contenedor, formulario=False):
    contenedor.configure(background=BLANCO, padx=0, pady=0)
    lateral = tk.Frame(contenedor, background=ROJO, padx=16, pady=24)
    lateral.pack(side="left", fill="y")
    tk.Label(lateral, text="Campus\nConnect", background=ROJO, foreground=BLANCO,
             font=("Segoe UI", 20, "bold"), justify="left").pack(anchor="w", pady=(0, 24))
    zona = tk.Frame(contenedor, background=BLANCO, padx=24, pady=16)
    zona.pack(side="left", fill="both", expand=True)
    if formulario:
        zona.columnconfigure(0, weight=1)
        zona.rowconfigure(0, weight=1)
        tarjeta = tk.Frame(zona, background=GRIS, padx=24, pady=16)
        tarjeta.grid(row=0, column=0)
        zona.bind("<Configure>", lambda evento: tarjeta.configure(width=min(440, max(240, evento.width - 48))))
        return lateral, tarjeta
    return lateral, zona


def decorar(contenedor):
    for widget in contenedor.winfo_children():
        clase = widget.winfo_class()
        fondo = contenedor.cget("background")
        if clase == "Label" and fondo != ROJO:
            widget.configure(background=fondo, foreground=TEXTO, font=("Segoe UI", 10))
        elif clase == "Entry":
            widget.configure(font=("Segoe UI", 12), background=BLANCO, foreground=TEXTO,
                             relief="flat", highlightthickness=1, highlightbackground="#D1D5DB",
                             highlightcolor=ROJO, insertbackground=TEXTO, width=28)
        elif clase == "Button":
            widget.configure(background=ROJO, foreground=BLANCO, activebackground="#B80023",
                             activeforeground=BLANCO, disabledforeground="#E5A5B1", relief="flat",
                             borderwidth=0, padx=14, pady=8, cursor="hand2", font=("Segoe UI", 10, "bold"))
            widget.bind("<Enter>", lambda evento: evento.widget.configure(background="#B80023"))
            widget.bind("<Leave>", lambda evento: evento.widget.configure(background=ROJO))
        elif clase == "Listbox":
            widget.configure(background=GRIS, foreground=TEXTO, selectbackground=ROJO,
                             selectforeground=BLANCO, relief="flat", borderwidth=0,
                             highlightthickness=1, highlightbackground=GRIS, font=("Segoe UI", 11))
        elif clase == "Frame":
            decorar(widget)


def encabezado(contenedor, titulo):
    for widget in contenedor.winfo_children():
        if widget.winfo_class() == "Label" and widget.cget("text") == titulo:
            widget.configure(font=("Segoe UI", 22, "bold"), foreground=TEXTO)


TEMAS = {
    "claro": {
        "FONDO": "#FFFFFF", "TARJETA": "#FFFFFF", "SUPERFICIE": "#F3F4F6",
        "CAMPO": "#FAFAFA", "TEXTO": "#1F2937", "SECUNDARIO": "#6B7280",
        "BORDE": "#E5E7EB", "ACENTO": "#E4002B", "ROJO_HOVER": "#B80023",
        "NEUTRO_HOVER": "#E5E7EB", "SELECCION": "#FCE7EC", "ERROR": "#B42318",
        "NAV_SELECCION": "#FFFFFF", "EXITO": "#24663B",
    },
    "oscuro": {
        "FONDO": "#111318", "TARJETA": "#1E2128", "SUPERFICIE": "#1E2128",
        "CAMPO": "#171A20", "TEXTO": "#F9FAFB", "SECUNDARIO": "#AEB4C0",
        "BORDE": "#343943", "ACENTO": "#E4002B", "ROJO_HOVER": "#B80023",
        "NEUTRO_HOVER": "#343943", "SELECCION": "#4A1825", "ERROR": "#FF8A8A",
        "NAV_SELECCION": "#343943", "EXITO": "#7BD99B",
    },
}


def _opcion(widget, nombre):
    try:
        return widget.cget(nombre)
    except (tk.TclError, TypeError):
        return None


def _es_tarjeta(widget, originales):
    borde = (originales.get("highlightbackground") or "").lower()
    grosor = _opcion(widget, "highlightthickness")
    try:
        return int(grosor) > 0 and borde in ("#e5e7eb", "#d1d5db")
    except (TypeError, ValueError):
        return False


def _dibujar_boton_redondeado(widget, color, fondo_padre):
    if widget.winfo_class() != "Button":
        return
    try:
        texto = widget.cget("text")
        icono = getattr(widget, "_campus_imagen", None)
        if icono is not None and texto:
            widget._campus_texto_boton = texto
        elif icono is not None:
            texto = getattr(widget, "_campus_texto_boton", "")
        if not texto and icono is None:
            return
        from PIL import Image, ImageDraw, ImageFont, ImageTk
        import tkinter.font as tkfont
        fuente = tkfont.Font(widget, font=widget.cget("font")) if texto else None
        icono_pil = ImageTk.getimage(icono).convert("RGBA") if icono is not None else None
        if getattr(widget, "_campus_rol", None) == "publicar":
            widget._campus_tamano_boton = (min(max(94, widget.winfo_reqwidth()), 128), 34)
        if not hasattr(widget, "_campus_tamano_boton"):
            widget.update_idletasks()
            ancho_texto = fuente.measure(texto) + 30 if texto else 0
            ancho_icono = icono_pil.width + 28 if icono_pil is not None else 0
            widget._campus_tamano_boton = (
                max(widget.winfo_reqwidth(), ancho_texto, ancho_icono),
                max(34, widget.winfo_reqheight()),
            )
        ancho, alto = widget._campus_tamano_boton
        escala = 4
        imagen = Image.new("RGBA", (ancho * escala, alto * escala), (0, 0, 0, 0))
        dibujo = ImageDraw.Draw(imagen)
        dibujo.rounded_rectangle(
            (1 * escala, 1 * escala, (ancho - 2) * escala, (alto - 2) * escala),
            radius=14 * escala, fill=color, outline=color, width=1 * escala,
        )
        if icono_pil is not None:
            x_icono = (ancho - icono_pil.width) // 2
            y_icono = max(1, (alto - icono_pil.height - (12 if texto else 0)) // 2)
            icono_grande = icono_pil.resize(
                (icono_pil.width * escala, icono_pil.height * escala), Image.Resampling.LANCZOS)
            imagen.alpha_composite(icono_grande, (x_icono * escala, y_icono * escala))
            if texto:
                try:
                    fuente_pil = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 9 * escala)
                except OSError:
                    fuente_pil = ImageFont.load_default(size=9 * escala)
                dibujo.text((ancho * escala / 2, (alto - 5) * escala), texto,
                            anchor="mm", font=fuente_pil, fill=widget.cget("foreground"))
        imagen = imagen.resize((ancho, alto), Image.Resampling.LANCZOS)
        widget._campus_fondo_redondeado = ImageTk.PhotoImage(imagen)
        widget._campus_color_fondo = color
        es_publicar = getattr(widget, "_campus_rol", None) == "publicar"
        opciones = {"image": widget._campus_fondo_redondeado, "compound": "center",
                    "background": color if es_publicar else fondo_padre,
                    "activebackground": color if es_publicar else fondo_padre,
                    "borderwidth": 0, "highlightthickness": 0,
                    "highlightbackground": color if es_publicar else fondo_padre,
                    "highlightcolor": color if es_publicar else fondo_padre,
                    "width": ancho, "height": alto}
        if es_publicar:
            opciones.update({"padx": 12, "pady": 0, "justify": "center"})
        if icono is not None:
            opciones["text"] = ""
        widget.configure(**opciones)
    except (ImportError, tk.TclError, ValueError, TypeError):
        pass


def aplicar_tema(widget, modo):
    """Pinta en sitio un ?rbol Tk completo, conservando sus valores base."""
    modo = modo if modo in TEMAS else "claro"
    paleta = TEMAS[modo]
    try:
        raiz = widget.winfo_toplevel()
        raiz._campus_modo_tema = modo
    except (tk.TclError, AttributeError):
        raiz = None

    fondo_inicial = None
    if widget is not raiz:
        try:
            fondo_inicial = widget.master.cget("background")
        except (tk.TclError, AttributeError):
            pass

    def pintar(actual, fondo_padre=None):
        if not hasattr(actual, "_campus_colores_base"):
            actual._campus_colores_base = {
                nombre: (str(_opcion(actual, nombre)) if _opcion(actual, nombre) is not None else None)
                for nombre in ("background", "foreground", "highlightbackground", "highlightcolor",
                               "insertbackground", "selectbackground", "selectforeground",
                               "disabledforeground", "activebackground", "activeforeground")
            }
        base = actual._campus_colores_base
        clase = actual.winfo_class()
        fondo_base = (base.get("background") or "").lower()
        frente_base = (base.get("foreground") or "").lower()
        parent_bg = fondo_padre or paleta["FONDO"]

        if clase in ("Tk", "Toplevel"):
            fondo = paleta["FONDO"]
        elif clase in ("Entry", "Text", "Listbox"):
            fondo = (paleta["CAMPO"] if modo == "oscuro" else
                     ("#FAFAFA" if fondo_base == "#fafafa" else paleta["SUPERFICIE"]))
        elif fondo_base in ("#f3f4f6", "#f5f5f5"):
            fondo = paleta["SUPERFICIE"]
        elif fondo_base == "#fafafa":
            fondo = paleta["CAMPO"]
        elif fondo_base == "#0b141a":
            fondo = paleta["FONDO"] if modo == "claro" else "#0B141A"
        elif fondo_base in ("#e5e7eb", "#d1d5db"):
            fondo = paleta["NEUTRO_HOVER"] if clase == "Button" else paleta["SUPERFICIE"]
        elif fondo_base == "#fce7ec":
            fondo = paleta["SELECCION"]
        elif fondo_base in ("#e4002b", "#b80023"):
            fondo = fondo_base
        elif fondo_base in ("#ffffff", "#fff", ""):
            fondo = paleta["TARJETA"] if _es_tarjeta(actual, base) else parent_bg
        else:
            fondo = base.get("background") or parent_bg

        if clase == "Button" and fondo_base in ("#ffffff", "#fff"):
            fondo = paleta["TARJETA"] if _es_tarjeta(actual, base) else parent_bg
        if frente_base in ("#1f2937", "#111827", "#000000", "#000"):
            frente = paleta["TEXTO"]
        elif frente_base in ("#6b7280", "#555555", "#374151"):
            frente = paleta["SECUNDARIO"]
        elif frente_base == "#b42318":
            frente = paleta["ERROR"]
        elif frente_base == "#24663b":
            frente = paleta["EXITO"]
        elif frente_base in ("#ffffff", "#fff"):
            frente = ("#FFFFFF" if fondo_base in ("#e4002b", "#b80023")
                      else paleta["TEXTO"])
        else:
            frente = base.get("foreground")

        if getattr(actual, "_campus_rol", None) == "publicar":
            fondo = "#E4002B"
            frente = "#FFFFFF"
        elif getattr(actual, "_campus_rol", None) in ("texto_publicacion", "texto_mensaje"):
            frente = "#FFFFFF" if modo == "oscuro" else "#000000"
        elif getattr(actual, "_campus_rol", None) == "reaccion":
            seleccionado = getattr(actual, "_campus_seleccionado", False)
            fondo = parent_bg
            frente = paleta["ACENTO"] if seleccionado else paleta["SECUNDARIO"]
        elif getattr(actual, "_campus_rol", None) == "navegacion":
            seleccionado = getattr(actual, "_campus_seleccionado", False)
            fondo = (paleta["NAV_SELECCION"] if seleccionado else paleta["ACENTO"])
            frente = paleta["ACENTO"] if seleccionado else "#FFFFFF"
        elif getattr(actual, "_campus_rol", None) == "tema":
            fondo = paleta["SUPERFICIE"]
            frente = "#FFFFFF" if modo == "oscuro" else paleta["TEXTO"]
        elif getattr(actual, "_campus_rol", None) in ("actualizar", "icono", "avatar"):
            fondo = parent_bg
            frente = paleta["TEXTO"]

        opciones = {}
        if _opcion(actual, "background") is not None:
            opciones["background"] = fondo
        if _opcion(actual, "foreground") is not None and frente:
            opciones["foreground"] = frente
        if _opcion(actual, "highlightbackground") is not None:
            opciones["highlightbackground"] = paleta["BORDE"]
        if _opcion(actual, "highlightcolor") is not None:
            opciones["highlightcolor"] = paleta["ACENTO"]
        if _opcion(actual, "insertbackground") is not None:
            opciones["insertbackground"] = paleta["TEXTO"]
        if _opcion(actual, "selectbackground") is not None:
            opciones["selectbackground"] = paleta["ACENTO"]
        if _opcion(actual, "selectforeground") is not None:
            opciones["selectforeground"] = "#FFFFFF"
        if _opcion(actual, "activebackground") is not None:
            opciones["activebackground"] = (paleta["ROJO_HOVER"] if fondo_base == "#e4002b"
                                                else paleta["NEUTRO_HOVER"])
        if _opcion(actual, "activeforeground") is not None:
            opciones["activeforeground"] = frente or paleta["TEXTO"]
        if clase == "Button":
            actual._campus_reposo = (fondo, frente)
            if getattr(actual, "_campus_seleccionado", False):
                opciones["activebackground"] = fondo
            opciones["highlightthickness"] = 0
        if getattr(actual, "_campus_icono", None):
            from gui.iconos import crear_icono
            actual._campus_imagen = crear_icono(actual._campus_icono, color=frente)
            if actual._campus_imagen is not None:
                opciones["image"] = actual._campus_imagen
            if getattr(actual, "_campus_contador_neutro", False):
                opciones["foreground"] = paleta["SECUNDARIO"]
                opciones["activeforeground"] = paleta["SECUNDARIO"]
                actual._campus_reposo = (fondo, paleta["SECUNDARIO"])
        try:
            if opciones:
                actual.configure(**opciones)
            if clase == "Button":
                _dibujar_boton_redondeado(actual, fondo, parent_bg)
        except tk.TclError:
            pass

        if clase == "Button":
            actual.bind("<Enter>", lambda evento: _hover(evento.widget), add="")
            actual.bind("<Leave>", lambda evento: _salir_hover(evento.widget), add="")
        if clase == "Text":
            try:
                for etiqueta in actual.tag_names():
                    base_tag = getattr(actual, "_campus_tags_base", {})
                    if etiqueta not in base_tag:
                        base_tag[etiqueta] = {
                            clave: actual.tag_cget(etiqueta, clave)
                            for clave in ("background", "foreground")
                        }
                    actual._campus_tags_base = base_tag
                    fondo_tag = base_tag[etiqueta]["background"]
                    frente_tag = base_tag[etiqueta]["foreground"]
                    if fondo_tag:
                        actual.tag_configure(etiqueta, background=(paleta["SUPERFICIE"]
                                           if fondo_tag.lower() in ("#f3f4f6", "#f5f5f5")
                                           else fondo if fondo_tag.lower() in ("#ffffff", "#fff") else fondo_tag))
                    if frente_tag:
                        actual.tag_configure(etiqueta, foreground=(paleta["TEXTO"]
                                           if frente_tag.lower() in ("#1f2937", "#000000") else frente_tag))
            except tk.TclError:
                pass

        bg_hijo = fondo if clase in ("Frame", "Tk", "Toplevel", "Canvas", "Labelframe") else parent_bg
        try:
            hijos = actual.winfo_children()
        except tk.TclError:
            hijos = []
        for hijo in hijos:
            pintar(hijo, bg_hijo)
        redibujar_campo = getattr(actual, "_campus_redibujar_campo", None)
        if callable(redibujar_campo):
            redibujar_campo()

    pintar(widget, fondo_inicial)
    try:
        from tkinter import ttk
        estilo = ttk.Style(raiz or widget)
        estilo.configure("TScrollbar", background=paleta["SUPERFICIE"],
                         troughcolor=paleta["FONDO"], bordercolor=paleta["BORDE"],
                         arrowcolor=paleta["SECUNDARIO"])
    except tk.TclError:
        pass


def _hover(widget):
    base = getattr(widget, "_campus_colores_base", {})
    modo = getattr(widget.winfo_toplevel(), "_campus_modo_tema", "claro")
    paleta = TEMAS[modo]
    if getattr(widget, "_campus_rol", None) == "tema":
        frente = "#FFFFFF" if modo == "oscuro" else paleta["TEXTO"]
        fondo_padre = widget.master.cget("background")
        widget.configure(foreground=frente)
        _dibujar_boton_redondeado(widget, paleta["SUPERFICIE"], fondo_padre)
        return
    if getattr(widget, "_campus_rol", None) == "publicar":
        widget.configure(background="#E4002B", activebackground="#B80023", foreground="#FFFFFF",
                        activeforeground="#FFFFFF", highlightthickness=0,
                        highlightbackground="#E4002B", highlightcolor="#E4002B", borderwidth=0,
                        padx=12, pady=0)
        _dibujar_boton_redondeado(widget, "#E4002B", widget.master.cget("background"))
        return
    if getattr(widget, "_campus_rol", None) in ("actualizar", "icono"):
        widget.configure(foreground=paleta["TEXTO"])
        if getattr(widget, "_campus_icono", None):
            from gui.iconos import crear_icono
            widget._campus_imagen = crear_icono(widget._campus_icono, color=paleta["TEXTO"])
        try:
            _dibujar_boton_redondeado(widget, paleta["NEUTRO_HOVER"], widget.master.cget("background"))
        except tk.TclError:
            pass
        return
    if getattr(widget, "_campus_rol", None) in ("reaccion", "navegacion") and getattr(
            widget, "_campus_seleccionado", False):
        return
    fondo = (paleta["ROJO_HOVER"] if (base.get("background") or "").lower() == "#e4002b"
             else paleta["NEUTRO_HOVER"])
    try:
        fondo_padre = widget.master.cget("background")
        widget.configure(foreground=widget.cget("foreground"))
        _dibujar_boton_redondeado(widget, fondo, fondo_padre)
    except tk.TclError:
        pass


def _salir_hover(widget):
    reposo = getattr(widget, '_campus_reposo', None)
    if getattr(widget, "_campus_rol", None) == "publicar":
        widget.configure(background="#E4002B", activebackground="#B80023", foreground="#FFFFFF",
                        activeforeground="#FFFFFF", highlightthickness=0,
                        highlightbackground="#E4002B", highlightcolor="#E4002B", borderwidth=0,
                        padx=12, pady=0)
        _dibujar_boton_redondeado(widget, "#E4002B", widget.master.cget("background"))
        return
    if reposo:
        try:
            fondo_padre = widget.master.cget("background")
        except tk.TclError:
            fondo_padre = reposo[0]
        widget.configure(foreground=reposo[1])
        _dibujar_boton_redondeado(widget, reposo[0], fondo_padre)


def aplicar_tema_actual(widget):
    """Aplica el tema activo de su ventana a un sub?rbol reci?n creado."""
    try:
        raiz = widget.winfo_toplevel()
        aplicar_tema(widget, getattr(raiz, "_campus_modo_tema", "claro"))
    except tk.TclError:
        pass
