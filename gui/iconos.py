"""Iconos vectoriales pequeños dibujados en memoria para Tkinter."""

try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    Image = ImageDraw = ImageTk = None


def crear_icono(nombre, color="#FFFFFF", tamano=22):
    if Image is None:
        return None
    escala = 4
    lado = tamano * escala
    imagen = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)

    def punto(x, y):
        return (int(x * escala), int(y * escala))

    ancho = max(1, escala * 2)
    if nombre == "enviar":
        dibujo.line([punto(3, 11), punto(20, 3), punto(15, 20), punto(10, 13),
                     punto(3, 11)], fill=color, width=ancho, joint="curve")
        dibujo.line([punto(10, 13), punto(20, 3)], fill=color, width=ancho)
    elif nombre == "imagen":
        dibujo.rounded_rectangle((punto(3, 4), punto(20, 19)), radius=escala * 2,
                                 outline=color, width=ancho)
        dibujo.ellipse((punto(7, 7), punto(10, 10)), outline=color, width=ancho)
        dibujo.line([punto(5, 17), punto(10, 12), punto(13, 15), punto(16, 11),
                     punto(19, 15)], fill=color, width=ancho, joint="curve")
    else:
        return None
    imagen = imagen.resize((tamano, tamano), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(imagen)
