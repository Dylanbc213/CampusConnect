import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText


class VentanaMuro:
    def __init__(self, contenedor, aplicacion, usuario):
        self.aplicacion = aplicacion
        self.usuario = usuario
        # Al destruir el panel (cerrar sesión), también se cierra este muro.
        self.ventana = tk.Toplevel(contenedor)
        self.ventana.title("Publicaciones y muros")
        self.ventana.geometry("600x650")
        tk.Label(self.ventana, text="Nueva publicación").pack()
        self.campo_contenido = ScrolledText(self.ventana, height=3, wrap="word")
        self.campo_contenido.pack(fill="x", padx=10)
        tk.Button(self.ventana, text="Publicar", command=self._publicar).pack(pady=4)
        tk.Button(self.ventana, text="Actualizar muros", command=self._actualizar).pack(pady=4)
        tk.Label(self.ventana, text="Mi muro").pack()
        self.muro_personal = ScrolledText(self.ventana, height=8, wrap="word", state="disabled")
        self.muro_personal.pack(fill="both", expand=True, padx=10, pady=4)
        tk.Label(self.ventana, text="Muro de amigos").pack()
        self.muro_amigos = ScrolledText(self.ventana, height=8, wrap="word", state="disabled")
        self.muro_amigos.pack(fill="both", expand=True, padx=10, pady=4)
        self._actualizar()

    def _publicar(self):
        try:
            self.aplicacion.gestor_publicaciones.crear_publicacion(
                self.usuario.nombre_usuario, self.campo_contenido.get("1.0", "end-1c"),
            )
        except ValueError as error:
            messagebox.showerror("Publicaciones", str(error), parent=self.ventana)
            return
        except OSError:
            messagebox.showerror("Publicaciones", "No se pudo guardar la publicación. Inténtalo de nuevo.",
                                 parent=self.ventana)
            return
        self.campo_contenido.delete("1.0", tk.END)
        self._actualizar()
        messagebox.showinfo("Publicaciones", "Publicación creada correctamente.", parent=self.ventana)

    def _actualizar(self):
        gestor = self.aplicacion.gestor_publicaciones
        self._mostrar(self.muro_personal, gestor.obtener_publicaciones_usuario(self.usuario.nombre_usuario))
        self._mostrar(self.muro_amigos, gestor.obtener_publicaciones_amigos(
            self.usuario.nombre_usuario, self.aplicacion.gestor_amistades,
        ))

    def _mostrar(self, muro, publicaciones):
        muro.configure(state="normal")
        muro.delete("1.0", tk.END)
        if not publicaciones:
            muro.insert(tk.END, "No hay publicaciones.\n")
        for publicacion in publicaciones:
            autor = self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(publicacion.nombre_usuario)
            nombre = "{} (@{})".format(autor.nombre, autor.nombre_usuario) if autor else publicacion.nombre_usuario
            muro.insert(tk.END, "{} | {}\n{}\n\n".format(nombre, publicacion.fecha, publicacion.contenido))
        muro.configure(state="disabled")
