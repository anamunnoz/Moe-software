import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QListWidget, QMessageBox, QFormLayout, QSpinBox, QFrame, QComboBox,
    QListWidgetItem, QApplication, QScrollArea, QDialog, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QMouseEvent
from urls import API_URL_CLIENTES, API_URL_BOOKS, API_URL_ADITIVOS, API_URL_CLIENTES, API_URL_ORDERS
from utils import http_get, http_post, http_patch, http_delete, make_icon_label
from price.get_rates import convert_to_currency

class ClickableOrderCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.order_data = order_data
        self.setObjectName("orderCard")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        order_id = QLabel(f"Orden #{order_data['idOrder']}")
        order_id.setStyleSheet("font-weight: 600; color: #222; font-size: 14px;")
        service = (" ").join(order_data['type'].split(" ")[1:]) if order_data['type'].lower()  != 'regular' else order_data['type']
        order_type = QLabel(f"📦 {service}")
        order_type.setStyleSheet("color: #555; font-size: 13px;")

        status_text = "✅ Completada" if order_data.get("done") else "🟡 Pendiente"
        order_status = QLabel(status_text)
        order_status.setStyleSheet("color: #666; font-size: 13px;")

        header_layout.addWidget(order_id)
        header_layout.addStretch()
        header_layout.addWidget(order_type)
        header_layout.addWidget(order_status)
        layout.addLayout(header_layout)

        details_layout = QVBoxLayout()
        details_layout.setSpacing(2)

        address = order_data.get("address")
        if address:
            address_label = QLabel(f"📍 {address}")
            address_label.setStyleSheet("color: #555; font-size: 12px;")
            details_layout.addWidget(address_label)

        delivery_zone = order_data.get("delivery_zone")
        if delivery_zone:
            delivery_label = QLabel(
                f"🚗 Entrega: {delivery_zone} (${order_data.get('delivery_price', 0)})"
            )
            delivery_label.setStyleSheet("color: #555; font-size: 12px;")
            details_layout.addWidget(delivery_label)

        total_price = order_data.get("total_price", 0)
        pay_method = order_data.get("pay_method", "")
        price_label = QLabel(f"💰 Total: ${total_price}")
        price_label.setStyleSheet("color: #555; font-size: 12px;")
        details_layout.addWidget(price_label)

        order_date = order_data.get("order_date", "-")
        delivery_date = order_data.get("delivery_date", "-")
        dates_label = QLabel(f"📅 Pedido: {order_date} - Entrega: {delivery_date}")
        dates_label.setStyleSheet("color: #555; font-size: 11px;")
        details_layout.addWidget(dates_label)

        layout.addLayout(details_layout)

        self.setStyleSheet("""
            QFrame#orderCard {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background: #fafafa;
                margin: 2px;
            }
            QFrame#orderCard:hover {
                background: #f0f8ff;
                border: 1px solid #007acc;
            }
        """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.order_data)
        super().mousePressEvent(event)


class ClientResultItem(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.setObjectName("clientCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        name_layout = QHBoxLayout()
        name_label = QLabel(client["name"])
        name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1c1c1c;
        """)
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        phone_layout = QHBoxLayout()
        phone_label = QLabel(f"Número de teléfono: {client['phone_number']}")
        phone_label.setStyleSheet("color: #555;")
        phone_layout.addWidget(phone_label)
        phone_layout.addStretch()
        layout.addLayout(phone_layout)

        id_layout = QHBoxLayout()
        id_label = QLabel(f"Carnet de identidad: {client['identity']}")
        id_label.setStyleSheet("color: #555;")
        id_layout.addWidget(id_label)
        id_layout.addStretch()
        layout.addLayout(id_layout)

        self.setStyleSheet("""
            QWidget#clientCard {
                border: 5px solid #FF0000;
                border-radius: 10px;
                background: #fff;
                padding: 8px;
            }
        """)


class ClientsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_styles()
        self._load_books_and_additives()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap("icons/customers.png").scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Manejo de clientes")
        title.setStyleSheet("font-size: 35px; font-weight: 700; color: #222;")
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        
        # Subpestañas principales
        self._build_addresses_tab()
        self._build_insert_tab()
        self._build_update_tab()
        self._build_delete_tab()

 #* ------------------- INSERT -------------------
    def _build_insert_tab(self):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        form_block = QWidget()
        form_layout = QVBoxLayout(form_block)
        form_layout.setSpacing(10)
        form_layout.setAlignment(Qt.AlignTop)

        form_card = QFrame()
        form_card.setObjectName("card")
        inner_form = QFormLayout(form_card)
        inner_form.setSpacing(12)

        self.add_name = QLineEdit()
        self.add_phone = QLineEdit()
        self.add_identity = QLineEdit()

        self.add_name.returnPressed.connect(self._add_cliente)
        self.add_phone.returnPressed.connect(self._add_cliente)
        self.add_identity.returnPressed.connect(self._add_cliente)


        inner_form.addRow(make_icon_label("icons/name.png", "Nombre"), self.add_name)
        inner_form.addRow(make_icon_label("icons/phone.png", "Teléfono"), self.add_phone)
        inner_form.addRow(make_icon_label("icons/identity.png", "Carnet de identidad"), self.add_identity)

        form_layout.addWidget(form_card)
        spacer = QWidget()
        spacer.setFixedHeight(10)
        form_layout.addWidget(spacer)

        btn = QPushButton("Añadir cliente")
        btn.setObjectName("primaryBtn")
        btn.clicked.connect(self._add_cliente)
        form_layout.addWidget(btn, alignment=Qt.AlignHCenter)

        main_layout.addWidget(form_block, alignment=Qt.AlignTop)
        self.tabs.addTab(tab, "Añadir")

    def _add_cliente(self):
        nombre = self.add_name.text().strip()
        telefono = self.add_phone.text().strip()
        identidad = self.add_identity.text().strip()

        if not nombre or not telefono or not identidad:
            QMessageBox.warning(self, "Validación", "Debe completar todos los campos.")
            return

        payload = {
            "name": nombre,
            "phone_number": telefono,
            "identity": identidad
        }

        r = http_post(API_URL_CLIENTES, payload)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al contactar la API.")
            return
        if r.status_code in (200, 201):
            QMessageBox.information(
                self,
                "👤 Cliente agregado",
                f"Se ha agregado el cliente:\n\n"
                f"👤 Nombre: {nombre}\n📞 Teléfono: {telefono}\n🪪 Carnet: {identidad}"
            )
            self.add_name.clear()
            self.add_phone.clear()
            self.add_identity.clear()
        elif r.status_code == 400:
            QMessageBox.warning(self, "Duplicado", "Ya existe un cliente con esa identidad.")
        else:
            QMessageBox.warning(self, "Falló la inserción", f"Insert failed: {r.status_code}\n{r.text}")
    
#* ------------------- UPDATE -------------------
    def _build_update_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignTop)

        self.search_cliente = QLineEdit()
        self.search_cliente.setPlaceholderText("Buscar por nombre")
        self.search_cliente.returnPressed.connect(self._search_cliente)

        btn_search = QPushButton("Buscar cliente")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._search_cliente)

        left.addWidget(self.search_cliente)
        left.addWidget(btn_search)

        self.list_cliente = QListWidget()
        self.list_cliente.itemSelectionChanged.connect(self._on_cliente_selected)
        left.addWidget(self.list_cliente, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QFormLayout(form_card)
        form_layout.setSpacing(12)

        self.edit_name = QLineEdit()
        self.edit_phone = QLineEdit()
        self.edit_identity = QLineEdit()

        form_layout.addRow(make_icon_label("icons/name.png", "Nombre"), self.edit_name)
        form_layout.addRow(make_icon_label("icons/phone.png", "Teléfono"), self.edit_phone)
        form_layout.addRow(make_icon_label("icons/identity.png", "Carnet de identidad"), self.edit_identity)

        self.btn_update_cliente = QPushButton("Aplicar cambios")
        self.btn_update_cliente.setObjectName("primaryBtn")
        self.btn_update_cliente.clicked.connect(self._update_cliente)
        self.btn_update_cliente.setEnabled(False)
        form_layout.addRow(QWidget(), self.btn_update_cliente)

        right.addWidget(form_card)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)

        self.tabs.addTab(tab, "Modificar")

    def _search_cliente(self):
        q = self.search_cliente.text().strip()
        if not q:
            QMessageBox.information(self, "Búsqueda", "Ingrese un nombre para buscar.")
            self.list_cliente.clear()
            return

        r = http_get(API_URL_CLIENTES)
        if r is None or r.status_code != 200:
            QMessageBox.critical(self, "Error", "Error de red.")
            return

        all_clients = r.json()
        q_lower = q.lower()

        data = [
        c for c in all_clients 
        if (q_lower in c["name"].lower() or 
            q_lower in c["identity"].lower() or 
            q_lower in c["phone_number"].lower())
        ]

        self.list_cliente.clear()
        self._cliente_cache = {}

        if not data:
            self.list_cliente.addItem("No se encontraron resultados")
            return

        for c in data:
            widget = ClientResultItem(c)
            item = QListWidgetItem(self.list_cliente)
            item.setSizeHint(widget.sizeHint())
            self.list_cliente.addItem(item)
            self.list_cliente.setItemWidget(item, widget)
            item.client_data = c


    def _on_cliente_selected(self):
        items = self.list_cliente.selectedItems()
        if not items:
            self.btn_update_cliente.setEnabled(False)
            return

        item = items[0]
        if not hasattr(item, "client_data"):
            self.btn_update_cliente.setEnabled(False)
            return

        c = item.client_data
        self.selected_cliente_id = c["idClient"]
        self.edit_name.setText(c["name"])
        self.edit_phone.setText(c["phone_number"])
        self.edit_identity.setText(c["identity"])
        self.btn_update_cliente.setEnabled(True)

    def _update_cliente(self):
        payload = {
            "name": self.edit_name.text().strip(),
            "phone_number": self.edit_phone.text().strip(),
            "identity": self.edit_identity.text().strip()
        }

        r = http_patch(f"{API_URL_CLIENTES}{self.selected_cliente_id}/", payload)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red.")
            return
        if r.status_code in (200, 204):
            QMessageBox.information(self, "Actualizado", "Cliente actualizado correctamente.")
            self._search_cliente()
        else:
            QMessageBox.warning(self, "Fallo", f"Falló la actualización: {r.status_code}\n{r.text}")


#* ------------------- DELETE -------------------
    def _build_delete_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.search_delete_input = QLineEdit()
        self.search_delete_input.setPlaceholderText("Buscar por nombre o carnet de identidad")
        self.search_delete_input.returnPressed.connect(self._search_for_delete)

        btn_search = QPushButton("Buscar")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._search_for_delete)
        left.addWidget(self.search_delete_input)
        left.addWidget(btn_search)

        self.search_delete_results = QListWidget()
        self.search_delete_results.itemSelectionChanged.connect(self._on_delete_selection)
        left.addWidget(self.search_delete_results, 1)

        right = QVBoxLayout()

        self.delete_info_container = QWidget()
        self.delete_info_container.setObjectName("infoContainer")
        self.delete_info_layout = QVBoxLayout(self.delete_info_container)
        self.delete_info_layout.setAlignment(Qt.AlignCenter)

        self.delete_placeholder = QWidget()
        ph_layout = QVBoxLayout(self.delete_placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_pix = QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pix)
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Seleccione un cliente para ver los detalles.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon_label)
        ph_layout.addWidget(text_label)

        self.delete_info_layout.addWidget(self.delete_placeholder)

        right.addWidget(self.delete_info_container, 1)

        self.btn_delete = QPushButton("Eliminar cliente seleccionado")
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._perform_delete)
        right.addWidget(self.btn_delete, alignment=Qt.AlignRight)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)
        self.tabs.addTab(tab, "Eliminar")

    def _search_for_delete(self):
        q = self.search_delete_input.text().strip()
        if not q:
            QMessageBox.information(self, "Input", "Escribe un nombre o carnet para buscar.")
            self.search_delete_results.clear()
            return

        r = http_get(API_URL_CLIENTES)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        all_clients = r.json()
        q_lower = q.lower()
        data = [
            c for c in all_clients 
            if (q_lower in c["name"].lower() or 
                q_lower in c["identity"].lower() or 
                q_lower in c["phone_number"].lower())
            ]

        self.search_delete_results.clear()
        self._delete_cache = {}

        if not data:
            self.search_delete_results.addItem("(sin resultados)")
            return

        for c in data:
            item_widget = ClientResultItem(c)
            list_item = QListWidgetItem(self.search_delete_results)
            list_item.setSizeHint(item_widget.sizeHint())

            self._delete_cache[id(list_item)] = c
            self.search_delete_results.addItem(list_item)
            self.search_delete_results.setItemWidget(list_item, item_widget)

    def _on_delete_selection(self):
        items = self.search_delete_results.selectedItems()
        if not items:
            self.btn_delete.setEnabled(False)
            self._clear_delete_info(show_placeholder=True)
            return

        list_item = items[0]
        client = self._delete_cache.get(id(list_item))
        if not client:
            self.btn_delete.setEnabled(False)
            self._clear_delete_info(show_placeholder=True)
            return

        self.selected_delete_id = client["idClient"]
        self.btn_delete.setEnabled(True)

        self._clear_delete_info(show_placeholder=False)

        info_card = QFrame()
        info_card.setObjectName("card")
        form = QFormLayout(info_card)
        form.setSpacing(10)

        def make_icon_line(icon_path, text):
            w = QWidget()
            layout = QHBoxLayout(w)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
            icon = QLabel()
            icon.setPixmap(QPixmap(icon_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label = QLabel(text)
            label.setStyleSheet("font-size: 14px; color: #333;")
            layout.addWidget(icon)
            layout.addWidget(label)
            layout.addStretch()
            return w

        form.addRow(make_icon_line("icons/name.png", f"Nombre: {client['name']}"))
        form.addRow(make_icon_line("icons/phone.png", f"Teléfono: {client['phone_number']}"))
        form.addRow(make_icon_line("icons/identity.png", f"Carnet de identidad: {client['identity']}"))

        self.delete_info_layout.addWidget(info_card, alignment=Qt.AlignCenter)

    def _clear_delete_info(self, show_placeholder=True):
        while self.delete_info_layout.count():
            child = self.delete_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not show_placeholder:
            return

        self.delete_placeholder = QWidget()
        ph_layout = QVBoxLayout(self.delete_placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_pix = QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pix)
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Seleccione un cliente para ver los detalles.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon_label)
        ph_layout.addWidget(text_label)
        self.delete_info_layout.addWidget(self.delete_placeholder)

    def _perform_delete(self):
        items = self.search_delete_results.selectedItems()
        if not items:
            QMessageBox.information(self, "Eliminar cliente", "Selecciona un cliente para eliminar.")
            return

        list_item = items[0]
        client = self._delete_cache.get(id(list_item))
        if not client:
            QMessageBox.warning(self, "Eliminar cliente", "No se pudo obtener la información del cliente seleccionado.")
            return

        msg_text = (
            f"¿Estás seguro que quieres eliminar este cliente?\n\n"
            f"👤 Nombre: {client['name']}\n"
            f"📞 Teléfono: {client['phone_number']}\n"
            f"🪪 Carnet de identidad: {client['identity']}\n"
        )

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            msg_text,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        r = http_delete(f"{API_URL_CLIENTES}{client['idClient']}/")
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al intentar eliminar el cliente.")
            return

        if r.status_code in (200, 204):
            QMessageBox.information(
                self,
                "Cliente eliminado",
                f"El cliente '{client['name']}' fue eliminado correctamente."
            )
            self._search_for_delete()
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo eliminar el cliente.\nCódigo: {r.status_code}\n{r.text}"
            )

    def _copy_client_to_clipboard(self, client):
        text = (
            f"👤 Nombre: {client['name']}\n"
            f"📞 Teléfono: {client['phone_number']}\n"
            f"🪪 Carnet de identidad: {client['identity']}\n"
            f"📦 Total de órdenes: {client['total_orders']}"
        )

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copiado", "La información del cliente se copió al portapapeles.")

    def _copy_addresses_to_clipboard(self, addresses):
        if not addresses:
            QMessageBox.information(self, "Sin direcciones", "Este cliente no tiene direcciones registradas.")
            return

        formatted = ""
        formatted += "\n".join([f"📍 {addr}" for addr in addresses])

        clipboard = QApplication.clipboard()
        clipboard.setText(formatted)

        QMessageBox.information(
            self,
            "📋 Copiado",
            "Las direcciones se copiaron al portapapeles."
    )

#* ------------------- LISTAR DIRECCIONES -------------------
    def _build_addresses_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(20)

        left = QVBoxLayout()
        left.setSpacing(12)

        search_layout = QVBoxLayout()
        search_layout.setSpacing(8)
        
        self.search_address_input = QLineEdit()
        self.search_address_input.setPlaceholderText("Buscar por nombre, carnet o teléfono...")
        self.search_address_input.returnPressed.connect(self._search_client_addresses)

        self.search_address_input.setClearButtonEnabled(True)

        btn_search = QPushButton("Buscar Clientes")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._search_client_addresses)

        search_layout.addWidget(self.search_address_input)
        search_layout.addWidget(btn_search)
        left.addLayout(search_layout)

        self.clients_list = QListWidget()
        self.clients_list.itemSelectionChanged.connect(self._on_client_address_selected)
        left.addWidget(self.clients_list, 1)

        right = QVBoxLayout()
        right.setSpacing(12)

        self.client_info_container = QWidget()
        self.client_info_container.setObjectName("infoContainer")
        self.client_info_layout = QVBoxLayout(self.client_info_container)
        self.client_info_layout.setAlignment(Qt.AlignCenter)

        self.client_placeholder = QWidget()
        ph_layout = QVBoxLayout(self.client_placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel()
        icon.setPixmap(QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        text = QLabel("Busca un cliente y selecciona uno para ver sus direcciones y órdenes.")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")
        
        ph_layout.addWidget(icon)
        ph_layout.addWidget(text)
        self.client_info_layout.addWidget(self.client_placeholder)

        right.addWidget(self.client_info_container, 1)

        main_layout.addLayout(left, 2)
        main_layout.addLayout(right, 2)
        self.tabs.addTab(tab, "Información de los clientes")

    def _search_client_addresses(self):
        query = self.search_address_input.text().strip()
        if not query:
            QMessageBox.information(self, "Búsqueda", "Ingresa un nombre, carnet o teléfono para buscar.")
            self.clients_list.clear()
            return

        url = f"{API_URL_CLIENTES}search_with_orders/?q={query}"

        r = http_get(url)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de conexión con el servidor.")
            return
            
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        data = r.json()
        clients = data.get('clients', [])
        
        self.clients_list.clear()
        self._addresses_cache = {}
        
        if not clients:
            self.clients_list.addItem("(sin resultados)")
            return

        for client in clients:
            client_widget = ClientResultItem(client)
            
            list_item = QListWidgetItem(self.clients_list)
            list_item.setSizeHint(client_widget.sizeHint())
            self.clients_list.addItem(list_item)
            self.clients_list.setItemWidget(list_item, client_widget)
            self._addresses_cache[id(list_item)] = client

    def _on_client_address_selected(self):
            items = self.clients_list.selectedItems()
            if not items:
                self._clear_client_info(show_placeholder=True)
                return

            list_item = items[0]
            client = self._addresses_cache.get(id(list_item))
            if not client:
                self._clear_client_info(show_placeholder=True)
                return

            self._clear_client_info(show_placeholder=False)

            main_widget = QWidget()
            main_layout = QVBoxLayout(main_widget)
            main_layout.setSpacing(15)

            #? ------------------ INFORMACIÓN DEL CLIENTE ------------------
            client_card = QFrame()
            client_card.setObjectName("card")
            client_layout = QVBoxLayout(client_card)
            client_layout.setSpacing(10)
            header_layout = QHBoxLayout()

            def make_icon_line(icon_path, text):
                w = QWidget()
                layout = QHBoxLayout(w)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(8)
                icon = QLabel()
                icon.setPixmap(QPixmap(icon_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                label = QLabel(text)
                label.setStyleSheet("font-size: 14px; color: #333;")
                layout.addWidget(icon)
                layout.addWidget(label)
                layout.addStretch()
                return w

            client_layout.addWidget(make_icon_line("icons/client.png", f"Nombre: {client['name']}"))
            client_layout.addWidget(make_icon_line("icons/identity.png", f"Carnet de identidad: {client['identity']}"))
            client_layout.addWidget(make_icon_line("icons/phone.png", f"Teléfono: {client['phone_number']}"))
            client_layout.addWidget(make_icon_line("icons/orders.png", f"Total de órdenes: {client['total_orders']}"))

            self.copy_client_btn = QPushButton("Copiar Cliente")
            self.copy_client_btn.setObjectName("secondaryBtn")
            self.copy_client_btn.clicked.connect(lambda: self._copy_client_to_clipboard(client))

            header_layout.addStretch()
            header_layout.addWidget(self.copy_client_btn)
            client_layout.addLayout(header_layout)


            main_layout.addWidget(client_card)

            #? ------------------ DIRECCIONES ------------------
            addresses_card = QFrame()
            addresses_card.setObjectName("card")
            addresses_layout = QVBoxLayout(addresses_card)
            addresses_layout.setSpacing(4)

            title_layout = QHBoxLayout()
            title_icon = QLabel()
            title_icon.setPixmap(QPixmap("icons/location.png").scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            title_label = QLabel("Direcciones Utilizadas")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
            title_layout.addWidget(title_icon)
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            addresses_layout.addLayout(title_layout)

            unique_addresses = client.get('unique_addresses', [])
            if unique_addresses:
                for address in unique_addresses:
                    pretty_address = f" 📍 {address}"
                    address_label = QLabel(pretty_address)
                    address_label.setStyleSheet("""
                        font-size: 13px;
                        color: #444;
                        padding: 3px 0;
                        border-left: 3px solid #ff5555;
                        padding-left: 6px;
                    """)
                    address_label.setWordWrap(True)
                    addresses_layout.addWidget(address_label)
            else:
                no_addresses = QLabel("No hay direcciones registradas")
                no_addresses.setStyleSheet("font-size: 13px; color: #888; font-style: italic;")
                no_addresses.setAlignment(Qt.AlignCenter)
                addresses_layout.addWidget(no_addresses)

            if unique_addresses:
                copy_addresses_btn = QPushButton("Copiar todas las direcciones")
                copy_addresses_btn.setObjectName("secondaryBtn")
                copy_addresses_btn.setCursor(Qt.PointingHandCursor)
                copy_addresses_btn.clicked.connect(lambda: self._copy_addresses_to_clipboard(unique_addresses))
                addresses_layout.addWidget(copy_addresses_btn, alignment=Qt.AlignRight)

            main_layout.addWidget(addresses_card)

            orders_card = QFrame()
            orders_card.setObjectName("card")
            orders_layout = QVBoxLayout(orders_card)

            orders_title_layout = QHBoxLayout()
            orders_icon = QLabel()
            orders_icon.setPixmap(QPixmap("icons/history.png").scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            orders_label = QLabel("Historial de Órdenes")
            orders_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
            orders_title_layout.addWidget(orders_icon)
            orders_title_layout.addWidget(orders_label)
            orders_title_layout.addStretch()
            orders_layout.addLayout(orders_title_layout)

            orders_list = client.get('orders', [])
            if orders_list:
                for order in orders_list:
                    order_widget = self._create_order_widget(order)
                    orders_layout.addWidget(order_widget)
            else:
                no_orders = QLabel("No hay órdenes registradas")
                no_orders.setStyleSheet("font-size: 13px; color: #888; font-style: italic;")
                no_orders.setAlignment(Qt.AlignCenter)
                orders_layout.addWidget(no_orders)
            
            main_layout.addWidget(orders_card)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(main_widget)
            scroll_area.setMaximumHeight(600)
            self.client_info_layout.addWidget(scroll_area)


    def _clear_client_info(self, show_placeholder=True):
        while self.client_info_layout.count():
            child = self.client_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if show_placeholder:
            self.client_placeholder = QWidget()
            ph_layout = QVBoxLayout(self.client_placeholder)
            ph_layout.setAlignment(Qt.AlignCenter)
            
            icon = QLabel()
            icon.setPixmap(QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            text = QLabel("Busca un cliente y selecciona uno para ver sus direcciones y órdenes.")
            text.setAlignment(Qt.AlignCenter)
            text.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")
            
            ph_layout.addWidget(icon)
            ph_layout.addWidget(text)
            self.client_info_layout.addWidget(self.client_placeholder)

    def _load_books_and_additives(self):
        r_books = http_get(API_URL_BOOKS)
        if r_books and r_books.status_code == 200:
            self.books_data = r_books.json()
        
        r_additives = http_get(API_URL_ADITIVOS)
        if r_additives and r_additives.status_code == 200:
            self.additives_data = r_additives.json()

    def _create_order_widget(self, order):
        widget = QWidget()
        widget.setObjectName("orderCard")
        widget.mousePressEvent = lambda event: self._show_order_summary(order['idOrder'])
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        header_layout = QHBoxLayout()
        
        order_id = QLabel(f"Orden #{order['idOrder']}")
        order_id.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        
        order_type = QLabel(f"📦 {order['type'].title()}")
        order_type.setStyleSheet("color: #666; font-size: 13px;")
        
        order_status = QLabel("✅ Completada" if order['done'] else "🟡 Pendiente")
        order_status.setStyleSheet("color: #666; font-size: 13px;")
        
        header_layout.addWidget(order_id)
        header_layout.addStretch()
        header_layout.addWidget(order_type)
        header_layout.addWidget(order_status)
        
        layout.addLayout(header_layout)
        
        details_layout = QVBoxLayout()
        details_layout.setSpacing(3)
        
        if order['address']:
            address_label = QLabel(f"📍 {order['address']}")
            address_label.setStyleSheet("color: #555; font-size: 12px;")
            address_label.setWordWrap(True)
            details_layout.addWidget(address_label)
        
        if order['delivery_zone']:
            delivery_label = QLabel(f"🚗 {order['delivery_zone']} (${order['delivery_price']})")
            delivery_label.setStyleSheet("color: #555; font-size: 12px;")
            details_layout.addWidget(delivery_label)
        
        price_label = QLabel(f"💰 ${order['total_price']}")
        price_label.setStyleSheet("color: #555; font-size: 12px;")
        details_layout.addWidget(price_label)
        
        dates_label = QLabel(f"📅 Pedido: {order['order_date']} | Entrega: {order['delivery_date']}")
        dates_label.setStyleSheet("color: #555; font-size: 11px;")
        details_layout.addWidget(dates_label)
        
        layout.addLayout(details_layout)
        
        widget.setStyleSheet("""
            QWidget#orderCard {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background: #f9f9f9;
                margin: 2px;
            }
            QWidget#orderCard:hover {
                background: #f0f0f0;
                border: 1px solid #007acc;
            }
        """)
        
        return widget

    def _show_order_summary(self, order_id):
        url = f"{API_URL_ORDERS}{order_id}/full_details/"
        r = http_get(url)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo obtener la información de la orden.")
            return
        
        order_data = r.json()
        
        mensaje = self._format_order_summary(order_data)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(mensaje)
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"📋 Vale de Orden #{order_id}")
        msg_box.setText(f"✅ Vale copiado al portapapeles\n\n{mensaje}")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setDefaultButton(QMessageBox.Ok)
        
        msg_box.setStyleSheet("""
            QMessageBox { 
                min-width: 600px; 
                min-height: 400px;
            }
            QMessageBox QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
        """)
        
        msg_box.exec()


    def _format_order_summary(self, order_data):
        mensaje = f"🔰 ORDEN No. {order_data['idOrder']}\n\n"
        mensaje += f"🗓 Fecha: {order_data['order_date']}\n"
        mensaje += f"🗓 Fecha aproximada de entrega: {order_data['delivery_date']}\n\n"
        
        for book_info in order_data['books']:
            book = book_info['book']
            additives = book_info['additives']
            discount = book_info['discount']
            cantidad = book_info['quantity']
            
            titulo = book.get("title", "Desconocido")
            autor = book.get("author", "Sin autor")
            
            caratula_name = "Tapa Normal"
            caratula_price = 0
            service_additives = []
            
            for additive in additives:
                if additive["name"].lower().startswith("carátula"):
                    caratula_name = additive['name']
                    caratula_price = additive['price']
                elif additive["name"].lower().startswith("servicio"):
                    service_additives.append(additive)
            
            base_price = book.get('number_pages', 0)
            
            precio_base_caratula = base_price + caratula_price
            cup_price_base = convert_to_currency(precio_base_caratula, 'USD', 'CUP')
            mlc_price_base = convert_to_currency(precio_base_caratula, 'USD', 'MLC')
            
            mensaje += f"📚 Título: {titulo}\n"
            mensaje += f"👤 Autor: {autor}\n"
            if cantidad > 1:
                mensaje += f"🔢 Cantidad: {cantidad}\n"
            
            mensaje += f"💰 {caratula_name}: {precio_base_caratula} USD | {cup_price_base} CUP | {mlc_price_base} MLC\n"
            
            for service in service_additives:
                service_cup = convert_to_currency(service['price'], 'USD', 'CUP')
                service_mlc = convert_to_currency(service['price'], 'USD', 'MLC')
                mensaje += f"💰 {service['name']}: {service['price']} USD | {service_cup} CUP | {service_mlc} MLC\n"
            
            if discount != 0:
                mensaje += f"📉 Descuento: {discount}%\n"
            else:
                mensaje += "\n"
            
            precio_base_con_descuento = precio_base_caratula * (1 - discount / 100))
            precio_servicios = sum(service['price'] for service in service_additives)
            precio_unitario_final = precio_base_con_descuento + precio_servicios
            precio_total_libro = precio_unitario_final * cantidad

            unitario_cup = convert_to_currency(precio_unitario_final, 'USD', 'CUP')
            unitario_mlc = convert_to_currency(precio_unitario_final, 'USD', 'MLC')
            libro_total_cup = convert_to_currency(precio_total_libro, 'USD', 'CUP')
            libro_total_mlc = convert_to_currency(precio_total_libro, 'USD', 'MLC')
            
            if cantidad > 1:
                mensaje += f"💰 Precio unitario: {precio_unitario_final:.2f} USD | {unitario_cup} CUP | {unitario_mlc} MLC\n"
                mensaje += f"💰 Total libro: {precio_total_libro:.2f} USD | {libro_total_cup} CUP | {libro_total_mlc} MLC\n\n"
            else:
                mensaje += f"💰 Total libro: {precio_total_libro:.2f} USD | {libro_total_cup} CUP | {libro_total_mlc} MLC\n\n"
        
        total_final = order_data['total_price']
        total_cup = convert_to_currency(total_final, 'USD', 'CUP')
        total_mlc = convert_to_currency(total_final, 'USD', 'MLC')
        mensaje += f"💰 Total a pagar: {total_final:.2f} USD | {total_cup} CUP | {total_mlc} MLC\n\n"
        
        mensaje += f"💰 Pago por adelantado: {order_data['payment_advance']:.2f} USD\n"
        mensaje += f"💰 Pago pendiente: {order_data['outstanding_payment']:.2f} USD\n\n"
        
        if order_data['delivery_price'] > 0:
            delivery_cup = convert_to_currency(order_data['delivery_price'], 'USD', 'CUP')
            delivery_mlc = convert_to_currency(order_data['delivery_price'], 'USD', 'MLC')
            mensaje += f"🚗 Mensajería: {order_data['delivery_price']:.2f} USD\n\n"
        else:
            mensaje += f"🚗 Mensajería: Recogida\n\n"

        mensaje += "👤Información del contacto:\n"
        mensaje += f"— Nombre: {order_data['client']['name']}\n"
        mensaje += f"— Carnet de Identidad: {order_data['client']['identity']}\n"
        mensaje += f"— Teléfono: {order_data['client']['phone_number']}\n"
        
        if (order_data['delivery_zone'] and 
            'recogida' not in order_data['delivery_zone'].lower() and 
            order_data['address']):
            mensaje += f"— Dirección de entrega: {order_data['address']}\n"
        
        mensaje += f"— Servicio de entrega: {order_data['type']}\n"
        mensaje += f"— Método de pago: {order_data['pay_method']}\n\n"
        
        mensaje += "🔆 Conoce nuestros trabajos en instagram.com/moe.libros"
        
        return mensaje

    def _show_detailed_order_summary(self, mensaje, order_id):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Vale de Orden #{order_id}")
        dialog.setMinimumWidth(700)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout(dialog)
        title_layout = QHBoxLayout()
        title_label = QLabel(f"📋 Vale de Orden #{order_id}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(mensaje)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("primaryBtn")
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
#* ------------------- STYLE -------------------
    def _apply_styles(self):
        self.setObjectName("clientsPage")
        self.setStyleSheet("""
        QWidget#clientsPage {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f8f8, stop:1 #e0e0e0);
        }

        QFrame#card {
            background: #fff;
            border-radius: 10px;
            padding: 20px;
            
        }

        QLabel {
            color: #222;
        }

        QLineEdit, QSpinBox {
            background: #fafafa;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
        }
        

        QPushButton#primaryBtn {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #333, stop:1 #000);
            color: white;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            border: 1px solid #111;
        }
        QPushButton#primaryBtn:hover {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #444, stop:1 #111);
            border: 1px solid #222;
        }

        QPushButton#primaryBtn:pressed {
            background-color: #000;
            border: 1px solid #000;
            padding-top: 11px;  
            padding-bottom: 9px;
        }

        QPushButton#secondaryBtn {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #333, stop:1 #000);
            color: white;
            font-weight: 600;
            padding: 5px 10px;
            border-radius: 8px;
            border: 1px solid #111;
        }
        QPushButton#secondaryBtn:hover {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #444, stop:1 #111);
            border: 1px solid #222;
        }
         QPushButton#secondaryBtn:pressed {
            background-color: #000;
            border: 1px solid #000;
            padding-top: 11px;   
            padding-bottom: 9px;
        }


        QPushButton#dangerBtn {
            background-color: #b91c1c;
            color: white;
            border-radius: 6px;
            padding: 8px 14px;
        }
        QPushButton#dangerBtn:hover {
            background-color: #dc2626;
        }

        QComboBox {
            background: #fafafa;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
        }
        QComboBox:hover {
            border: 1px solid #888;
        }
        
        
        
        """)

