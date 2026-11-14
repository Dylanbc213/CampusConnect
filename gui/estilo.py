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
