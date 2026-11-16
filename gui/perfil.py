"""Vista de perfiles públicos y edición del perfil propio."""

import os
import tkinter as tk
import uuid
from tkinter import filedialog, messagebox

from gui.estilo import BLANCO, GRIS, ROJO, TEXTO, aplicar_tema_actual, crear_campo_redondeado
from gui.lista_publicaciones import ListaPublicaciones
from gui.avatar import dibujar_avatar
from gui.editor_foto import EditorFoto
from gui.imagenes import validar_imagen


class Perfil(tk.Frame):
    def __init__(self, padre, aplicacion, propietario, abrir_perfil, al_volver=None, al_actualizar=None):
        super().__init__(padre, background=BLANCO, padx=28, pady=20)
        self.aplicacion = aplicacion
        self.propietario = propietario
        self.abrir_perfil = abrir_perfil
        self.al_volver = al_volver
        self.al_actualizar = al_actualizar
        self.usuario = propietario
        self.imagen = None
        self.ruta_foto = propietario.foto_perfil
        self.foto_pendiente = None
        self._construir()

    def _construir(self):
        self.tarjeta = tk.Frame(self, background=BLANCO, padx=24, pady=20,
                                highlightbackground="#E5E7EB", highlightthickness=1)
        self.tarjeta.pack(fill="both", expand=True)
        barra = tk.Frame(self.tarjeta, background=BLANCO)
        barra.pack(fill="x")
        if self.al_volver:
            tk.Button(barra, text="‹ Volver", command=self.al_volver, background=BLANCO,
                      foreground=ROJO, activeforeground=ROJO, relief="flat", borderwidth=0,
                      cursor="hand2", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.avatar = tk.Canvas(self.tarjeta, width=120, height=120, background=BLANCO,
                                highlightthickness=0)
        self.avatar.pack(anchor="center", pady=(8, 12))
        barra_nombre = tk.Frame(self.tarjeta, background=BLANCO)
        barra_nombre.pack(pady=(0, 2))
        self.nombre = tk.Label(barra_nombre, text="", background=BLANCO,
                               foreground=TEXTO, font=("Segoe UI", 20, "bold"))
        self.nombre.pack(side="left", padx=(0, 12))
        self.boton_editar = tk.Button(
            barra_nombre, text="Editar perfil", command=self._editar,
            background=ROJO, foreground=BLANCO, activebackground="#B80023",
            activeforeground=BLANCO, relief="flat", borderwidth=0,
            padx=13, pady=7, cursor="hand2", font=("Segoe UI", 9, "bold"),
        )
        self.usuario_label = tk.Label(self.tarjeta, text="", background=BLANCO,
                                      foreground="#6B7280", font=("Segoe UI", 11))
        self.usuario_label.pack_forget()
        self.bio = tk.Label(self.tarjeta, text="", background=BLANCO, foreground=TEXTO,
                            wraplength=560, justify="center")
        self.bio.pack(pady=8)
        self.contadores = tk.Label(self.tarjeta, text="", background=BLANCO,
                                   foreground=TEXTO, font=("Segoe UI", 11, "bold"))
        self.contadores.pack(pady=8)
        self.estado = tk.Label(self.tarjeta, text="", background=BLANCO,
                               foreground="#6B7280")
        self.estado.pack(pady=3)
        self.accion_amistad = tk.Button(self.tarjeta, text="Agregar amigo", command=self._agregar_amigo)
        self.accion_amistad.pack(pady=4)
        self.boton_mensaje = tk.Button(self.tarjeta, text="Mensaje", background=ROJO,
                                      foreground=BLANCO, relief="flat", cursor="hand2",
                                      command=lambda: self.abrir_chat(self.usuario.nombre_usuario))
        self.editor = tk.Frame(self.tarjeta, background=BLANCO)
        tk.Label(self.editor, text="Nombre visible", background=BLANCO).pack(anchor="w", pady=(10, 2))
        self.marco_campo_nombre, self.campo_nombre = crear_campo_redondeado(self.editor, tk.Entry)
        self.marco_campo_nombre.pack(fill="x")
        tk.Label(self.editor, text="Biografía (máximo 150 caracteres)", background=BLANCO).pack(anchor="w", pady=(10, 2))
        self.marco_campo_bio, self.campo_bio = crear_campo_redondeado(
            self.editor, tk.Text, height=4, wrap="word")
        self.marco_campo_bio.pack(fill="x")
        self.campo_bio.bind("<KeyRelease>", self._contar_bio)
        self.contador_bio = tk.Label(self.editor, text="0 / 150", background=BLANCO, foreground="#6B7280")
        self.contador_bio.pack(anchor="e")
        self.boton_elegir_foto = tk.Button(
            self.editor, text="Cambiar foto", command=self._elegir_foto,
            background=ROJO, foreground=BLANCO, activebackground="#B80023",
            activeforeground=BLANCO, relief="flat", borderwidth=0,
            padx=14, pady=8, cursor="hand2", font=("Segoe UI", 10, "bold"),
        )
        self.boton_elegir_foto.pack(side="left", pady=8)
        self.foto_estado = tk.Label(self.editor, text="Sin foto", background=BLANCO, foreground="#6B7280")
        self.foto_estado.pack(side="left", padx=8)
        self.vista_foto_frame = tk.Frame(self.tarjeta, background=BLANCO)
        self.vista_foto = EditorFoto(self.vista_foto_frame)
        self.vista_foto.pack(pady=(8, 4))
        fila_foto = tk.Frame(self.vista_foto_frame, background=BLANCO)
        fila_foto.pack()
        tk.Button(fila_foto, text="Restablecer", command=self.vista_foto.restablecer,
                  background="#E5E7EB", foreground=TEXTO, relief="flat",
                  padx=14, pady=8, cursor="hand2").pack(side="left", padx=4)
        self.boton_guardar_foto = tk.Button(
            fila_foto, text="Guardar foto", command=self._guardar_foto,
            background=ROJO, foreground=BLANCO, activebackground="#B80023",
            activeforeground=BLANCO, relief="flat", borderwidth=0,
            padx=14, pady=8, cursor="hand2", font=("Segoe UI", 10, "bold"),
        )
        self.boton_guardar_foto.pack(side="left", padx=4)
        self.boton_cancelar_foto = tk.Button(
            fila_foto, text="Cancelar", command=self._cancelar_foto,
            background="#E5E7EB", foreground=TEXTO, relief="flat", borderwidth=0,
            padx=14, pady=8, cursor="hand2",
        )
        self.boton_cancelar_foto.pack(side="left", padx=4)
        self.vista_foto_frame.pack_forget()
        acciones_editor = tk.Frame(self.editor, background=BLANCO)
        acciones_editor.pack(fill="x", pady=8)
        tk.Button(acciones_editor, text="Cancelar", command=self._cancelar,
                  background="#E5E7EB", foreground=TEXTO, relief="flat", borderwidth=0,
                  padx=14, pady=8, cursor="hand2").pack(side="right", padx=(8, 0))
        self.boton_guardar = tk.Button(acciones_editor, text="Guardar cambios", command=self._guardar,
                                      background=ROJO, foreground=BLANCO, activebackground="#B80023",
                                      activeforeground=BLANCO, relief="flat", borderwidth=0,
                                      padx=14, pady=8, cursor="hand2")
        self.boton_guardar.pack(side="right")
        self.estado_edicion = tk.Label(self.tarjeta, text="", background=BLANCO, foreground="#24663b")
        self.estado_edicion.pack(anchor="e", pady=(2, 0))
        self.publicaciones_titulo = tk.Label(self.tarjeta, text="Publicaciones", background=BLANCO,
                                             foreground=TEXTO, font=("Segoe UI", 14, "bold"))
        self.publicaciones_titulo.pack(anchor="w", pady=(20, 5))
        self.publicaciones = ListaPublicaciones(
            self.tarjeta, self.aplicacion, self.propietario, self.abrir_perfil,
        )
        self.publicaciones.pack(fill="both", expand=True)
        self.mostrar(self.propietario)

    def mostrar(self, usuario):
        if self.foto_pendiente:
            self._cancelar_foto()
        self.usuario = usuario
        propio = usuario is self.propietario
        amigos = self.aplicacion.gestor_amistades.obtener_amistades(self.propietario.nombre_usuario)
        self.boton_mensaje.pack_forget()
        if usuario.nombre_usuario in amigos and hasattr(self, "abrir_chat"):
            self.boton_mensaje.pack(pady=4, before=self.estado_edicion)
        amigos_objetivo = self.aplicacion.gestor_amistades.obtener_amistades(usuario.nombre_usuario)
        self.nombre.configure(text="@" + usuario.nombre_usuario)
        self.usuario_label.configure(text="")
        self.bio.configure(text=usuario.biografia or "Sin biografía.")
        posts = self.aplicacion.gestor_publicaciones.obtener_publicaciones_usuario(usuario.nombre_usuario)
        self.contadores.configure(text="{} amigos     ·     {} publicaciones".format(len(amigos_objetivo), len(posts)))
        if propio:
            self.estado.configure(text="Este es tu perfil")
            self.accion_amistad.pack_forget()
            self.boton_editar.pack(side="left")
            if self.editor.winfo_manager():
                self._cargar_formulario()
        else:
            self.estado_edicion.configure(text="")
            self.boton_editar.pack_forget()
            self.editor.pack_forget()
            self.estado.configure(text="Amigos" if usuario.nombre_usuario in amigos else "Aún no son amigos")
            if usuario.nombre_usuario in amigos:
                self.accion_amistad.configure(text="Ya son amigos", state="disabled")
            else:
                solicitud = self.aplicacion.gestor_amistades.estado_solicitud(
                    self.propietario.nombre_usuario, usuario.nombre_usuario)
                self.accion_amistad.configure(
                    text="Solicitud enviada" if solicitud == "enviada" else
                         "Aceptar solicitud" if solicitud == "recibida" else "Enviar solicitud",
                    state="disabled" if solicitud == "enviada" else "normal")
            self.accion_amistad.pack(pady=4)
        self._mostrar_avatar(usuario)
        self.publicaciones.mostrar(posts, "Aún no hay publicaciones.")
        aplicar_tema_actual(self)

    def _cargar_formulario(self):
        self.campo_nombre.delete(0, tk.END)
        self.campo_nombre.insert(0, self.propietario.nombre_visible)
        self.campo_bio.delete("1.0", tk.END)
        self.campo_bio.insert("1.0", self.propietario.biografia)
        self.foto_pendiente = None
        self.vista_foto.limpiar()
        self.vista_foto_frame.pack_forget()
        self.foto_estado.configure(text=os.path.basename(self.ruta_foto) if self.ruta_foto else "Sin foto")
        self._contar_bio()

    def _editar(self):
        if self.usuario is not self.propietario:
            return
        self.estado_edicion.configure(text="")
        self._cargar_formulario()
        self.boton_editar.pack_forget()
        self.publicaciones_titulo.pack_forget()
        self.publicaciones.pack_forget()
        self.editor.pack(fill="x", pady=8)

    def _cancelar(self):
        self.foto_pendiente = None
        self._cargar_formulario()
        self.editor.pack_forget()
        self.boton_editar.pack(side="left")
        self._mostrar_publicaciones()
        self.estado_edicion.configure(text="")

    def _mostrar_publicaciones(self):
        self.publicaciones_titulo.pack(anchor="w", pady=(20, 5))
        self.publicaciones.pack(fill="both", expand=True)

    def _mostrar_avatar(self, usuario):
        self.avatar.delete("all")
        dibujar_avatar(self.avatar, usuario,
                       os.path.dirname(self.aplicacion.gestor_usuarios.ruta_archivo), 120)

    def _contar_bio(self, evento=None):
        cuenta = len(self.campo_bio.get("1.0", "end-1c"))
        self.contador_bio.configure(text="{} / 150".format(cuenta), foreground=ROJO if cuenta > 150 else "#6B7280")

    def _elegir_foto(self):
        origen = filedialog.askopenfilename(parent=self, filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp *.gif")])
        if not origen:
            return
        try:
            validar_imagen(origen)
            self.vista_foto.cargar(origen)
            self.foto_pendiente = origen
            self.foto_estado.configure(text=os.path.basename(origen))
            self.editor.pack_forget()
            self.vista_foto_frame.pack(fill="x", pady=(2, 8), before=self.estado_edicion)
            aplicar_tema_actual(self.vista_foto_frame)
        except (OSError, ValueError) as error:
            messagebox.showerror("Foto de perfil", str(error), parent=self)

    def _cancelar_foto(self):
        self.foto_pendiente = None
        self.vista_foto.limpiar()
        self.vista_foto_frame.pack_forget()
        self.editor.pack(fill="x", pady=8, before=self.estado_edicion)
        self.foto_estado.configure(text=os.path.basename(self.ruta_foto) if self.ruta_foto else "Sin foto")

    def _guardar_foto(self):
        if self.usuario is not self.propietario:
            return
        if not self.foto_pendiente:
            return
        nombre_borrador = self.campo_nombre.get()
        bio_borrador = self.campo_bio.get("1.0", "end-1c")
        try:
            self._persistir_foto(self.propietario.nombre_visible, self.propietario.biografia)
        except (OSError, ValueError) as error:
            messagebox.showerror("Mi perfil", str(error), parent=self)
            return
        self.campo_nombre.delete(0, tk.END)
        self.campo_nombre.insert(0, nombre_borrador)
        self.campo_bio.delete("1.0", tk.END)
        self.campo_bio.insert("1.0", bio_borrador)
        self.estado_edicion.configure(text="Foto guardada correctamente.", foreground="#24663b")
        self.publicaciones.mostrar(
            self.aplicacion.gestor_publicaciones.obtener_publicaciones_usuario(
                self.propietario.nombre_usuario),
            "Aún no hay publicaciones.",
        )
        if self.al_actualizar:
            self.al_actualizar()

    def _persistir_foto(self, nombre, biografia):
        carpeta = os.path.join(os.path.dirname(self.aplicacion.gestor_usuarios.ruta_archivo), "avatares")
        os.makedirs(carpeta, exist_ok=True)
        archivo = "{}_{}.png".format(self.propietario.nombre_usuario, uuid.uuid4().hex)
        destino = os.path.join(carpeta, archivo)
        relativa = "avatares/" + archivo
        try:
            self.vista_foto.recortar().save(destino, format="PNG")
            self.aplicacion.gestor_usuarios.actualizar_perfil(
                self.propietario, self.propietario, nombre, biografia, relativa,
            )
        except Exception:
            if os.path.exists(destino):
                os.remove(destino)
            raise
        self.ruta_foto = relativa
        self._cancelar_foto()
        self.foto_estado.configure(text=os.path.basename(relativa))
        self._mostrar_avatar(self.propietario)
        return relativa

    def _guardar(self):
        foto_final = self.ruta_foto
        try:
            if self.usuario is not self.propietario:
                raise PermissionError("Solo puedes editar tu propio perfil.")
            if not self.campo_nombre.get().strip():
                raise ValueError("El nombre visible es obligatorio.")
            biografia = self.campo_bio.get("1.0", "end-1c")
            if len(biografia) > 150:
                raise ValueError("La biografía no puede superar los 150 caracteres.")
            if self.foto_pendiente:
                foto_final = self._persistir_foto(self.campo_nombre.get(), biografia)
            else:
                self.aplicacion.gestor_usuarios.actualizar_perfil(
                    self.propietario, self.propietario, self.campo_nombre.get(), biografia, foto_final,
                )
        except (ValueError, PermissionError, OSError) as error:
            self.estado_edicion.configure(text="No se guardaron los cambios.", foreground=ROJO)
            messagebox.showerror("Mi perfil", str(error), parent=self)
            return
        self.ruta_foto = foto_final
        self.foto_pendiente = None
        self.mostrar(self.propietario)
        self.editor.pack_forget()
        self.boton_editar.pack(side="left")
        self._mostrar_publicaciones()
        self.estado_edicion.configure(text="Cambios guardados correctamente.", foreground="#24663b")
        if self.al_actualizar:
            self.al_actualizar()

    def _agregar_amigo(self):
        try:
            gestor = self.aplicacion.gestor_amistades
            accion = (gestor.aceptar_solicitud if gestor.estado_solicitud(
                self.propietario.nombre_usuario, self.usuario.nombre_usuario) == "recibida"
                else gestor.agregar_amistad)
            accion(
                self.propietario.nombre_usuario, self.usuario.nombre_usuario)
        except (ValueError, OSError) as error:
            messagebox.showerror("Amistades", str(error), parent=self)
            return
        self.mostrar(self.usuario)
        if self.al_actualizar:
            self.al_actualizar()
