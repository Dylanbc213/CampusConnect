import tkinter as tk
from tkinter import ttk

ROJO = "#E4002B"
BLANCO = "#FFFFFF"
GRIS = "#F3F4F6"
TEXTO = "#1F2937"


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

        if getattr(actual, "_campus_rol", None) == "reaccion":
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
        widget.configure(background=paleta["SUPERFICIE"],
                         foreground="#FFFFFF" if modo == "oscuro" else paleta["TEXTO"])
        return
    if getattr(widget, "_campus_rol", None) in ("actualizar", "icono"):
        widget.configure(background=paleta["NEUTRO_HOVER"], foreground=paleta["TEXTO"])
        return
    if getattr(widget, "_campus_rol", None) in ("reaccion", "navegacion") and getattr(
            widget, "_campus_seleccionado", False):
        return
    fondo = (paleta["ROJO_HOVER"] if (base.get("background") or "").lower() == "#e4002b"
             else paleta["NEUTRO_HOVER"])
    try:
        widget.configure(background=fondo)
    except tk.TclError:
        pass


def _salir_hover(widget):
    reposo = getattr(widget, '_campus_reposo', None)
    if reposo:
        widget.configure(background=reposo[0], foreground=reposo[1])


def aplicar_tema_actual(widget):
    """Aplica el tema activo de su ventana a un sub?rbol reci?n creado."""
    try:
        raiz = widget.winfo_toplevel()
        aplicar_tema(widget, getattr(raiz, "_campus_modo_tema", "claro"))
    except tk.TclError:
        pass
