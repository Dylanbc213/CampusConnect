import tkinter as tk
from tkinter import ttk
from gui.avatar import dibujar_avatar
from gui.scroll import enlazar_rueda_descendientes
from gui.estilo import aplicar_tema_actual


class ListaAmigos(tk.Frame):
    def __init__(self, padre, al_seleccionar=None, obtener_usuario=None, carpeta_datos=None):
        super().__init__(padre, background="#FFFFFF")
        cabecera = tk.Frame(self, background="#FFFFFF")
        cabecera.pack(fill="x", pady=(8, 4))
        tk.Label(cabecera, text="Mis amigos", background="#FFFFFF", foreground="#1F2937",
                 font=("Segoe UI", 24, "bold")).pack(side="left")
        self.contador = tk.Label(cabecera, text="0", background="#FCE7EC", foreground="#E4002B",
                                 font=("Segoe UI", 12, "bold"), padx=14, pady=6)
        self.contador.pack(side="right", padx=4)
        tk.Label(self, text="Tu comunidad, cada vez más cerca.", anchor="w", background="#FFFFFF",
                 foreground="#6B7280", font=("Segoe UI", 11)).pack(fill="x", pady=(0, 20))
        self.zona = tk.Frame(self, background="#F3F4F6", padx=8, pady=8)
        self.zona.pack(fill="both", expand=True)
        self.al_seleccionar = al_seleccionar
        self.obtener_usuario = obtener_usuario
        self.carpeta_datos = carpeta_datos or ""
        self.canvas = tk.Canvas(self.zona, background="#F3F4F6", highlightthickness=0, width=1)
        self.scroll = ttk.Scrollbar(self.zona, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.tarjetas = tk.Frame(self.canvas, background="#F3F4F6")
        self.ventana = self.canvas.create_window((0, 0), window=self.tarjetas, anchor="nw")
        self.tarjetas.bind("<Configure>", lambda evento: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._ajustar)
        self.vacio = tk.Frame(self.zona, background="#F3F4F6", padx=12, pady=24)
        tk.Label(self.vacio, text="Tu comunidad empieza aquí", background="#F3F4F6", foreground="#1F2937",
                 font=("Segoe UI", 16, "bold"), wraplength=270).pack(pady=(0, 12))
        tk.Label(self.vacio, text="Aún no tienes amigos.\nBusca a tus compañeros y conecta con ellos.",
                 background="#F3F4F6", foreground="#6B7280", font=("Segoe UI", 11),
                 wraplength=270, justify="center").pack()
        enlazar_rueda_descendientes(self.canvas, self._rueda)

    def _ajustar(self, evento):
        self.canvas.itemconfigure(self.ventana, width=evento.width)
        for tarjeta in self.tarjetas.winfo_children():
            for widget in tarjeta.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(wraplength=max(100, evento.width - 110))

    def _enlazar_scroll(self, widget):
        widget.bind("<MouseWheel>", self._rueda)
        widget.bind("<Button-4>", lambda evento: self._desplazar(-1))
        widget.bind("<Button-5>", lambda evento: self._desplazar(1))

    def _desplazar(self, unidades):
        if self.tarjetas.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(unidades, "units")
        return "break"

    def _rueda(self, evento):
        if getattr(evento, "num", None) == 4:
            unidades = -1
        elif getattr(evento, "num", None) == 5:
            unidades = 1
        else:
            unidades = -1 if evento.delta > 0 else 1
        return self._desplazar(unidades)

    def mostrar(self, amigos, solicitudes=(), al_responder=None):
        for tarjeta in self.tarjetas.winfo_children():
            tarjeta.destroy()
        self.contador.configure(text=str(len(amigos)))
        if amigos or solicitudes:
            self.vacio.place_forget()
        else:
            self.vacio.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95)
        for emisor in solicitudes:
            fila = tk.Frame(self.tarjetas, background="#FFFFFF", padx=14, pady=12)
            fila.pack(fill="x", padx=4, pady=6)
            tk.Button(fila, text="@{} quiere ser tu amigo".format(emisor),
                      command=lambda u=emisor: self.al_seleccionar(u),
                      background="#FFFFFF", foreground="#1F2937", relief="flat",
                      borderwidth=0, cursor="hand2").pack(anchor="w")
            for texto, aceptar in (("Aceptar", True), ("Rechazar", False)):
                tk.Button(fila, text=texto, command=lambda u=emisor, a=aceptar: al_responder(u, a),
                          background="#E4002B" if aceptar else "#E5E7EB",
                          foreground="#FFFFFF" if aceptar else "#1F2937", relief="flat",
                          borderwidth=0, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)
            enlazar_rueda_descendientes(fila, self._rueda)
        for nombre, usuario in amigos:
            tarjeta = tk.Frame(self.tarjetas, background="#FFFFFF", highlightbackground="#E5E7EB",
                               highlightthickness=1, padx=14, pady=14)
            tarjeta.pack(fill="x", padx=4, pady=6)
            tarjeta.columnconfigure(1, weight=1)
            if hasattr(self, "abrir_chat"):
                tk.Button(tarjeta, text="Mensaje", command=lambda u=usuario: self.abrir_chat(u),
                          background="#E4002B", foreground="#FFFFFF", relief="flat",
                          borderwidth=0, padx=10, pady=6, cursor="hand2").grid(row=0, column=2, rowspan=2)
            avatar = tk.Canvas(tarjeta, width=48, height=48, background="#FFFFFF", highlightthickness=0)
            avatar.grid(row=0, column=0, rowspan=2, padx=(0, 14))
            if self.al_seleccionar:
                avatar.configure(cursor="hand2")
                avatar.bind("<Button-1>", lambda evento, user=usuario: self.al_seleccionar(user))
            persona = self.obtener_usuario(usuario) if self.obtener_usuario else None
            if persona:
                dibujar_avatar(avatar, persona, self.carpeta_datos, 48)
            else:
                avatar.create_oval(1, 1, 47, 47, fill="#FCE7EC", outline="")
                iniciales = "".join(parte[0] for parte in nombre.split()[:2]).upper() or "?"
                avatar.create_text(24, 24, text=iniciales, fill="#E4002B", font=("Segoe UI", 14, "bold"))
            tk.Label(tarjeta, text="@" + usuario, background="#FFFFFF", foreground="#1F2937",
                     font=("Segoe UI", 12, "bold"), anchor="w", justify="left",
                     wraplength=max(100, self.canvas.winfo_width() - 110)
                     ).grid(row=0, column=1, rowspan=2, sticky="ew", pady=2)
            if self.al_seleccionar:
                for widget in tarjeta.winfo_children():
                    if isinstance(widget, tk.Label):
                        widget.configure(cursor="hand2")
                        widget.bind("<Button-1>", lambda evento, user=usuario: self.al_seleccionar(user))
            enlazar_rueda_descendientes(tarjeta, self._rueda)
        aplicar_tema_actual(self)
        self.canvas.yview_moveto(0)
