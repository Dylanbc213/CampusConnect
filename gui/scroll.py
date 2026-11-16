"""Bindings de rueda limitados a los widgets de una lista desplazable."""

def enlazar_rueda_descendientes(raiz, accion):
    pendientes = [raiz]
    while pendientes:
        widget = pendientes.pop()
        widget.bind("<MouseWheel>", accion, add="+")
        widget.bind("<Button-4>", accion, add="+")
        widget.bind("<Button-5>", accion, add="+")
        pendientes.extend(widget.winfo_children())
