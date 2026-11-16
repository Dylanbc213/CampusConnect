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
    elif nombre == "responder":
        dibujo.line([punto(8, 4), punto(3, 9), punto(8, 14)],
                     fill=color, width=ancho, joint="curve")
        dibujo.line([punto(3, 9), punto(12, 9)], fill=color, width=ancho)
        dibujo.arc((punto(6, 9), punto(20, 21)), 270, 360, fill=color, width=ancho)
    elif nombre == "repost":
        dibujo.line([punto(3, 13), punto(3, 5), punto(16, 5)], fill=color, width=ancho, joint="curve")
        dibujo.line([punto(13, 2), punto(16, 5), punto(13, 8)], fill=color, width=ancho, joint="curve")
        dibujo.line([punto(19, 9), punto(19, 17), punto(6, 17)], fill=color, width=ancho, joint="curve")
        dibujo.line([punto(9, 14), punto(6, 17), punto(9, 20)], fill=color, width=ancho, joint="curve")
    elif nombre == "corazon":
        dibujo.polygon([punto(3, 10), punto(11, 19), punto(19, 10)], fill=color)
        dibujo.ellipse((punto(2, 3), punto(12, 13)), fill=color)
        dibujo.ellipse((punto(10, 3), punto(20, 13)), fill=color)
    elif nombre == "sonrisa":
        dibujo.ellipse((punto(2, 2), punto(20, 20)), outline=color, width=ancho)
        for x in (7, 14):
            dibujo.arc((punto(x - 2, 6), punto(x + 2, 10)), 190, 350, fill=color, width=ancho)
        dibujo.arc((punto(6, 8), punto(16, 16)), 0, 180, fill=color, width=ancho)
    else:
        return None
    imagen = imagen.resize((tamano, tamano), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(imagen)
