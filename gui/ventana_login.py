"""Formulario básico de inicio de sesión."""

import tkinter as tk
from tkinter import messagebox


class VentanaLogin:
    """Muestra el formulario para acceder a una cuenta existente."""


    def __init__(self, contenedor, aplicacion):
        """Construye los campos y conecta la validación con el gestor de usuarios."""
        blanco, rojo, gris, texto = "#FFFFFF", "#E4002B", "#F3F4F6", "#1F2937"
        contenedor.configure(background=blanco)
        self.vista = tk.Frame(contenedor, background=blanco)
        self.vista.pack(fill="both", expand=True)

        barra_superior = tk.Frame(self.vista, background=blanco)
        barra_superior.pack(fill="x", padx=30, pady=(20, 0))
        self.boton_volver = tk.Button(
            barra_superior, text="← Volver", command=lambda: aplicacion.mostrar_vista("inicio"),
            background=blanco, foreground=texto, activebackground=gris, activeforeground=texto,
            relief="flat", borderwidth=0, padx=9, pady=5, cursor="hand2",
            font=("Segoe UI", 9),
        )
        self.boton_volver.pack(side="left")
        self.boton_volver.bind("<Enter>", lambda evento: evento.widget.configure(background=gris))
        self.boton_volver.bind("<Leave>", lambda evento: evento.widget.configure(background=blanco))

        zona = tk.Frame(self.vista, background=blanco)
        zona.pack(fill="both", expand=True)
        zona.grid_rowconfigure(0, weight=1)
        zona.grid_columnconfigure(0, weight=1)
        self.tarjeta = tk.Frame(zona, background=blanco, padx=38, pady=28,
                                highlightbackground="#E5E7EB", highlightthickness=1)
        self.tarjeta.grid(row=0, column=0, padx=24, pady=18)

        tk.Label(self.tarjeta, text="Iniciar sesión", background=blanco, foreground=texto,
                 font=("Segoe UI", 22, "bold")).pack(pady=(4, 22))

        tk.Label(self.tarjeta, text="Nombre de usuario", background=blanco, foreground=texto,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.campo_usuario = tk.Entry(
            self.tarjeta, relief="flat", background="#FAFAFA", foreground=texto,
            insertbackground=texto, highlightthickness=1, highlightbackground="#D1D5DB",
            highlightcolor=rojo, font=("Segoe UI", 12),
        )
        self.campo_usuario.pack(fill="x", pady=(5, 14), ipady=8)
        tk.Label(self.tarjeta, text="Contraseña", background=blanco, foreground=texto,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.campo_contrasena = tk.Entry(
            self.tarjeta, show="*", relief="flat", background="#FAFAFA", foreground=texto,
            insertbackground=texto, highlightthickness=1, highlightbackground="#D1D5DB",
            highlightcolor=rojo, font=("Segoe UI", 12),
        )
        self.campo_contrasena.pack(fill="x", pady=(5, 2), ipady=8)
        self.visible = False
        self._sesion_abierta = False
        self.boton_visibilidad = tk.Button(
            self.tarjeta, text="Mostrar contraseña", command=self._alternar_contrasena,
            background=blanco, foreground="#6B7280", activebackground=blanco,
            activeforeground=rojo, relief="flat", borderwidth=0, padx=0, pady=3,
            cursor="hand2", font=("Segoe UI", 9),
        )
        self.boton_visibilidad.pack(anchor="w", pady=(0, 14))
        for campo in (self.campo_usuario, self.campo_contrasena):
            campo.bind("<Return>", lambda evento: self._iniciar_sesion(aplicacion))
        self.campo_usuario.focus_set()
        fila_botones = tk.Frame(self.tarjeta, background=blanco)
        fila_botones.pack(fill="x", pady=(3, 0))
        fila_botones.grid_columnconfigure(0, weight=1, uniform="acciones")
        fila_botones.grid_columnconfigure(1, weight=1, uniform="acciones")
        self.boton_iniciar = tk.Button(
            fila_botones, text="Iniciar sesión", command=lambda: self._iniciar_sesion(aplicacion),
            background=rojo, foreground=blanco, activebackground="#B80023",
            activeforeground=blanco, relief="flat", borderwidth=0, padx=12, pady=10,
            cursor="hand2", font=("Segoe UI", 10, "bold"),
        )
        self.boton_iniciar.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=2)
        self.boton_registrarse = tk.Button(
            fila_botones, text="Registrarse", command=lambda: aplicacion.mostrar_vista("registro"),
            background=blanco, foreground=rojo, activebackground="#FCE7EC",
            activeforeground=rojo, relief="flat", borderwidth=1, highlightthickness=1,
            highlightbackground=rojo, highlightcolor=rojo, padx=12, pady=9,
            cursor="hand2", font=("Segoe UI", 10, "bold"),
        )
        self.boton_registrarse.grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=2)
        self.boton_iniciar.bind("<Enter>", lambda evento: evento.widget.configure(background="#B80023"))
        self.boton_iniciar.bind("<Leave>", lambda evento: evento.widget.configure(background=rojo))
        self.boton_registrarse.bind("<Enter>", lambda evento: evento.widget.configure(background="#FCE7EC"))
        self.boton_registrarse.bind("<Leave>", lambda evento: evento.widget.configure(background=blanco))

        self.tarjeta.update_idletasks()
        self._alto_tarjeta = self.tarjeta.winfo_reqheight()
        self.tarjeta.configure(width=min(480, max(340, self.tarjeta.winfo_reqwidth())),
                               height=self._alto_tarjeta)
        self.tarjeta.grid_propagate(False)
        zona.bind("<Configure>", self._ajustar_tarjeta)

    def _ajustar_tarjeta(self, evento):
        ancho = min(480, max(300, evento.width - 40))
        alto = min(self._alto_tarjeta, max(360, evento.height - 24))
        self.tarjeta.configure(width=ancho, height=alto)

    def _alternar_contrasena(self):
        self.visible = not self.visible
        self.campo_contrasena.configure(show="" if self.visible else "*")
        self.boton_visibilidad.configure(text="Ocultar contraseña" if self.visible else "Mostrar contraseña")

    def _iniciar_sesion(self, aplicacion):
        """Autentica al usuario y abre el panel si las credenciales son correctas."""
        if self._sesion_abierta:
            return
        try:
            usuario = aplicacion.gestor_usuarios.iniciar_sesion(
                self.campo_usuario.get(),
                self.campo_contrasena.get(),
            )
        except ValueError as error:
            messagebox.showerror("Acceso denegado", str(error))
            return
        except OSError:
            messagebox.showerror("No se pudo iniciar sesión", "No se pudo guardar la contraseña protegida. Inténtalo de nuevo.")
            return
        if usuario is None:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            return
        self._sesion_abierta = True
        aplicacion.mostrar_vista("panel", usuario)
