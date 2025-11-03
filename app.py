# app.py
import os
import sys
import threading
import requests
import customtkinter as ctk
from PIL import Image

# -------------- Config --------------
BASE_URL = "http://127.0.0.1:8000"   # <- cambia según tu servidor Django
API_TOKEN = None                     # si usas token, ponlo aquí o carga desde ajustes
SIDEBAR_EXPANDED_WIDTH = 200
SIDEBAR_COLLAPSED_WIDTH = 64
ANIMATION_STEP = 16      # píxeles por frame de animación
ANIMATION_DELAY = 12     # ms entre frames

# -------------- Helpers --------------
def resource_path(relative_path: str) -> str:
    """Para que funcione con PyInstaller (_MEIPASS)"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# -------------- App --------------
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Mi Aplicación - Cliente")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # estado del sidebar
        self.sidebar_expanded = True
        self.sidebar_width = SIDEBAR_EXPANDED_WIDTH

        # almacenamiento de iconos (para evitar GC)
        self.icons = {}
        self.load_icons()

        # layout principal: sidebar + contenido
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.create_sidebar()
        self.create_main_area()

    def load_icons(self):
        icons_folder = resource_path(os.path.join("assets", "icons"))
        # Nombres de archivos esperados (ajusta si cambias)
        mapping = {
            "menu": "menu.png",
            "pedidos": "pedidos.png",
            "ajustes": "ajustes.png",
            "consultas": "consultas.png"
        }
        for key, filename in mapping.items():
            path = os.path.join(icons_folder, filename)
            if os.path.exists(path):
                img = Image.open(path)
                # usamos CTkImage para integrarlo con CTk
                self.icons[key] = ctk.CTkImage(img, size=(28, 28))
            else:
                self.icons[key] = None  # fallback

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=self.sidebar_width, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)

        # Toggle button (arriba)
        self.btn_toggle = ctk.CTkButton(
            self.sidebar, 
            text="", 
            width=36, height=36, 
            command=self.toggle_sidebar,
            fg_color="transparent",
            hover=False,
            image=self.icons.get("menu")
        )
        self.btn_toggle.grid(row=0, column=0, padx=12, pady=12, sticky="w")

        # Menu items
        self.menu_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(8,0))
        self.menu_frame.grid_columnconfigure(0, weight=1)

        self.menu_buttons = []
        menu_items = [
            ("Pedidos", self.icons.get("pedidos"), self.show_pedidos),
            ("Ajustes",  self.icons.get("ajustes"),  self.show_ajustes),
            ("Consultas",self.icons.get("consultas"),self.show_consultas)
        ]
        for idx, (text, icon, cmd) in enumerate(menu_items):
            btn = ctk.CTkButton(self.menu_frame, text=text, image=icon, anchor="w",
                                compound="left", command=cmd, height=44)
            btn.grid(row=idx, column=0, sticky="ew", pady=6, padx=4)
            self.menu_buttons.append(btn)

        # Spacer y footer estado
        self.sidebar.grid_rowconfigure(2, weight=1)
        self.status_lbl = ctk.CTkLabel(self.sidebar, text="Conectado", anchor="w", fg_color="transparent")
        self.status_lbl.grid(row=3, column=0, padx=12, pady=12, sticky="swe")

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkLabel(self.main_frame, text="Bienvenido", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.grid(row=0, column=0, sticky="new", pady=(6,12))

        # contenido dinámico
        self.content_area = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew")

        # por defecto mostrar pedidos
        self.show_pedidos()

    # ------------------ Navegación / páginas ------------------
    def clear_content(self):
        for w in self.content_area.winfo_children():
            w.destroy()

    def show_pedidos(self):
        self.header.configure(text="Pedidos")
        self.clear_content()
        toolbar = ctk.CTkFrame(self.content_area, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0,8))
        refresh_btn = ctk.CTkButton(toolbar, text="Cargar pedidos", command=self.fetch_pedidos)
        refresh_btn.pack(side="left", padx=(0,6))
        new_btn = ctk.CTkButton(toolbar, text="Nuevo pedido", command=self.nuevo_pedido_demo)
        new_btn.pack(side="left")

        # scrollable area para listar pedidos
        self.scroll = ctk.CTkScrollableFrame(self.content_area, width=600, height=400)
        self.scroll.pack(fill="both", expand=True)
        # nota: inicialmente vacío; se llenará al llamar fetch_pedidos()

    def show_ajustes(self):
        self.header.configure(text="Ajustes")
        self.clear_content()
        frame = ctk.CTkFrame(self.content_area)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(frame, text="Ajustes de conexión y preferencias", font=ctk.CTkFont(size=16)).pack(anchor="w", pady=6)
        # Ejemplo de ajuste: base url
        base_lbl = ctk.CTkLabel(frame, text="Backend URL:")
        base_lbl.pack(anchor="w", pady=(12,0))
        self.base_entry = ctk.CTkEntry(frame)
        self.base_entry.insert(0, BASE_URL)
        self.base_entry.pack(anchor="w", pady=(4,0))
        save_btn = ctk.CTkButton(frame, text="Guardar", command=self.guardar_ajustes)
        save_btn.pack(anchor="w", pady=12)

    def show_consultas(self):
        self.header.configure(text="Consultas")
        self.clear_content()
        frame = ctk.CTkFrame(self.content_area)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(frame, text="Consulta rápida a la API", font=ctk.CTkFont(size=16)).pack(anchor="w", pady=6)
        # aquí pondrías filtros, fechas, etc.

    # ------------------ Sidebar animación ------------------
    def toggle_sidebar(self):
        target = SIDEBAR_COLLAPSED_WIDTH if self.sidebar_expanded else SIDEBAR_EXPANDED_WIDTH
        self.animate_sidebar(target)
        self.sidebar_expanded = not self.sidebar_expanded
        # ocultar/mostrar texto en botones (rápido)
        for btn in self.menu_buttons:
            btn.configure(text=btn.cget("text") if self.sidebar_expanded else "")

    def animate_sidebar(self, target_width):
        def step():
            current = self.sidebar.winfo_width()
            if current == target_width:
                return
            direction = 1 if target_width > current else -1
            new = current + direction * ANIMATION_STEP
            if (direction == 1 and new > target_width) or (direction == -1 and new < target_width):
                new = target_width
            self.sidebar.configure(width=new)
            self.sidebar.update()
            self.after(ANIMATION_DELAY, step)
        step()

    # ------------------ Conexión con backend (ejemplos) ------------------
    def fetch_pedidos(self):
        # lanza hilo para no bloquear UI
        self.status_lbl.configure(text="Cargando pedidos...")
        thread = threading.Thread(target=self._fetch_pedidos_thread, daemon=True)
        thread.start()

    def _fetch_pedidos_thread(self):
        try:
            headers = {}
            if API_TOKEN:
                headers["Authorization"] = f"Token {API_TOKEN}"
            url = f"{BASE_URL}/api/pedidos/"
            resp = requests.get(url, headers=headers, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            # actualizar UI desde hilo principal
            self.after(0, lambda: self.display_pedidos(data))
            self.after(0, lambda: self.status_lbl.configure(text="Pedidos cargados"))
        except Exception as e:
            self.after(0, lambda: self.status_lbl.configure(text=f"Error: {str(e)}"))

    def display_pedidos(self, items):
        # limpia scroll
        for w in self.scroll.winfo_children():
            w.destroy()
        if not items:
            ctk.CTkLabel(self.scroll, text="No hay pedidos").pack(pady=12)
            return
        for it in items:
            # supone que cada item tiene 'id', 'cliente' y 'total' — adapta según tu API
            t = f"#{it.get('id')} — {it.get('cliente', 'sin cliente')} — ${it.get('total', 0)}"
            frame = ctk.CTkFrame(self.scroll, corner_radius=6)
            frame.pack(fill="x", pady=6, padx=6)
            ctk.CTkLabel(frame, text=t, anchor="w").pack(side="left", padx=8, pady=8)
            ver_btn = ctk.CTkButton(frame, text="Ver", width=80, command=lambda i=it: self.ver_pedido(i))
            ver_btn.pack(side="right", padx=8, pady=6)

    def ver_pedido(self, pedido):
        # ventana modal simple para mostrar detalle
        win = ctk.CTkToplevel(self)
        win.title(f"Pedido #{pedido.get('id')}")
        win.geometry("480x320")
        ctk.CTkLabel(win, text=str(pedido), wraplength=460).pack(padx=12, pady=12)

    def nuevo_pedido_demo(self):
        # ejemplo de POST (mock). Adapta payload a tu API.
        payload = {"cliente": "Prueba", "total": 123.45}
        thread = threading.Thread(target=self._post_pedido_thread, args=(payload,), daemon=True)
        thread.start()
        self.status_lbl.configure(text="Enviando nuevo pedido...")

    def _post_pedido_thread(self, payload):
        try:
            headers = {"Content-Type": "application/json"}
            if API_TOKEN:
                headers["Authorization"] = f"Token {API_TOKEN}"
            url = f"{BASE_URL}/api/pedidos/"
            resp = requests.post(url, json=payload, headers=headers, timeout=8)
            resp.raise_for_status()
            self.after(0, lambda: self.status_lbl.configure(text="Pedido creado"))
            # refrescar lista
            self.fetch_pedidos()
        except Exception as e:
            self.after(0, lambda: self.status_lbl.configure(text=f"Error al crear: {str(e)}"))

    def guardar_ajustes(self):
        global BASE_URL, API_TOKEN
        BASE_URL = self.base_entry.get()
        # podrías guardar en un fichero o en DB local
        self.status_lbl.configure(text="Ajustes guardados")
        # actualizar variables en la app si es necesario

# ------------------ Run ------------------
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
