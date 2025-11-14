import sys
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QFormLayout, QListWidget, QListWidgetItem, QDialog,
    QCompleter, QSpinBox, QTabWidget, QGroupBox, QListView, QSizePolicy,
    QDialogButtonBox, QCheckBox, QScrollArea, QDateEdit,  QApplication, QFrame)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon, QPixmap,  QStandardItemModel, QStandardItem
from datetime import date, datetime
from frontend.utils import http_get, http_post, http_delete, http_put, make_icon_label
from frontend.urls import (
    API_URL_ORDERS, API_URL_CLIENTES, API_URL_MENSAJERIAS, API_URL_BOOKS,
    API_URL_ADITIVOS, API_URL_REQUESTED_BOOKS, API_URL_REQUESTED_BOOK_ADDITIVES,
    API_URL_BOOK_ON_ORDER
)
from frontend.price.get_rates import convert_to_currency
from frontend.price.price import calculate_price
from frontend.price_service import PriceService
import json
import requests

#? ------------------------------
#? Diálogo para crear nuevo cliente
#? ------------------------------
class NewClientDialog(QDialog):
    def __init__(self, name=""):
        super().__init__()
        self.setWindowTitle("Nuevo cliente")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(name)
        self.identity_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        layout.addRow("👤 Nombre:", self.name_edit)
        layout.addRow("🪪 Carnet de identidad:", self.identity_edit)
        layout.addRow("📞 Teléfono:", self.phone_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Guardar")
        cancel_btn = QPushButton("Cancelar")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "identity": self.identity_edit.text().strip(),
            "phone_number": self.phone_edit.text().strip()
        }

#? --------------------------------
#? Diálogo para libros de una orden
#? --------------------------------
class BookItemWidget(QWidget):
    def __init__(self, book_entry):
        super().__init__()
        self.book_entry = book_entry

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(3)

        title_label = QLabel(f"<b>{book_entry['title']}</b> — {book_entry['author']} ")
        title_label.setStyleSheet("font-size: 14px; color: #333;")
        layout.addWidget(title_label)

        quantity_discount_label = QLabel(f"Cantidad: {book_entry['quantity']} | Descuento: {book_entry['discount']}%")
        quantity_discount_label.setStyleSheet("font-size: 12px; color: #555;")
        layout.addWidget(quantity_discount_label)

        additives = book_entry.get("additives_names", [])
        if additives:
            additives_label = QLabel("Servicios extras: " + ", ".join(additives))

            additives_label.setStyleSheet("font-size: 12px; color: #777; font-style: italic;")
            layout.addWidget(additives_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #F9F9F9;
                border: none;
                border-radius: 6px;
            }
        """)

class OrderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Órdenes")
        self.layout = QVBoxLayout(self)
        self._apply_styles()

        header_layout = QHBoxLayout()
        header_icon = QLabel()
        header_icon.setPixmap(
            QPixmap("frontend/icons/orders.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        header_title = QLabel("Órdenes")
        header_title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #333;
        """)

        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        line = QLabel()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #d0d0d0; margin: 8px 0;")

        self.layout.addLayout(header_layout)
        self.layout.addWidget(line)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Pestañas
        self.add_tab = QWidget()
        self.modify_tab = QWidget()
        self.delete_tab = QWidget()
        self.tabs.addTab(self.add_tab, "Añadir Orden")
        self.tabs.addTab(self.modify_tab, "Modificar Orden")
        self.tabs.addTab(self.delete_tab, "Eliminar Orden")

        # Variables
        self.selected_books = []
        self.order_data = None
        self.clients_data = []

        # Inicializar cada pestaña
        self.selected_additives = []
        self._setup_add_tab()
        self._setup_modify_tab()
        self._setup_delete_tab()

        # Cargar datos
        self._load_clients()
        self._load_deliveries()
        self._load_books()
        self._load_additives()


#* -------------------- CARGAR DATOS DESDE BACKEND --------------------
    def _load_clients(self):
        self.clients_data = []
        r = http_get(API_URL_CLIENTES)
        if r and r.status_code == 200:
            self.clients_data = r.json()

    def _load_deliveries(self):
        r = http_get(API_URL_MENSAJERIAS)
        if r and r.status_code == 200:
            self.mensajerias_data = r.json()  # Guardar los datos
            zonas = [m["zone"] for m in self.mensajerias_data]
            model = QStandardItemModel()
            for z in zonas:
                item = QStandardItem(z)
                model.appendRow(item)
            self.add_delivery_completer.setModel(model)
            self.add_delivery_completer.activated.connect(self._on_delivery_selected)

    def _load_books(self):
        r = http_get(API_URL_BOOKS)
        if r and r.status_code == 200:
            self.books_data = r.json()

            titles = [f"{b['title']} — {b['author']} — Formato: {b['printing_format']}" for b in self.books_data]
            model = QStandardItemModel()
            for title in titles:
                model.appendRow(QStandardItem(title))
            self.book_completer.setModel(model)
            self.book_completer.setModel(model)
            self.book_completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.book_completer.setFilterMode(Qt.MatchContains)
            self.book_completer.setCompletionMode(QCompleter.PopupCompletion)
            self.book_completer.popup().setStyleSheet("""
                QListView {
                    background-color: #ffffff;
                    border: 1px solid #b0b0b0;
                    border-radius: 6px;
                    font-size: 14px;
                    padding: 4px;
                    selection-background-color: #e3f2fd;
                    selection-color: #000000;
                }
                QListView::item {
                    padding: 6px 10px;
                }
                QListView::item:selected {
                    background-color: #bbdefb;
                    border-radius: 4px;
                }
            """)

    def _load_additives(self):
        r = http_get(API_URL_ADITIVOS)
        if r and r.status_code == 200:
            self.additives_data = r.json()
        else:
            self.additives_data = []
        service_additives = [a for a in self.additives_data if a["name"].lower().startswith("servicio")]
        self.add_type_combo.clear()
        self.add_type_combo.addItem("Regular")
        for additive in service_additives:
            self.add_type_combo.addItem(additive["name"])


#* -------------------- PESTAÑA AÑADIR ORDEN --------------------
    def _setup_add_tab(self):        
        scroll = QScrollArea(self.add_tab)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        #? -------------------- SECCIÓN CLIENTE --------------------
        client_group = QGroupBox("Datos del cliente")
        client_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #b8b8b8;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
        """)
        client_layout = QFormLayout(client_group)
        client_layout.setLabelAlignment(Qt.AlignLeft)
        client_layout.setFormAlignment(Qt.AlignLeft)
        client_layout.setSpacing(12)

        # Campo cliente
        self.add_client_input = QLineEdit()
        self.add_client_input.setPlaceholderText("Buscar cliente por nombre o carnet de identidad...")

        self.client_completer = QCompleter()
        self.client_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.client_completer.setFilterMode(Qt.MatchContains)
        
        self.add_client_input.setCompleter(self.client_completer)
        self.add_client_input.textChanged.connect(self._update_client_completer)

        client_layout.addRow(make_icon_label("frontend/icons/client.png", "Cliente"), self.add_client_input)

        # --- Zona / Municipio con autocompletado ---
        self.add_delivery_input = QLineEdit()
        self.add_delivery_input.setPlaceholderText("Escribe para buscar zona o municipio...")
        self.add_delivery_completer = QCompleter()
        self.add_delivery_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.add_delivery_completer.setFilterMode(Qt.MatchContains)
        self.add_delivery_input.setCompleter(self.add_delivery_completer)

        # Conectar el cambio de texto para detectar cuando el usuario escribe
        self.add_delivery_input.textChanged.connect(self._on_delivery_text_changed)

        client_layout.addRow(make_icon_label("frontend/icons/zone.png", "Municipio"), self.add_delivery_input)

        # Dirección
        self.add_address_input = QLineEdit()
        self.add_address_input.setPlaceholderText("Dirección exacta de entrega")
        client_layout.addRow(make_icon_label("frontend/icons/description.png", "Dirección exacta"), self.add_address_input)

        # Método de pago
        self.add_payment_combo = QComboBox()
        self.add_payment_combo.addItems(["CUP", "USD", "EUR", "Zelle", "USDT", "Bitcoin"])
        client_layout.addRow(make_icon_label("frontend/icons/card.png", "Método de pago"), self.add_payment_combo)

        main_layout.addWidget(client_group)

        #? -------------------- SECCIÓN LIBROS --------------------
        books_group = QGroupBox("Libros y servicios extras del pedido")
        books_group.setStyleSheet(client_group.styleSheet())
        books_layout = QVBoxLayout(books_group)
        books_layout.setAlignment(Qt.AlignTop)
        books_layout.setSpacing(10)

        self.add_book_input = QLineEdit()
        self.add_book_input.setPlaceholderText("Escribe el título del libro...")
        self.book_completer = QCompleter()
        self.book_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.add_book_input.setCompleter(self.book_completer)
        books_layout.addRow = books_layout.addWidget
        books_layout.addWidget(make_icon_label("frontend/icons/books.png", "Libros"))
        books_layout.addWidget(self.add_book_input)

        # Cantidad de libros
        quantity_group = QWidget()
        quantity_layout = QHBoxLayout(quantity_group)
        quantity_layout.setContentsMargins(0, 0, 0, 0)
        quantity_layout.setSpacing(8)

        quantity_icon = QLabel()
        quantity_icon.setPixmap(QPixmap("frontend/icons/quantity.png").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        quantity_label = QLabel("Cantidad")
        quantity_label.setStyleSheet("font-weight: 500;")

        self.add_quantity_spin = QSpinBox()
        self.add_quantity_spin.setRange(1, 100)
        self.add_quantity_spin.setValue(1)
        self.add_quantity_spin.setFixedWidth(120)
        self.add_quantity_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #C0C0C0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #FAFAFA;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
            }
        """)

        quantity_layout.addWidget(quantity_icon)
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.add_quantity_spin)
        quantity_layout.addStretch()

        books_layout.addWidget(quantity_group)

        # Servicios extras
        books_layout.addWidget(make_icon_label("frontend/icons/extra.png", "Servicios extras"))
        self.select_services_btn = QPushButton("Seleccionar servicios extras")
        self.select_services_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                border: 1px solid #C0C0C0;
                border-radius: 6px;
                padding: 6px 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
            }
        """)
        self.select_services_btn.clicked.connect(self._open_additives_dialog)
        books_layout.addWidget(self.select_services_btn)

        # Descuento
        discount_group = QWidget()
        discount_layout = QHBoxLayout(discount_group)
        discount_layout.setContentsMargins(0, 0, 0, 0)
        discount_layout.setSpacing(8)

        # Label con ícono + texto
        discount_label = QWidget()
        discount_label_layout = QHBoxLayout(discount_label)
        discount_label_layout.setContentsMargins(0, 0, 0, 0)
        discount_label_layout.setSpacing(5)

        icon = QLabel()
        pixmap = QPixmap("frontend/icons/discount.png").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon.setPixmap(pixmap)

        text_label = QLabel("Descuento")
        text_label.setStyleSheet("font-weight: 500;")

        discount_label_layout.addWidget(icon)
        discount_label_layout.addWidget(text_label)

        # SpinBox
        self.add_discount_spin = QSpinBox()
        self.add_discount_spin.setRange(0, 100)
        self.add_discount_spin.setSuffix(" %")
        self.add_discount_spin.setFixedWidth(120)
        self.add_discount_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #C0C0C0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #FAFAFA;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
            }
        """)

        discount_layout.addWidget(discount_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        discount_layout.addWidget(self.add_discount_spin, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        discount_layout.addStretch()

        books_layout.addWidget(discount_group)

        add_book_btn = QPushButton("Añadir libro al pedido")
        add_book_btn.setObjectName("primaryBtn")
        add_book_btn.clicked.connect(self._add_book_add_tab)
        books_layout.addWidget(add_book_btn)

        books_layout.addWidget(QLabel("Libros añadidos:"))
        self.add_selected_books_list = QListWidget()
        self.add_selected_books_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.add_selected_books_list.setMinimumHeight(250)
        self.add_selected_books_list.setSpacing(5)
        books_layout.addWidget(self.add_selected_books_list)

        # Botón para eliminar libro seleccionado
        self.remove_book_btn = QPushButton("Eliminar libro seleccionado")
        self.remove_book_btn.setObjectName("dangerBtn")
        self.remove_book_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8d7da;
                border: 1px solid #f5c2c7;
                border-radius: 6px;
                padding: 6px 10px;
                color: #721c24;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f1b0b7;
            }
        """)
        self.remove_book_btn.clicked.connect(self._remove_selected_book_add_tab)
        books_layout.addWidget(self.remove_book_btn)


        main_layout.addWidget(books_group)

        #? -------------------- SECCIÓN DETALLES DEL PEDIDO --------------------
        details_group = QGroupBox("Detalles del pedido")
        details_group.setStyleSheet(client_group.styleSheet())
        details_layout = QFormLayout(details_group)
        details_layout.setLabelAlignment(Qt.AlignLeft)
        details_layout.setFormAlignment(Qt.AlignLeft)
        details_layout.setSpacing(12)

        # Tipo de pedido
        self.add_type_combo = QComboBox()
        self.add_type_combo.addItems([self.add_type_combo])
    
        self.add_type_combo.currentIndexChanged.connect(self._update_delivery_date_add)
        details_layout.addRow(make_icon_label("frontend/icons/tipo.png", "Tipo de pedido"), self.add_type_combo)

        # Costo de mensajería (solo lectura)
        self.delivery_price_label = QLabel("0.00 $")
        details_layout.addRow(make_icon_label("frontend/icons/delivery.png", "Costo de mensajería"), self.delivery_price_label)

        # Fecha de realizado
        self.add_order_date = QDateEdit()
        self.add_order_date.setDate(QDate.currentDate())
        self.add_order_date.setCalendarPopup(True)
        self.add_order_date.setReadOnly(True)
        self.add_order_date.setButtonSymbols(QDateEdit.NoButtons)
        details_layout.addRow(make_icon_label("frontend/icons/fecha1.png", "Fecha de realizado"), self.add_order_date)

        # Fecha aproximada de entrega 
        self.add_delivery_date = QDateEdit()
        self.add_delivery_date.setDate(QDate.currentDate().addDays(5))
        self.add_delivery_date.setCalendarPopup(True)
        self.add_delivery_date.setReadOnly(True)
        self.add_delivery_date.setButtonSymbols(QDateEdit.NoButtons)
        details_layout.addRow(make_icon_label("frontend/icons/fecha2.png", "Fecha aproximada de entrega"), self.add_delivery_date)
        
        # Precio total
        self.total_price_label = QLabel("0.00 $")
        details_layout.addRow(make_icon_label("frontend/icons/price.png", "Total"), self.total_price_label)

        # Pago adelantado
        self.add_payment_advance_edit = QLineEdit()
        self.add_payment_advance_edit.setPlaceholderText("0.00")
        self.add_payment_advance_edit.textChanged.connect(self._update_totals_add)
        self.add_payment_advance_edit.textEdited.connect(self._update_totals_add)

        details_layout.addRow(make_icon_label("frontend/icons/money.png", "Pago adelantado"), self.add_payment_advance_edit)

        # Pago pendiente
        self.add_outstanding_payment_label = QLabel("0.00 $")
        details_layout.addRow(make_icon_label("frontend/icons/pending.png", "Pago pendiente"), self.add_outstanding_payment_label)

        # Botón crear orden
        create_order_btn = QPushButton("Crear orden")
        create_order_btn.setObjectName("primaryBtn")
        create_order_btn.clicked.connect(self._create_order_add_tab)
        details_layout.addRow(create_order_btn)

        main_layout.addWidget(details_group)

        # --- Montar todo en el scroll ---
        scroll.setWidget(container)

        # --- Asignar layout final a la pestaña ---
        tab_layout = QVBoxLayout(self.add_tab)
        tab_layout.addWidget(scroll)

#* -------------------- FUNCIONES DE AÑADIR ORDEN --------------------
    def _calculate_book_price(self, book_entry):
        book_data = None
        for b in self.books_data:
            if b['idBook'] == book_entry.get('book_id'):
                book_data = b
                break
        
        if not book_data:
            return 0
        
        book_additives = []
        for add_id in book_entry.get('additives', []):
            for additive in self.additives_data:
                if additive['idAdditive'] == add_id:
                    book_additives.append(additive)
                    break
        caratula_price = 0
        other_additives_price = 0
        for additive in book_additives:
            if "carátula" in additive.get("name", "").lower():
                caratula_price = additive.get("price", 0)
            else:
                other_additives_price += additive.get("price", 0)

        number_of_pages = book_data.get('number_pages', 0)
        color_pages = book_data.get("color_pages", 0)
        printing_format = book_data.get("printing_format", "normal").lower()
        book_base_price = calculate_price(number_of_pages, color_pages, printing_format)

        total_price_before_discount = book_base_price + caratula_price + other_additives_price
        discount_percentage = book_entry.get('discount', 0)
        if discount_percentage > 0:
            total_price_before_discount *= (1 - discount_percentage / 100)
        final_price = total_price_before_discount * book_entry.get('quantity', 1)
        
        return final_price

    def _update_delivery_date_add(self):
        today = QDate.currentDate()
        tipo = self.add_type_combo.currentText().strip().lower()
       
        if tipo == "servicio regular":
            fecha_entrega = today.addDays(30)

        elif tipo in ("servicio express", "servicio premium express"):
            objetivo = 7 if tipo == "servicio express" else 2
            dias_habiles = 0
            fecha_entrega = today

            while dias_habiles < objetivo:
                fecha_entrega = fecha_entrega.addDays(1)
                if fecha_entrega.dayOfWeek() < 6:
                    dias_habiles += 1

        else:
            fecha_entrega = today.addDays(30)
        self.add_delivery_date.setDate(fecha_entrega)


    def _on_delivery_selected(self, text):
        selected_zone = text.strip()
        
        for m in self.mensajerias_data:
            if m["zone"].strip() == selected_zone:
                price = m.get("price", 0)
                self.delivery_price_label.setText(f"{price:.2f} $")
                self._update_totals_add()
                return
        
        self.delivery_price_label.setText("0.00 $")
        self._update_totals_add()

    def _on_delivery_text_changed(self, text):
        if text.strip():
            for m in self.mensajerias_data:
                if m["zone"].strip().lower() == text.strip().lower():
                    price = m.get("price", 0)
                    self.delivery_price_label.setText(f"{price:.2f} $")
                    self._update_totals_add()
                    return
        self.delivery_price_label.setText("0.00 $")
        self._update_totals_add()

    def _update_client_completer(self, text):
        text = text.strip()
        if not text:
            self.client_completer.setModel(QStandardItemModel())
            return

        filtered = []
        for c in self.clients_data:
            name_match = text.lower() in c.get('name', '').lower()
            identity_match = text.lower() in c.get('identity', '').lower()
            phone_match = text.lower() in c.get('phone_number', '').lower()
            
            if name_match or identity_match or phone_match:
                display_text = f"{c.get('name', 'N/A')} — CI: {c.get('identity', 'N/A')} — Tel: {c.get('phone_number', 'N/A')}"
                filtered.append((display_text, c))

        model = QStandardItemModel()
        for display_text, client_data in filtered:
            item = QStandardItem(display_text)
            item.setData(client_data, Qt.UserRole)
            model.appendRow(item)

        self.client_completer.setModel(model)
        self.client_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.client_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.client_completer.setFilterMode(Qt.MatchContains)
        try:
            self.client_completer.activated.disconnect()
        except:
            pass
        self.client_completer.activated.connect(self._select_client_from_completer)

    def _select_client_from_completer(self, text_value):
        model = self.client_completer.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.text() == text_value:
                client_data = item.data(Qt.UserRole)
                if client_data:
                    display_text = f"{client_data['name']} — CI: {client_data.get('identity', 'N/A')} — Tel: {client_data.get('phone_number', 'N/A')}"
                    self.add_client_input.setText(display_text)
                break

    

    def _update_aditivos_display(self):
        selected_names = [item.text() for item in self.add_aditivos_list.selectedItems()]
        display = ", ".join(selected_names) if selected_names else "Seleccionar aditivos..."
        self.add_aditivos_combo.setCurrentText(display)


    def _open_additives_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar servicios extras")
        layout = QVBoxLayout(dialog)

        checkboxes = []
        for additive in getattr(self, "additives_data", []):
            cb = QCheckBox(f"{additive['name']} (${additive['price']})")
            cb.setChecked(additive in self.selected_additives)
            layout.addWidget(cb)
            checkboxes.append((cb, additive))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            self.selected_additives = [a for cb, a in checkboxes if cb.isChecked()]
            selected_names = [a["name"] for a in self.selected_additives]
            if selected_names:
                self.select_services_btn.setText(f"Seleccionados: " + ", ".join(selected_names[:2]) + ("..." if len(selected_names) > 2 else ""))
            else:
                self.select_services_btn.setText("Seleccionar servicios extras")

            self._update_totals_add()


    def _remove_selected_book_add_tab(self):
        selected_items = self.add_selected_books_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un libro para eliminar.")
            return

        for item in selected_items:
            row = self.add_selected_books_list.row(item)
            self.add_selected_books_list.takeItem(row)
            if row < len(self.selected_books):
                del self.selected_books[row]

        self._update_totals_add()
        QMessageBox.information(self, "Eliminado", "Libro eliminado correctamente del pedido.")


    def _update_totals_add(self):
        delivery_price = 0
        delivery_text = self.delivery_price_label.text().replace('$', '').strip()
        try:
            delivery_price = float(delivery_text) if delivery_text else 0
        except ValueError:
            delivery_price = 0

        total_books_price = sum(self._calculate_book_price(book) for book in self.selected_books)
        total_order_price = total_books_price + delivery_price
        
        order_calculation = PriceService.calculate_order_price(
            selected_books=self.selected_books,
            books_data=self.books_data,
            additives_data=self.additives_data,
            delivery_price=delivery_price
        )
        
        try:
            payment_advance = float(self.add_payment_advance_edit.text() or 0)
        except ValueError:
            payment_advance = 0.0
        
        outstanding = PriceService.calculate_outstanding_payment(
            order_calculation['total_price'], 
            payment_advance
        )
        
        self.total_price_label.setText(f"{order_calculation['total_price']:.2f} $")
        self.add_outstanding_payment_label.setText(f"{outstanding:.2f} $")

    def _get_order_summary_for_clipboard(self, order_id):
        delivery_text = self.delivery_price_label.text().replace('$', '').strip()
        try:
            delivery_price = float(delivery_text) if delivery_text else 0
        except ValueError:
            delivery_price = 0
        
        order_calculation = PriceService.calculate_order_price(
            selected_books=self.selected_books,
            books_data=self.books_data,
            additives_data=self.additives_data,
            delivery_price=delivery_price
        )
        
        try:
            payment_advance = float(self.add_payment_advance_edit.text() or 0)
        except ValueError:
            payment_advance = 0.0
        
        outstanding = PriceService.calculate_outstanding_payment(
            order_calculation['total_price'], 
            payment_advance
        )
        
        mensaje = f"🔰 ORDEN No. {order_id}\n\n"
        mensaje += f"🗓 Fecha: {self.add_order_date.date().toString('dd-MM-yyyy')}\n"
        mensaje += f"🗓 Fecha aproximada de entrega: {self.add_delivery_date.date().toString('dd-MM-yyyy')}\n\n"
        
        for i, book_entry in enumerate(self.selected_books):
            book_calc = order_calculation['books_prices'][i]
            
            titulo = book_entry.get("title", "Desconocido")
            autor = book_entry.get("author", "Sin autor")
            cantidad = book_entry.get("quantity", 1)
            
            book_data = None
            for b in self.books_data:
                if b['idBook'] == book_entry.get('book_id'):
                    book_data = b
                    break
            
            caratula_name = "Tapa Normal"
            caratula_price = 0
            service_additives = []
            
            for add_id in book_entry.get("additives", []):
                for additive in self.additives_data:
                    if add_id == additive['idAdditive']:
                        if additive["name"].lower().startswith("carátula"):
                            caratula_name = additive['name']
                            caratula_price = additive['price']
                        elif additive["name"].lower().startswith("servicio"):
                            service_additives.append(additive)

            number_of_pages = book_data.get('number_pages', 0)
            color_pages = book_data.get("color_pages", 0)
            printing_format = book_data.get("printing_format", "normal").lower()
            precio_regular = calculate_price(number_of_pages, color_pages, printing_format) + caratula_price

            cup_price = convert_to_currency(precio_regular, 'USD', 'CUP')
            mlc_price = convert_to_currency(precio_regular, 'USD', 'MLC')
            
            mensaje += f"📚 Título: {titulo}\n"
            mensaje += f"👤 Autor: {autor}\n"
            if cantidad > 1:
                mensaje += f"🔢 Cantidad: {cantidad}\n"
            
            mensaje += f"💰 {caratula_name}: {precio_regular} USD | {cup_price} CUP | {mlc_price} MLC\n"
            
            for service in service_additives:
                service_cup = convert_to_currency(service['price'], 'USD', 'CUP')
                service_mlc = convert_to_currency(service['price'], 'USD', 'MLC')
                mensaje += f"💰 {service['name']}: {service['price']} USD | {service_cup} CUP | {service_mlc} MLC\n"
            

            discount = book_entry.get("discount", 0)
            if discount != 0:
                mensaje += f"📉 Descuento: {discount}%\n"
            else:
                mensaje += "\n"
            
            libro_total = book_calc['price']
            libro_total_cup = convert_to_currency(libro_total, 'USD', 'CUP')
            libro_total_mlc = convert_to_currency(libro_total, 'USD', 'MLC')
            
            if cantidad > 1:
                precio_unitario = libro_total / cantidad
                unitario_cup = convert_to_currency(precio_unitario, 'USD', 'CUP')
                unitario_mlc = convert_to_currency(precio_unitario, 'USD', 'MLC')
                mensaje += f"💰 Precio unitario: {precio_unitario:.2f} USD | {unitario_cup} CUP | {unitario_mlc} MLC\n"
                mensaje += f"💰 Total libro: {libro_total:.2f} USD | {libro_total_cup} CUP | {libro_total_mlc} MLC\n\n"
        
        total_final = order_calculation['total_price']
        total_cup = convert_to_currency(total_final, 'USD', 'CUP')
        total_mlc = convert_to_currency(total_final, 'USD', 'MLC')
        mensaje += f"💰 Total a pagar: {total_final:.2f} USD | {total_cup} CUP | {total_mlc} MLC\n\n"
        
        mensaje += f"💰 Pago por adelantado: {payment_advance:.2f} USD\n"
        mensaje += f"💰 Pago pendiente: {outstanding:.2f} USD\n\n"
        
        if delivery_price > 0:
            delivery_cup = convert_to_currency(delivery_price, 'USD', 'CUP')
            delivery_mlc = convert_to_currency(delivery_price, 'USD', 'MLC')
            mensaje += f"🚗 Mensajería: {delivery_price:.2f} USD\n\n"
        else:
             mensaje += f"🚗 Mensajería: Recogida\n\n"

        mensaje += "👤Información del contacto:\n"
        mensaje += f"— Nombre: {self.add_client_input.text().split("—")[0]}\n"
        mensaje += f"— Carnet de Identidad: {self._get_selected_client_identity()}\n"
        mensaje += f"— Teléfono: {self._get_selected_client_phone()}\n"
        
        delivery_text_lower = self.add_delivery_input.text().lower()
        if 'recogida' not in delivery_text_lower:
            mensaje += f"— Dirección de entrega: {self.add_address_input.text()}\n"
        
        mensaje += f"— Servicio de entrega: {self.add_type_combo.currentText()}\n"
        mensaje += f"— Método de pago: {self.add_payment_combo.currentText()}\n\n"
        
        mensaje += "🔆 Conoce nuestros trabajos en instagram.com/moe.libros"
        
        return mensaje

    def _add_book_add_tab(self):
        book_text = self.add_book_input.text().strip()
        if not book_text:
            QMessageBox.warning(self, "Error", "Debe escribir o seleccionar un libro.")
            return
        book = next(
            (b for b in self.books_data
            if book_text.lower() in f"{b['title']} — {b['author']} — Formato: {b['printing_format']}".lower()),
            None
        )
        if not book:
            QMessageBox.warning(self, "Error", "El libro especificado no existe.")
            return

        book_entry = {
            "book_id": book["idBook"],
            "title": book["title"],
            "author": book["author"],
            "additives": [a["idAdditive"] for a in self.selected_additives],
            "additives_names": [a["name"] for a in self.selected_additives],
            "discount": self.add_discount_spin.value(),
            "quantity": self.add_quantity_spin.value()
        }

        self.selected_books.append(book_entry)

        additives_text = (
            ", ".join(book_entry["additives_names"])
            if book_entry["additives_names"]
            else "Sin servicios extras"
        )

        item_text = (
        f"{book['title']} — {book['author']} | "
        f"{additives_text} | Descuento: {book_entry['discount']}% | "
        f"Cantidad: {book_entry['quantity']}"
        )

        item = QListWidgetItem()
        widget = BookItemWidget(book_entry)
        item.setSizeHint(widget.sizeHint())
        self.add_selected_books_list.addItem(item)
        self.add_selected_books_list.setItemWidget(item, widget)
        self.add_book_input.clear()
        self.selected_additives = []
        self.select_services_btn.setText("Seleccionar servicios extras")
        self.add_discount_spin.setValue(0)
        self._update_totals_add()

    def _create_order_add_tab(self):
        client_name = self.add_client_input.text().strip()
        if not client_name:
            QMessageBox.warning(self, "Error", "Debe escribir el nombre del cliente.")
            return
        
        if not self.selected_books:
            QMessageBox.warning(self, "Error", "Debe añadir al menos un libro al pedido.")
            return

        client_id = None
        for c in self.clients_data:

            s_client = c["name"] + " — CI: " + c["identity"] + " — Tel: " + c["phone_number"]
            if s_client.lower() == client_name.lower():
                client_id = c["idClient"]
                break

        if not client_id:
            dialog = NewClientDialog(client_name)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                r = http_post(API_URL_CLIENTES, data)
                if not r or r.status_code not in (200, 201):
                    QMessageBox.warning(self, "Error", "No se pudo crear el cliente.")
                    return
                client_id = r.json().get("idClient")
                self._load_clients()
            else:
                return

        delivery_text = self.add_delivery_input.text().strip()
        id_delivery = None
        for d in getattr(self, "mensajerias_data", []):
            if d["zone"].strip().lower() == delivery_text.lower():
                id_delivery = d["idDelivery"]
                break

        if id_delivery is None:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un municipio válido.")
            return

        delivery_price = 0
        delivery_text_price = self.delivery_price_label.text().replace('$', '').strip()
        try:
            delivery_price = float(delivery_text_price) if delivery_text_price else 0
        except ValueError:
            delivery_price = 0

        try:
            payment_advance = float(self.add_payment_advance_edit.text() or 0)
        except ValueError:
            payment_advance = 0.0

        order_calculation = PriceService.calculate_order_price(
            selected_books=self.selected_books,
            books_data=self.books_data,
            additives_data=self.additives_data,
            delivery_price=delivery_price
        )
        outstanding_payment = PriceService.calculate_outstanding_payment(
            order_calculation['total_price'], 
            payment_advance
        )
        order_data = {
            "_type": self.add_type_combo.currentText().lower(),
            "address": self.add_address_input.text().strip(),
            "idDelivery": id_delivery,
            "idClient": client_id,
            "order_date": self.add_order_date.date().toString("yyyy-MM-dd"),
            "delivery_date": self.add_delivery_date.date().toString("yyyy-MM-dd"),
            "total_price": order_calculation['total_price'],
            "pay_method": self.add_payment_combo.currentText(),
            "done": False,
            "payment_advance": payment_advance,
            "outstanding_payment": outstanding_payment,
            "requested_books": []
        }
        for book_entry in self.selected_books:
            book_data = {
                "idBook": book_entry["book_id"],
                "additives": book_entry["additives"],
                "discount": book_entry["discount"],
                "quantity": book_entry["quantity"]
            }
            order_data["requested_books"].append(book_data)
        

        r = http_post(f"{API_URL_ORDERS}create_full_order/", order_data)
        if not r or r.status_code not in (200, 201):
            QMessageBox.warning(self, "Error", "No se pudo crear la orden en el servidor.")
            return

        order = r.json()
        order_id = order['order']["idOrder"]
        mensaje = self._get_order_summary_for_clipboard(order_id)
        clipboard = QApplication.clipboard()
        clipboard.setText(mensaje)
        QMessageBox.information(self, "Éxito", 
                            f"Orden #{order_id} creada correctamente.\n\nEl resumen ha sido copiado al portapapeles.")
        self._clear_order_form()

    def _clear_order_form(self):
        self.selected_books = []
        self.add_selected_books_list.clear()
        self.selected_additives = []
        self.select_services_btn.setText("Seleccionar servicios extras")
        self.add_client_input.clear()
        self.add_delivery_input.clear()
        self.add_address_input.clear()
        self.add_payment_advance_edit.clear()
        self.add_book_input.clear()
        self.add_quantity_spin.setValue(1)
        self.add_discount_spin.setValue(0)
        self.add_type_combo.setCurrentIndex(0)
        self.add_payment_combo.setCurrentIndex(0)
        self.add_order_date.setDate(QDate.currentDate())
        self._update_delivery_date_add()
        self.delivery_price_label.setText("0.00 $")
        self.total_price_label.setText("0.00 $")
        self.add_outstanding_payment_label.setText("0.00 $")

    def _get_selected_client_identity(self):
        text = self.add_client_input.text()
        for c in self.clients_data:
            if (c["name"] in text or 
                c.get("identity", "") in text or 
                c.get("phone_number", "") in text):
                return c.get("identity", "")
        return ""

    def _get_selected_client_phone(self):
        text = self.add_client_input.text()
        for c in self.clients_data:
            if (c["name"] in text or 
                c.get("identity", "") in text or 
                c.get("phone_number", "") in text):
                return c.get("phone_number", "")
        return ""

    def _clear_client_selection(self):
        self.add_client_input.clear()

    def reload_data(self):
        self._load_clients()
        self._load_deliveries()
        self._load_books()
        self._load_additives()
    

    
#* -------------------- PESTAÑA MODIFICAR ORDEN --------------------
    def _setup_modify_tab(self):
        if hasattr(self, "_modify_tab_initialized") and self._modify_tab_initialized:
            return
        self._modify_tab_initialized = True
        scroll = QScrollArea(self.modify_tab)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        #? -------------------- SECCIÓN BÚSQUEDA --------------------
        search_group = QGroupBox("Buscar orden")
        search_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #b8b8b8;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1.5px solid #ccc;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1.5px solid #555;
                background-color: #ffffff;
            }
        """)

        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)

        # Campo único de búsqueda
        search_field_layout = QHBoxLayout()
        self.modify_unified_search_edit = QLineEdit()
        self.modify_unified_search_edit.setPlaceholderText("Buscar por número de orden, nombre...")
        self.modify_unified_search_btn = QPushButton("Buscar")
        self.modify_unified_search_btn.setObjectName("primaryBtn")

        # Buscar al presionar Enter
        self.modify_unified_search_edit.returnPressed.connect(self._search_orders_unified)
        self.modify_unified_search_btn.clicked.connect(self._search_orders_unified)

        search_field_layout.addWidget(self.modify_unified_search_edit)
        search_field_layout.addWidget(self.modify_unified_search_btn)
        search_layout.addLayout(search_field_layout)

        # Lista de resultados
        self.modify_order_list = QListWidget()
        self.modify_order_list.setFixedHeight(180)
        self.modify_order_list.setStyleSheet("""
            QListWidget {
                border: 1.5px solid #ccc;
                border-radius: 8px;
                background-color: #fff;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border: none;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #f2f2f2;
                border: none;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #a6a6a6; 
                color: black;
                border-radius: 6px;
                border: none;
                outline: none;
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)
        self.modify_order_list.itemClicked.connect(lambda item: self._load_order_modify(item.data(Qt.UserRole)))

        search_layout.addWidget(self.modify_order_list)
        main_layout.addWidget(search_group)

        #? -------------------- SECCIÓN DATOS FIJOS DE LA ORDEN --------------------
        fixed_data_group = QGroupBox("Datos de la orden")
        fixed_data_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #b8b8b8;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                background-color: #fefefe;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                font-size: 14px;
                padding: 4px;
            }
        """)

        fixed_form = QFormLayout(fixed_data_group)

        # --- CLIENTE ---
        self.client_name_label = QLabel("")
        self.client_phone_label = QLabel("")
        self.client_identity_label = QLabel("")
        fixed_form.addRow(make_icon_label("frontend/icons/client.png", "Nombre:"), self.client_name_label)
        fixed_form.addRow(make_icon_label("frontend/icons/identity.png", "Carnet de Identidad:"), self.client_identity_label)
        fixed_form.addRow(make_icon_label("frontend/icons/phone.png", "Teléfono:"), self.client_phone_label)

        # --- DIRECCIÓN ACTUAL ---
        self.modify_order_address_current = QLineEdit()
        self.modify_order_address_current.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/description.png", "Dirección exacta actual:"), self.modify_order_address_current)

        # --- MUNICIPIO ACTUAL ---
        self.modify_delivery_current = QLineEdit()
        self.modify_delivery_current.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/zone.png", "Municipio actual:"), self.modify_delivery_current)

        # --- MÉTODO DE PAGO ACTUAL ---
        self.modify_payment_method_current = QLineEdit()
        self.modify_payment_method_current.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/card.png", "Método de pago actual:"), self.modify_payment_method_current)

        # --- TIPO DE PEDIDO ACTUAL ---
        self.modify_order_type_current = QLineEdit()
        self.modify_order_type_current.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/tipo.png", "Tipo de pedido actual:"), self.modify_order_type_current)

        # --- COSTO DE MENSAJERÍA ---
        self.modify_delivery_price = QLineEdit()
        self.modify_delivery_price.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/delivery.png", "Costo de mensajería:"), self.modify_delivery_price)

        # --- FECHAS ---
        self.modify_order_date = QLineEdit()
        self.modify_order_date.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/fecha1.png", "Fecha de realizado:"), self.modify_order_date)

        self.modify_delivery_date = QLineEdit()
        self.modify_delivery_date.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/fecha2.png", "Fecha de entrega:"), self.modify_delivery_date)

        # --- TOTAL ---
        self.modify_total_price = QLineEdit()
        self.modify_total_price.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/price.png", "Total:"), self.modify_total_price)

        # --- PAGO ADELANTADO ACTUAL ---
        self.modify_payment_advance_current = QLineEdit()
        self.modify_payment_advance_current.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/money.png", "Pago adelantado actual:"), self.modify_payment_advance_current)

        # --- PAGO PENDIENTE ---
        self.modify_outstanding_payment = QLineEdit()
        self.modify_outstanding_payment.setReadOnly(True)
        fixed_form.addRow(make_icon_label("frontend/icons/pending.png", "Pago pendiente:"), self.modify_outstanding_payment)

        # --- ESTADO DE LA ORDEN ---
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        self.modify_order_status_icon = QLabel()
        self.modify_order_status_icon.setFixedSize(20, 20)
        self.modify_order_status_text = QLabel("Pendiente")
        self.modify_order_status_text.setStyleSheet("font-size: 14px; font-weight: 500;")
        
        status_layout.addWidget(self.modify_order_status_icon)
        status_layout.addWidget(self.modify_order_status_text)
        status_layout.addStretch()

        fixed_form.addRow(make_icon_label("frontend/icons/status.png", "Estado de la orden:"), status_widget)

        main_layout.addWidget(fixed_data_group)

        #? -------------------- SECCIÓN DATOS MODIFICABLES --------------------
        variable_data_group = QGroupBox("Datos modificables")
        variable_data_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #2E86C1;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                background-color: #f8fdff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2E86C1;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QComboBox, QLineEdit, QSpinBox {
                font-size: 14px;
                padding: 4px;
                background-color: #ffffff;
            }
        """)

        variable_form = QFormLayout(variable_data_group)

        # --- NUEVO MÉTODO DE PAGO ---
        self.modify_payment_method_new = QComboBox()
        self.modify_payment_method_new.addItems(["CUP", "USD", "EUR", "Zelle", "USDT", "Bitcoin"])
        variable_form.addRow(make_icon_label("frontend/icons/card.png", "Nuevo método de pago:"), self.modify_payment_method_new)

        # --- NUEVO TIPO DE PEDIDO ---
        self.modify_order_type_new = QComboBox()
        variable_form.addRow(make_icon_label("frontend/icons/tipo.png", "Nuevo tipo de pedido:"), self.modify_order_type_new)

        # --- NUEVA DIRECCIÓN ---
        self.modify_order_address_new = QLineEdit()
        self.modify_order_address_new.setPlaceholderText("Nueva dirección exacta...")
        variable_form.addRow(make_icon_label("frontend/icons/description.png", "Nueva dirección:"), self.modify_order_address_new)

        # --- NUEVO MUNICIPIO ---
        self.modify_delivery_new = QComboBox()
        self.modify_delivery_new.currentIndexChanged.connect(self._on_delivery_changed)
        variable_form.addRow(make_icon_label("frontend/icons/zone.png", "Nuevo municipio:"), self.modify_delivery_new)

        # --- NUEVO PAGO ADELANTADO ---
        self.modify_payment_advance_new = QSpinBox()
        self.modify_payment_advance_new.setRange(0, 100000)
        self.modify_payment_advance_new.valueChanged.connect(self._update_modify_totals)
        variable_form.addRow(make_icon_label("frontend/icons/money.png", "Nuevo pago adelantado:"), self.modify_payment_advance_new)

        main_layout.addWidget(variable_data_group)

        #? -------------------- BOTÓN FINAL --------------------
        self.update_btn = QPushButton("Guardar cambios y copiar vale")
        self.update_btn.setObjectName("primaryBtn")
        self.update_btn.clicked.connect(self._update_order)
        main_layout.addWidget(self.update_btn, alignment=Qt.AlignCenter)

        scroll.setWidget(container)
        layout = QVBoxLayout(self.modify_tab)
        layout.addWidget(scroll)

#* -------------------- FUNCIONES DE MODIFICAR ORDEN --------------------
    def _search_orders_unified(self):
        query = self.modify_unified_search_edit.text().strip().lower()
        self.modify_order_list.clear()

        if not query:
            QMessageBox.warning(self, "Atención", "Por favor escriba algo para buscar.")
            return
        if query.isdigit():
            r = http_get(f"{API_URL_ORDERS}{query}/")
            if r and r.status_code == 200:
                order = r.json()
                date = order.get("order_date", "Sin fecha")
                item_text = f"Orden #{order['idOrder']} — {order['client_name']} ({date})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, order["idOrder"])
                
                if order.get("done", False):
                    item.setIcon(QIcon("frontend/icons/check.png"))  
                else:
                    item.setIcon(QIcon("frontend/icons/pendiente.png")) 
                    
                self.modify_order_list.addItem(item)
                return

        r = http_get(API_URL_ORDERS)
        if not r or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudieron obtener las órdenes del servidor.")
            return

        results = []
        for order in r.json():
            client = order.get("client_name", "").lower()
            identity = order.get("client_identity", "").lower()
            phone = order.get("client_phone_number", "").lower()
            date = order.get("order_date", "Sin fecha")

            if (
                query in client
                or query in identity
                or query in phone
                or query in str(order["idOrder"])
            ):
                item_text = f"Orden #{order['idOrder']} — {order['client_name']} ({date})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, order["idOrder"])
                if order.get("done", False):
                    item.setIcon(QIcon("frontend/icons/check.png"))  
                else:
                    item.setIcon(QIcon("frontend/icons/pendiente.png"))
                    
                results.append(item)
        if results:
            for item in results:
                self.modify_order_list.addItem(item)
        else:
            QMessageBox.information(self, "Sin resultados", "No se encontraron órdenes con ese criterio.")

        def _search_order_by_number(self):
            order_number = self.modify_order_search_edit.text().strip()
            self.modify_order_list.clear()
            if not order_number:
                QMessageBox.warning(self, "Atención", "Debe escribir un número de orden.")
                return

            r = http_get(f"{API_URL_ORDERS}{order_number}/")
            if r and r.status_code == 200:
                order = r.json()
                item = QListWidgetItem(f"{order['client_name']} — {order['idOrder']}")
                item.setData(Qt.UserRole, order["idOrder"])
                self.modify_order_list.addItem(item)
            else:
                QMessageBox.information(self, "Sin resultados", "No se encontró una orden con ese número.")

    def _load_order_modify(self, order_id):
        try:
            self.current_order_id = order_id
            r = http_get(f"{API_URL_ORDERS}{order_id}/full_details/")
            if not r or r.status_code != 200:
                QMessageBox.warning(self, "Error", f"No se pudo cargar la orden #{order_id}")
                return
            data = r.json()
            self.order_data = data
            is_done = data.get("done", False)
            if is_done:
                self._set_modify_form_enabled(False)
                self.modify_order_status_icon.setPixmap(QPixmap("frontend/icons/check.png").scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.modify_order_status_text.setText("COMPLETADA")
                self.modify_order_status_text.setStyleSheet("font-size: 14px; font-weight: 500; color: #27ae60;")
                QMessageBox.information(self, "Orden completada", 
                                      "Esta orden ya está marcada como completada y no puede ser modificada.")
            else:
                self._set_modify_form_enabled(True)
                self.modify_order_status_icon.setPixmap(QPixmap("frontend/icons/pendiente.png").scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.modify_order_status_text.setText("PENDIENTE")
                self.modify_order_status_text.setStyleSheet("font-size: 14px; font-weight: 500; color: #F4320B;")

            # --- DATOS DEL CLIENTE ---
            client = data.get("client", {})
            client_name = client.get("name", "No disponible")
            client_phone = client.get("phone_number", "No disponible")
            client_identity = client.get("identity", "No disponible")

            self.client_name_label.setText(client_name)
            self.client_phone_label.setText(client_phone)
            self.client_identity_label.setText(client_identity)

            # --- DIRECCIÓN ACTUAL ---
            address = data.get("address", "")
            self.modify_order_address_current.setText(address)
            self.modify_order_address_new.setText(address) 

            # --- MUNICIPIO ACTUAL ---
            delivery_zone = data.get("delivery_zone", "No especificado")
            self.modify_delivery_current.setText(delivery_zone)

            # --- MÉTODO DE PAGO ---
            pay_method = data.get("pay_method", "")
            self.modify_payment_method_current.setText(pay_method)
            
            index = self.modify_payment_method_new.findText(pay_method)
            if index >= 0:
                self.modify_payment_method_new.setCurrentIndex(index)
            else:
                self.modify_payment_method_new.setCurrentIndex(0)

            # --- TIPO DE PEDIDO ---
            order_type = data.get("_type", "")
            self.modify_order_type_current.setText(order_type)
            
            # Cargar tipos de pedido (Regular + servicios)
            self._load_order_types_for_modify()
            
            index = self.modify_order_type_new.findText(order_type)
            if index >= 0:
                self.modify_order_type_new.setCurrentIndex(index)
            else:
                self.modify_order_type_new.setCurrentIndex(0)

            # --- COSTO DE MENSAJERÍA ---
            delivery_price = data.get("delivery_price", 0)
            self.modify_delivery_price.setText(f"{delivery_price:.2f}")

            # --- FECHAS ---
            order_date = data.get("order_date", "")
            delivery_date = data.get("delivery_date", "")
            
            self.modify_order_date.setText(order_date or "No especificada")
            self.modify_delivery_date.setText(delivery_date or "No especificada")

            # --- PRECIOS (DE BASE DE DATOS) ---
            total_price = data.get("total_price", 0)
            payment_advance = data.get("payment_advance", 0)
            outstanding = data.get("outstanding_payment", total_price - payment_advance)

            self.modify_total_price.setText(f"{total_price:.2f}")
            self.modify_payment_advance_current.setText(f"{payment_advance:.2f}")
            self.modify_payment_advance_new.setValue(int(payment_advance))
            self.modify_outstanding_payment.setText(f"{outstanding:.2f}")

            self._load_deliveries_for_modify_combo()

            current_delivery_zone = data.get("delivery_zone", "")
            if current_delivery_zone:
                index = self.modify_delivery_new.findText(current_delivery_zone)
                if index >= 0:
                    self.modify_delivery_new.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la orden.\n{str(e)}")

    def _set_modify_form_enabled(self, enabled):
        self.modify_payment_method_new.setEnabled(enabled)
        self.modify_order_type_new.setEnabled(enabled)
        self.modify_order_address_new.setEnabled(enabled)
        self.modify_delivery_new.setEnabled(enabled)
        self.modify_payment_advance_new.setEnabled(enabled)
        self.update_btn.setEnabled(enabled)

    def _on_delivery_changed(self, index):
        if index >= 0:
            delivery_id = self.modify_delivery_new.currentData()
            if delivery_id:
                for delivery in self.mensajerias_data:
                    if delivery["idDelivery"] == delivery_id:
                        new_price = delivery.get("price", 0)
                        self.modify_delivery_price.setText(f"{new_price:.2f}")
                        self._update_modify_totals()                       
                        break

    def _load_order_types_for_modify(self):
        try:
            self.modify_order_type_new.clear()
            self.modify_order_type_new.addItem("Regular")
            r = http_get(API_URL_ADITIVOS)
            if r and r.status_code == 200:
                additives_data = r.json()
                service_additives = [a for a in additives_data if a["name"].lower().startswith("servicio")]
                for additive in service_additives:
                    self.modify_order_type_new.addItem(additive["name"])
        except Exception as e:
            pass

    def _load_deliveries_for_modify_combo(self):
        try:
            r = http_get(API_URL_MENSAJERIAS)
            if r and r.status_code == 200:
                self.mensajerias_data = r.json()
                self.modify_delivery_new.clear()
                self.modify_delivery_new.addItem("", None)
                for delivery in self.mensajerias_data:
                    self.modify_delivery_new.addItem(delivery["zone"], delivery["idDelivery"])
        except Exception as e:
            pass

    def _update_modify_totals(self):
        try:
            total_price_text = self.modify_total_price.text()
            total_price = float(total_price_text) if total_price_text else 0
            payment_advance = self.modify_payment_advance_new.value()
            outstanding_payment = total_price - payment_advance
            self.modify_outstanding_payment.setText(f"{outstanding_payment:.2f}")           
        except Exception as e:
            pass

    def _update_order(self):
        if not hasattr(self, 'current_order_id') or not self.current_order_id:
            QMessageBox.warning(self, "Error", "No se ha cargado ninguna orden para modificar.")
            return       
        try:
            order_id = self.current_order_id
            r = http_get(f"{API_URL_ORDERS}{order_id}/")
            if r and r.status_code == 200:
                order_data = r.json()
                if order_data.get("done", False):
                    QMessageBox.warning(self, "Orden completada", 
                                      "Esta orden ya está completada y no puede ser modificada.")
                    return
            
            updated_data = {
                "address": self.modify_order_address_new.text().strip(),
                "pay_method": self.modify_payment_method_new.currentText(),
                "_type": self.modify_order_type_new.currentText(),
                "payment_advance": self.modify_payment_advance_new.value(),
                "total_price": float(self.modify_total_price.text() or 0),
                "outstanding_payment": float(self.modify_outstanding_payment.text() or 0)
            }
            
            current_delivery_id = self.modify_delivery_new.currentData()
            if current_delivery_id:
                updated_data["idDelivery"] = current_delivery_id

            resp = http_put(f"{API_URL_ORDERS}{order_id}/update_order_data/", updated_data)
            
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "Éxito", f"Orden #{order_id} actualizada correctamente.")
                
                r_updated = http_get(f"{API_URL_ORDERS}{order_id}/full_details/")
                if r_updated and r_updated.status_code == 200:
                    updated_order_data = r_updated.json()
                    vale_text = self._format_order_summary(updated_order_data)
                    clipboard = QApplication.clipboard()
                    clipboard.setText(vale_text)
                else:
                    QMessageBox.information(self, "Éxito", 
                                          f"Orden #{order_id} actualizada correctamente.\n\n" +
                                          "Nota: No se pudo generar el vale automáticamente.")  
                self._clear_modify_form()
            else:
                error_msg = f"No se pudo actualizar la orden. Código: {resp.status_code if resp else 'Sin respuesta'}"
                if resp:
                    error_msg += f"\nError: {resp.text}"
                QMessageBox.warning(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la orden.\n{str(e)}")

    def _clear_modify_form(self):
        self.current_order_id = None
        self.order_data = None
        self.client_name_label.setText("")
        self.client_phone_label.setText("")
        self.client_identity_label.setText("")
        self.modify_order_address_current.clear()
        self.modify_order_address_new.clear()
        self.modify_delivery_current.clear()
        self.modify_delivery_new.setCurrentIndex(0)
        self.modify_payment_method_current.clear()
        self.modify_payment_method_new.setCurrentIndex(0)
        self.modify_order_type_current.clear()
        self.modify_order_type_new.setCurrentIndex(0)
        self.modify_delivery_price.clear()
        self.modify_order_date.clear()
        self.modify_delivery_date.clear()
        self.modify_total_price.clear()
        self.modify_payment_advance_current.clear()
        self.modify_payment_advance_new.setValue(0)
        self.modify_outstanding_payment.clear()
        self.modify_order_status_icon.clear()
        self._set_modify_form_enabled(True)

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
            
            number_of_pages = book.get('number_pages', 0)
            color_pages = book.get("color_pages", 0)
            printing_format = book.get("printing_format", "normal").lower()
            precio_base_caratula = calculate_price(number_of_pages, color_pages, printing_format) + caratula_price

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
            
            precio_base_con_descuento = precio_base_caratula * (1 - discount / 100)
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
        
        mensaje += f"— Servicio de entrega: {order_data['_type']}\n"
        mensaje += f"— Método de pago: {order_data['pay_method']}\n\n"
        mensaje += "🔆 Conoce nuestros trabajos en instagram.com/moe.libros"
        return mensaje


#* -------------------- PESTAÑA ELIMINAR ORDEN --------------------
    def _setup_delete_tab(self):
        if hasattr(self, "_delete_tab_initialized") and self._delete_tab_initialized:
            return
        self._delete_tab_initialized = True
        
        scroll = QScrollArea(self.delete_tab)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        #? -------------------- SECCIÓN BÚSQUEDA --------------------
        search_group = QGroupBox("Buscar orden para eliminar")
        search_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: none;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1.5px solid #ccc;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1.5px solid #555;
                background-color: #ffffff;
            }
        """)

        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)

        # Campo único de búsqueda
        search_field_layout = QHBoxLayout()
        self.delete_unified_search_edit = QLineEdit()
        self.delete_unified_search_edit.setPlaceholderText("Buscar por número de orden, nombre...")
        self.delete_unified_search_btn = QPushButton("Buscar")
        self.delete_unified_search_btn.setObjectName("primaryBtn")

        # Buscar al presionar Enter
        self.delete_unified_search_edit.returnPressed.connect(self._search_orders_delete_unified)
        self.delete_unified_search_btn.clicked.connect(self._search_orders_delete_unified)

        search_field_layout.addWidget(self.delete_unified_search_edit)
        search_field_layout.addWidget(self.delete_unified_search_btn)
        search_layout.addLayout(search_field_layout)

        # Lista de resultados
        self.delete_order_list = QListWidget()
        self.delete_order_list.setFixedHeight(180)
        self.delete_order_list.setStyleSheet("""
            QListWidget {
                border: 1.5px solid #ccc;
                border-radius: 8px;
                background-color: #fff;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border: none;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #f2f2f2;
                border: none;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #a6a6a6; 
                color: black;
                border-radius: 6px;
                border: none;
                outline: none;
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)
        self.delete_order_list.itemClicked.connect(lambda item: self._load_order_delete(item.data(Qt.UserRole)))
        search_layout.addWidget(self.delete_order_list)
        main_layout.addWidget(search_group)

        #? -------------------- SECCIÓN DETALLES DE LA ORDEN --------------------
        details_group = QGroupBox("Detalles de la orden")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                background-color: #fff5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #e74c3c;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit, QTextEdit {
                font-size: 14px;
                padding: 4px;
            }
        """)

        details_layout = QVBoxLayout(details_group)

        # --- INFORMACIÓN BÁSICA ---
        basic_info_group = QGroupBox("Información básica")
        basic_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 5px;
                padding: 8px;
                background-color: #f9f9f9;
            }
        """)
        basic_form = QFormLayout(basic_info_group)

        # Cliente
        self.delete_client_name = QLabel("")
        self.delete_client_identity = QLabel("")
        self.delete_client_phone = QLabel("")
        basic_form.addRow(make_icon_label("frontend/icons/client.png", "Nombre:"), self.delete_client_name)
        basic_form.addRow(make_icon_label("frontend/icons/identity.png", "Carnet:"), self.delete_client_identity)
        basic_form.addRow(make_icon_label("frontend/icons/phone.png", "Teléfono:"), self.delete_client_phone)

        # Dirección y municipio
        self.delete_order_address = QLabel("")
        self.delete_delivery_zone = QLabel("")
        basic_form.addRow(make_icon_label("frontend/icons/description.png", "Dirección:"), self.delete_order_address)
        basic_form.addRow(make_icon_label("frontend/icons/zone.png", "Municipio:"), self.delete_delivery_zone)

        # Fechas
        self.delete_order_date = QLabel("")
        self.delete_delivery_date = QLabel("")
        basic_form.addRow(make_icon_label("frontend/icons/fecha1.png", "Fecha de pedido:"), self.delete_order_date)
        basic_form.addRow(make_icon_label("frontend/icons/fecha2.png", "Fecha de entrega:"), self.delete_delivery_date)

        # Método de pago y tipo
        self.delete_payment_method = QLabel("")
        self.delete_order_type = QLabel("")
        basic_form.addRow(make_icon_label("frontend/icons/card.png", "Método de pago:"), self.delete_payment_method)
        basic_form.addRow(make_icon_label("frontend/icons/tipo.png", "Tipo de pedido:"), self.delete_order_type)

        details_layout.addWidget(basic_info_group)

        # --- INFORMACIÓN FINANCIERA ---
        financial_group = QGroupBox("Información financiera")
        financial_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 5px;
                padding: 8px;
                background-color: #f9f9f9;
            }
        """)
        financial_form = QFormLayout(financial_group)

        self.delete_total_price = QLabel("")
        self.delete_payment_advance = QLabel("")
        self.delete_outstanding_payment = QLabel("")
        self.delete_delivery_price = QLabel("")

        financial_form.addRow(make_icon_label("frontend/icons/price.png", "Total:"), self.delete_total_price)
        financial_form.addRow(make_icon_label("frontend/icons/money.png", "Pago adelantado:"), self.delete_payment_advance)
        financial_form.addRow(make_icon_label("frontend/icons/pending.png", "Pago pendiente:"), self.delete_outstanding_payment)
        financial_form.addRow(make_icon_label("frontend/icons/delivery.png", "Costo mensajería:"), self.delete_delivery_price)

        details_layout.addWidget(financial_group)

        # --- LIBROS Y ADITIVOS ---
        books_group = QGroupBox("Libros y servicios")
        books_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 5px;
                padding: 8px;
                background-color: #f9f9f9;
            }
        """)
        books_layout = QVBoxLayout(books_group)

        books_scroll = QScrollArea()
        books_scroll.setWidgetResizable(True)
        books_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        books_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        books_scroll.setFixedHeight(250)
        books_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QScrollArea > QWidget > QWidget {
                background-color: white;
            }
        """)

        self.delete_books_container = QWidget()
        self.delete_books_layout = QVBoxLayout(self.delete_books_container)
        self.delete_books_layout.setAlignment(Qt.AlignTop)
        self.delete_books_layout.setSpacing(10)
        self.delete_books_layout.setContentsMargins(10, 10, 10, 10)

        books_scroll.setWidget(self.delete_books_container)
        books_layout.addWidget(books_scroll)

        details_layout.addWidget(books_group)

        main_layout.addWidget(details_group)

        #? -------------------- BOTÓN ELIMINAR --------------------
        self.delete_btn = QPushButton("ELIMINAR ORDEN COMPLETA")
        self.delete_btn.setObjectName("dangerBtn")
        self.delete_btn.setStyleSheet("""
            QPushButton#dangerBtn {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#dangerBtn:hover {
                background-color: #c0392b;
            }
            QPushButton#dangerBtn:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.delete_btn.clicked.connect(self._delete_order)
        self.delete_btn.setEnabled(False)
        main_layout.addWidget(self.delete_btn, alignment=Qt.AlignCenter)

        scroll.setWidget(container)
        layout = QVBoxLayout(self.delete_tab)
        layout.addWidget(scroll)

#* -------------------- FUNCIONES DE ELIMINAR ORDEN --------------------
    def _search_orders_delete_unified(self):
        query = self.delete_unified_search_edit.text().strip().lower()
        self.delete_order_list.clear()

        if not query:
            QMessageBox.warning(self, "Atención", "Por favor escriba algo para buscar.")
            return
        if query.isdigit():
            r = http_get(f"{API_URL_ORDERS}{query}/")
            if r and r.status_code == 200:
                order = r.json()
                date = order.get("order_date", "Sin fecha")
                item_text = f"Orden #{order['idOrder']} — {order['client_name']} ({date})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, order["idOrder"])

                if order.get("done", False):
                    item.setIcon(QIcon("frontend/icons/check.png"))  
                else:
                    item.setIcon(QIcon("frontend/icons/pendiente.png"))

                self.delete_order_list.addItem(item)
                return

        r = http_get(API_URL_ORDERS)
        if not r or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudieron obtener las órdenes del servidor.")
            return

        results = []
        for order in r.json():
            client = order.get("client_name", "").lower()
            identity = order.get("client_identity", "").lower()
            phone = order.get("client_phone_number", "").lower()
            date = order.get("order_date", "Sin fecha")

            if (
                query in client
                or query in identity
                or query in phone
                or query in str(order["idOrder"])
            ):
                item_text = f"Orden #{order['idOrder']} — {order['client_name']} ({date})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, order["idOrder"])
                if order.get("done", False):
                    item.setIcon(QIcon("frontend/icons/check.png"))  
                else:
                    item.setIcon(QIcon("frontend/icons/pendiente.png"))
                results.append(item)

        if results:
            for item in results:
                self.delete_order_list.addItem(item)
        else:
            if not getattr(self, "_suppress_no_results_msg", False):
                QMessageBox.information(self, "Sin resultados", "No se encontraron órdenes con ese criterio.")

    def _load_order_delete(self, order_id):
        try:
            self.current_delete_order_id = order_id
            r = http_get(f"{API_URL_ORDERS}{order_id}/full_details/")
            if not r or r.status_code != 200:
                QMessageBox.warning(self, "Error", f"No se pudo cargar la orden #{order_id}")
                return

            data = r.json()

            # --- INFORMACIÓN DEL CLIENTE ---
            client = data.get("client", {})
            self.delete_client_name.setText(client.get("name", "No disponible"))
            self.delete_client_identity.setText(client.get("identity", "No disponible"))
            self.delete_client_phone.setText(client.get("phone_number", "No disponible"))

            # --- INFORMACIÓN DE LA ORDEN ---
            self.delete_order_address.setText(data.get("address", "No especificada"))
            self.delete_delivery_zone.setText(data.get("delivery_zone", "No especificado"))
            self.delete_order_date.setText(data.get("order_date", "No especificada"))
            self.delete_delivery_date.setText(data.get("delivery_date", "No especificada"))
            self.delete_payment_method.setText(data.get("pay_method", "No especificado"))
            self.delete_order_type.setText(data.get("_type", "No especificado"))

            # --- INFORMACIÓN FINANCIERA ---
            total_price = data.get("total_price", 0)
            payment_advance = data.get("payment_advance", 0)
            outstanding = data.get("outstanding_payment", 0)
            delivery_price = data.get("delivery_price", 0)

            self.delete_total_price.setText(f"{total_price:.2f} USD")
            self.delete_payment_advance.setText(f"{payment_advance:.2f} USD")
            self.delete_outstanding_payment.setText(f"{outstanding:.2f} USD")
            self.delete_delivery_price.setText(f"{delivery_price:.2f} USD")

            # --- LIBROS Y ADITIVOS ---
            for i in reversed(range(self.delete_books_layout.count())):
                widget = self.delete_books_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            books = data.get("books", [])
            
            if not books:
                no_books_label = QLabel("No hay libros en esta orden")
                no_books_label.setAlignment(Qt.AlignCenter)
                no_books_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
                self.delete_books_layout.addWidget(no_books_label)
            else:
                for i, book_info in enumerate(books, 1):
                    book_widget = self._create_book_widget_delete(i, book_info)
                    self.delete_books_layout.addWidget(book_widget)

            self.delete_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la orden.\n{str(e)}")

    def _delete_order(self):
        if not hasattr(self, 'current_delete_order_id') or not self.current_delete_order_id:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ninguna orden para eliminar.")
            return

        order_id = self.current_delete_order_id

        try:
            r = http_get(f"{API_URL_ORDERS}{order_id}/")
            if not r or r.status_code != 200:
                QMessageBox.warning(self, "Error", f"No se pudo verificar el estado de la orden #{order_id}.")
                return
            order_data = r.json()
            if order_data.get("done", False):
                QMessageBox.warning(
                    self,
                    "No permitido",
                    f"La orden #{order_id} ya está marcada como finalizada y no puede eliminarse. 🚫"
                )
                return

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo verificar la orden antes de eliminar.\n{str(e)}")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar la orden #{order_id}?\n\n"
            f"⚠️ ESTA ACCIÓN ELIMINARÁ:\n"
            f"• La orden completa\n"
            f"• Todos los libros asociados\n"
            f"• Todos los servicios/aditivos\n"
            f"• El historial de pagos\n\n"
            f"🚫 ESTA ACCIÓN NO SE PUEDE DESHACER",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            resp = http_delete(f"{API_URL_ORDERS}{order_id}/delete_full_order/")
            
            if resp and resp.status_code in (200, 204):
                QMessageBox.information(self, "Éxito", f"Orden #{order_id} eliminada correctamente.")
                self._clear_delete_form()
                self._suppress_no_results_msg = True
                self._search_orders_delete_unified()
                self._suppress_no_results_msg = False
            else:
                error_msg = f"No se pudo eliminar la orden #{order_id}."
                if resp:
                    error_msg += f"\nCódigo: {resp.status_code}\nError: {resp.text}"
                QMessageBox.warning(self, "Error", error_msg)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar la orden: {str(e)}")

    def _clear_delete_form(self):
        self.current_delete_order_id = None
        self.delete_client_name.setText("")
        self.delete_client_identity.setText("")
        self.delete_client_phone.setText("")
        self.delete_order_address.setText("")
        self.delete_delivery_zone.setText("")
        self.delete_order_date.setText("")
        self.delete_delivery_date.setText("")
        self.delete_payment_method.setText("")
        self.delete_order_type.setText("")
        self.delete_total_price.setText("")
        self.delete_payment_advance.setText("")
        self.delete_outstanding_payment.setText("")
        self.delete_delivery_price.setText("")
        self.delete_btn.setEnabled(False)

    def _create_book_widget_delete(self, index, book_info):
        book_widget = QFrame()
        book_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
            }
        """)

        layout = QVBoxLayout(book_widget)
        layout.setSpacing(6)

        # ------------------- HEADER -------------------
        header_layout = QHBoxLayout()

        title_label = QLabel(book_info['book'].get('title', 'Desconocido'))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # ------------------- DETALLES -------------------
        book_details_layout = QFormLayout()
        book_details_layout.setHorizontalSpacing(10)
        book_details_layout.setVerticalSpacing(3)

        book = book_info['book']

        # Campos básicos
        author_label = QLabel(book.get('author', 'No especificado'))
        pages_label = QLabel(f"{book.get('number_pages', 0)} páginas")
        format_label = QLabel(book.get('printing_format', 'No especificado'))
        color_label = QLabel(f"{book.get('color_pages', 0)} páginas color")
        quantity_label = QLabel(f"{book_info.get('quantity', 1)} unidad(es)")
        discount_label = QLabel(f"{book_info.get('discount', 0)}%")
        ready = book_info.get('ready', False)
        if ready:
            state_label= QLabel("✅ Listo")
        else:
            state_label= QLabel("⏳ Pendiente")

        for lbl in [pages_label, format_label, color_label, quantity_label, discount_label, state_label, author_label]:
            lbl.setStyleSheet("color: #555; font-size: 13px;")

        book_details_layout.addRow("👤 Author:", author_label)
        book_details_layout.addRow("📄 Páginas:", pages_label)
        book_details_layout.addRow("🖨️ Formato:", format_label)
        book_details_layout.addRow("🎨 Color:", color_label)
        book_details_layout.addRow("🔢 Cantidad:", quantity_label)
        book_details_layout.addRow("💰 Descuento:", discount_label)
        book_details_layout.addRow("⚠️ Estado:", state_label)

        layout.addLayout(book_details_layout)
        # ------------------- SERVICIOS / ADITIVOS -------------------
        additives = book_info.get('additives', [])
        if additives:
            additives_group = QGroupBox("🛠️ Servicios incluidos")
            additives_group.setStyleSheet("""
                QGroupBox {
                    font-weight: 600;
                    font-size: 13px;
                    border: none;
                    border-radius: 8px;
                    margin-top: 6px;
                    padding: 6px 8px;
                    background-color: #fafafa;
                }
                QGroupBox::title {
                    color: #2c3e50;
                    font-size: 13px;
                    margin-bottom: 4px;
                    subcontrol-origin: margin;
                    left: 5px;
                    padding: 0 4px;
                }
            """)

            additives_layout = QVBoxLayout(additives_group)
            additives_layout.setSpacing(3)

            for additive in additives:
                name_label = QLabel(f"• {additive['name']}")
                name_label.setStyleSheet("font-size: 13px; color: #2c3e50;")
                additives_layout.addWidget(name_label)

            layout.addWidget(additives_group)

        return book_widget


        
#* ------------------- STYLE -------------------
    def _apply_styles(self):
        self.setStyleSheet("""
        QWidget#gestionPage {
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
            font-size: 14px;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox {
            background: #fafafa;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
        }

        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #2E86C1;
            background: #fff;
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
            padding-top: 11px;   /* efecto hundido */
            padding-bottom: 9px;
        }

        QPushButton#secondaryBtn {
            background-color: #444;
            color: white;
            border-radius: 6px;
            padding: 6px 10px;
        }

        QPushButton#secondaryBtn:hover {
            background-color: #666;
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
        QDateEdit{
            background: #fafafa;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
        }

        QComboBox:hover {
            border: 1px solid #888;
        }
        #secondaryBtn {
            background-color: #f0f0f0;
            color: #333;
            border-radius: 8px;
            padding: 8px 14px;
        }
        #secondaryBtn:hover {
            background-color: #e2e2e2;
        }
        """)
