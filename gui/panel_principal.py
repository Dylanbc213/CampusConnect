"""Panel principal de la cuenta autenticada."""

import tkinter as tk
from tkinter import messagebox
from gui.ventana_muro import VentanaMuro
from gui.estilo import estructura, decorar, encabezado
from gui.lista_amigos import ListaAmigos


class PanelPrincipal:
    """Presenta un saludo y permite cerrar la sesión."""

    def __init__(self, contenedor, aplicacion, usuario):
        """Construye una vista inicial sencilla para una cuenta autenticada."""
        self.aplicacion = aplicacion
        self.usuario = usuario
        self.resultados = []
        lateral, central = estructura(contenedor)
        self.secciones = {nombre: tk.Frame(central, background="#FFFFFF")
                          for nombre in ("Buscar usuarios", "Amigos", "muro")}
        self.muro = VentanaMuro(self.secciones["muro"], aplicacion, usuario)
        contenedor = self.secciones["Buscar usuarios"]
        tk.Label(contenedor, text="Panel principal", font=("Arial", 18, "bold")).pack(pady=16)
        tk.Label(contenedor, text="Bienvenido/a, {}".format(usuario.nombre)).pack(pady=8)
        tk.Label(contenedor, text="Buscar por nombre o usuario").pack()
        self.campo_busqueda = tk.Entry(contenedor)
        self.campo_busqueda.pack(fill="x")
        self.campo_busqueda.bind("<KeyRelease>", lambda evento: self._buscar())
        for evento in ("<<Paste>>", "<<Cut>>"):
            self.campo_busqueda.bind(evento, lambda evento: self.campo_busqueda.after_idle(self._buscar))
        tk.Button(contenedor, text="Buscar", command=self._buscar).pack(pady=4)
        self.estado_busqueda = tk.Label(contenedor, text="Escribe un nombre o usuario.", anchor="w")
        self.estado_busqueda.pack(fill="x", pady=(4, 6))
        self.lista_resultados = tk.Listbox(contenedor, height=5, exportselection=False)
        self.lista_resultados.pack(fill="both", expand=True)
        self.lista_resultados.bind("<<ListboxSelect>>", self._actualizar_seleccion)
        self.boton_agregar = tk.Button(contenedor, text="Agregar amigo", command=self._agregar_amigo, state="disabled")
        self.boton_agregar.pack(fill="x", pady=(6, 12))
        contenedor = self.secciones["Amigos"]
        self.lista_amigos = ListaAmigos(contenedor)
        self.lista_amigos.pack(fill="both", expand=True)
        self._actualizar_amigos()
        self.botones_navegacion = {}
        self.seccion_activa = None
        for nombre in ("Inicio", "Buscar usuarios", "Amigos", "Mi muro"):
            boton = tk.Button(lateral, text=nombre, anchor="w",
                              command=lambda seccion=nombre: self._mostrar_seccion(seccion))
            boton.pack(fill="x", pady=4)
            self.botones_navegacion[nombre] = boton
        tk.Button(lateral, text="Cerrar sesión",
                  command=lambda: aplicacion.mostrar_vista("inicio")).pack(side="bottom", fill="x", pady=10)
        decorar(self.secciones["Buscar usuarios"])
        decorar(lateral)
        encabezado(self.secciones["Buscar usuarios"], "Panel principal")
        for nombre, boton in self.botones_navegacion.items():
            boton.bind("<Enter>", lambda evento: evento.widget.configure(background="#B80023", foreground="#FFFFFF"))
            boton.bind("<Leave>", lambda evento, seccion=nombre: self._resaltar_navegacion())
        self._mostrar_seccion("Inicio")

    def _resaltar_navegacion(self):
        for nombre, boton in self.botones_navegacion.items():
            activo = nombre == self.seccion_activa
            boton.configure(background="#FFFFFF" if activo else "#E4002B",
                            foreground="#E4002B" if activo else "#FFFFFF")

    def _mostrar_seccion(self, nombre):
        for seccion in self.secciones.values():
            seccion.pack_forget()
        self.seccion_activa = nombre
        if nombre in ("Inicio", "Mi muro"):
            self.secciones["muro"].pack(fill="both", expand=True)
            self.muro.mostrar_feed(propias=nombre == "Mi muro")
        else:
            self.secciones[nombre].pack(fill="both", expand=True)
            if nombre == "Amigos":
                self._actualizar_amigos()
            else:
                self._buscar()
                self.campo_busqueda.focus_set()
        self._resaltar_navegacion()

    def _buscar(self):
        consulta = self.campo_busqueda.get()
        self.resultados = self.aplicacion.gestor_usuarios.buscar_usuarios(consulta)
        self.lista_resultados.delete(0, tk.END)
        amigos = self.aplicacion.gestor_amistades.obtener_amistades(self.usuario.nombre_usuario)
        for usuario in self.resultados:
            estado = " — Ya son amigos" if usuario.nombre_usuario in amigos else ""
            if usuario.nombre_usuario == self.usuario.nombre_usuario:
                estado = " — Tú"
            self.lista_resultados.insert(tk.END, "{} (@{}){}".format(usuario.nombre, usuario.nombre_usuario, estado))
        if not consulta.strip():
            texto = "Escribe un nombre o usuario."
        elif not self.resultados:
            texto = "No se encontraron usuarios."
        else:
            texto = "Resultados: {}. Selecciona un usuario.".format(len(self.resultados))
        self.estado_busqueda.configure(text=texto)
        self._actualizar_seleccion()

    def _actualizar_seleccion(self, evento=None):
        seleccion = self.lista_resultados.curselection()
        habilitado = False
        if seleccion and seleccion[0] < len(self.resultados):
            nombre = self.resultados[seleccion[0]].nombre_usuario
            habilitado = (nombre != self.usuario.nombre_usuario and nombre not in
                          self.aplicacion.gestor_amistades.obtener_amistades(self.usuario.nombre_usuario))
        self.boton_agregar.configure(state="normal" if habilitado else "disabled")

    def _agregar_amigo(self):
        seleccion = self.lista_resultados.curselection()
        if not seleccion:
            messagebox.showerror("Amistades", "Selecciona un usuario de los resultados.")
            return
        amigo = self.resultados[seleccion[0]]
        try:
            self.aplicacion.gestor_amistades.agregar_amistad(
                self.usuario.nombre_usuario, amigo.nombre_usuario,
            )
        except ValueError as error:
            messagebox.showerror("Amistades", str(error))
            return
        except OSError:
            messagebox.showerror("Amistades", "No se pudo guardar la amistad. Inténtalo de nuevo.")
            return
        self._actualizar_amigos()
        self._buscar()
        self.estado_busqueda.configure(text="Amigo agregado correctamente.")

    def _actualizar_amigos(self):
        amigos = self.aplicacion.gestor_amistades.obtener_amistades(self.usuario.nombre_usuario)
        tarjetas = []
        for nombre_usuario in amigos:
            amigo = self.aplicacion.gestor_usuarios.usuarios_por_nombre.get(nombre_usuario)
            tarjetas.append((amigo.nombre if amigo else nombre_usuario, nombre_usuario))
        self.lista_amigos.mostrar(tarjetas)
