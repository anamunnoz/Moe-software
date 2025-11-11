import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QCheckBox, QMessageBox,
    QScrollArea, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon

from utils import http_get, http_put, make_icon_label
from urls import API_URL_ORDERS, API_URL_BOOK_ON_ORDER, API_URL_REQUESTED_BOOK_ADDITIVES

class ProductionStatusTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_orders = []
        self._apply_styles()
        self._setup_production_tab()

    def _get_cover_type(self, requested_book_id):
        try:
            r = http_get(f"{API_URL_REQUESTED_BOOK_ADDITIVES}?idRequested_book={requested_book_id}")
            if r and r.status_code == 200:
                additives = r.json()
                for additive in additives:
                    additive_name = additive.get('additive', {}).get('name', '').lower()
                    if 'caratula' in additive_name or 'carátula' in additive_name:
                        return additive_name
            return "Carátula Regular"
        except:
            return "Carátula Regular"

    def _setup_production_tab(self):
        if hasattr(self, "_production_tab_initialized") and self._production_tab_initialized:
            return
        self._production_tab_initialized = True

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        #? ---------------- ENCABEZADO PRINCIPAL ----------------
        header_layout = QHBoxLayout()
        header_icon = QLabel()
        header_icon.setPixmap(
            QPixmap("icons/production.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        header_title = QLabel("Estado de Producción")
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

        main_layout.addLayout(header_layout)
        main_layout.addWidget(line)

        #? ---------------- ÁREA SCROLL ----------------
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignTop)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(15, 15, 15, 15)

        #? ---------------- SECCIÓN BÚSQUEDA ----------------
        search_group = QGroupBox()
        search_group.setTitle("Buscar orden")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)

        field_layout = QHBoxLayout()
        self.production_search_edit = QLineEdit()
        self.production_search_edit.setPlaceholderText("Buscar por número de orden o cliente...")
        self.production_search_btn = QPushButton("Buscar")
        self.production_search_btn.setObjectName("primaryBtn")

        field_layout.addWidget(self.production_search_edit)
        field_layout.addWidget(self.production_search_btn)
        search_layout.addLayout(field_layout)

        self.production_order_list = QListWidget()
        self.production_order_list.setFixedHeight(200)
        search_layout.addWidget(self.production_order_list)

        self.production_search_edit.returnPressed.connect(self._search_orders_production)
        self.production_search_btn.clicked.connect(self._search_orders_production)
        self.production_order_list.itemClicked.connect(lambda item: self._load_order_production(item.data(Qt.UserRole)))

        container_layout.addWidget(search_group)

        #? ---------------- SECCIÓN ESTADO DE ORDEN ----------------
        status_group = QGroupBox("Estado de producción actual")
        status_layout = QVBoxLayout(status_group)

        info_layout = QHBoxLayout()
        self.order_done_checkbox = QCheckBox()
        self.order_done_checkbox.setEnabled(False)
        self.order_done_checkbox.setFixedSize(24, 24)

        self.order_title_label = QLabel("Orden #")
        self.order_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")

        info_layout.addWidget(self.order_done_checkbox)
        info_layout.addWidget(self.order_title_label)
        info_layout.addStretch()

        status_layout.addLayout(info_layout)

        self.books_list_widget = QListWidget()
        self.books_list_widget.setMinimumHeight(450)
        self.books_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                min-width: 600px;
            }
            QListWidget::item {
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)
        status_layout.addWidget(self.books_list_widget)
        container_layout.addWidget(status_group)

        #? ---------------- BOTÓN GUARDAR ----------------
        self.save_production_btn = QPushButton("Guardar estados")
        self.save_production_btn.setObjectName("primaryBtn")
        self.save_production_btn.setIcon(QPixmap("icons/save.png"))
        self.save_production_btn.setEnabled(False)
        self.save_production_btn.clicked.connect(self._save_production_status)
        container_layout.addWidget(self.save_production_btn, alignment=Qt.AlignCenter)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

#* -------------------- FUNCIONES DE ESTADO DE PRODUCCIÓN --------------------
    def _search_orders_production(self):
        query = self.production_search_edit.text().strip().lower()
        self.production_order_list.clear()

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
                    item.setIcon(QIcon("icons/check.png"))  
                else:
                    item.setIcon(QIcon("icons/pendiente.png"))
                self.production_order_list.addItem(item)
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
                    item.setIcon(QIcon("icons/check.png"))  
                else:
                    item.setIcon(QIcon("icons/pendiente.png"))
                results.append(item)

        if results:
            for item in results:
                self.production_order_list.addItem(item)
        else:
            QMessageBox.information(self, "Sin resultados", "No se encontraron órdenes con ese criterio.")

    def _load_order_production(self, order_id):
        try:
            self.current_production_order_id = order_id
            self.current_book_states = {}
            
            r = http_get(f"{API_URL_ORDERS}{order_id}/full_details/")
            if not r or r.status_code != 200:
                QMessageBox.warning(self, "Error", f"No se pudo cargar la orden #{order_id}")
                return

            data = r.json()

            self.order_title_label.setText(f"Orden #{order_id} - {data.get('client', {}).get('name', '')}")

            is_order_done = data.get("done", False)
            self.order_done_checkbox.setChecked(is_order_done)

            self.books_list_widget.clear()

            books = data.get("books", [])
            for i, book_info in enumerate(books, 1):
                book = book_info['book']
                is_ready = book_info.get('ready', False)
                book_id = book_info.get('idRequested_book')
                quantity = book_info.get('quantity', 1)
                
                cover_type = self._get_cover_type(book_id)
                self.current_book_states[book_id] = is_ready
                
                book_widget = QWidget()
                book_layout = QHBoxLayout(book_widget)
                book_layout.setContentsMargins(20, 15, 20, 15) 
                book_layout.setSpacing(20)
                
                ready_checkbox = QCheckBox()
                ready_checkbox.setChecked(is_ready)
                ready_checkbox.setFixedSize(22, 22)
                
                ready_checkbox.toggled.connect(lambda checked, bid=book_id: self._on_book_ready_changed(bid, checked))
                
                book_info_widget = QWidget()
                book_info_layout = QVBoxLayout(book_info_widget)
                book_info_layout.setContentsMargins(0, 0, 0, 0)
                book_info_layout.setSpacing(8)
                
                title_label = QLabel(book.get('title', 'Libro sin título'))
                title_label.setStyleSheet("""
                    font-size: 14px; 
                    font-weight: bold; 
                    color: #2c3e50;
                    padding: 4px 0px;
                    margin-bottom: 6px;
                """)
                title_label.setWordWrap(True)
                title_label.setMinimumHeight(40)
                title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                
                details_text = f"• Cantidad: {quantity} | • Carátula: {cover_type}"
                details_label = QLabel(details_text)
                details_label.setStyleSheet("""
                    font-size: 12px; 
                    color: #666;
                    padding: 2px 0px;
                """)
                details_label.setMinimumHeight(20)
                
                book_info_layout.addWidget(title_label)
                book_info_layout.addWidget(details_label)
                book_info_layout.addStretch()
                
                book_info_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                
                book_layout.addWidget(ready_checkbox)
                book_layout.addWidget(book_info_widget)
                book_layout.addStretch()
                
                list_item = QListWidgetItem()
                list_item.setSizeHint(QSize(550, 90))
                
                self.books_list_widget.addItem(list_item)
                self.books_list_widget.setItemWidget(list_item, book_widget)

            self.books_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            

            self.save_production_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la orden.\n{str(e)}")

    def _on_book_ready_changed(self, book_id, is_ready):
        self.current_book_states[book_id] = is_ready
        
        all_ready = all(self.current_book_states.values())
        self.order_done_checkbox.setChecked(all_ready)

    def _save_production_status(self):
        if not hasattr(self, 'current_production_order_id') or not self.current_production_order_id:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ninguna orden.")
            return

        order_id = self.current_production_order_id

        try:
            r = http_get(f"{API_URL_BOOK_ON_ORDER}?idOrder={order_id}")
            if not r or r.status_code != 200:
                QMessageBox.warning(self, "Error", "No se pudieron obtener los libros de la orden.")
                return

            book_links = r.json()

            update_success = True
            for book_id, is_ready in self.current_book_states.items():
                book_updated = False
                
                for book_link in book_links:
                    if book_link.get('idRequested_book') == book_id:
                        book_on_order_id = book_link.get('id')
                        
                        if not book_on_order_id:
                            update_success = False
                            continue
                        
                        update_data = book_link.copy()
                        update_data['ready'] = is_ready
                        
                        update_data.pop('idRequested_book_title', None)
                        update_data.pop('idOrder_type', None)
                        
                        resp = http_put(f"{API_URL_BOOK_ON_ORDER}{book_on_order_id}/", update_data)
                        
                        if resp and resp.status_code == 200:
                            book_updated = True
                        else:
                            update_success = False
                        break
                
                if not book_updated:
                    update_success = False

            all_ready = all(self.current_book_states.values())
            
            order_update_data = {"done": all_ready}
            resp = http_put(f"{API_URL_ORDERS}{order_id}/update_order_data/", order_update_data)
            
            if resp and resp.status_code == 200:
                if update_success:
                    QMessageBox.information(self, "Éxito", "Estados guardados correctamente.")
                else:
                    QMessageBox.warning(self, "Advertencia", 
                                    "Estado de la orden actualizado, pero algunos libros no se pudieron actualizar.")
                
                self._load_order_production(order_id)
                self._search_orders_production()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar el estado de la orden {order_id}.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar los estados: {str(e)}")

    def _clear_production_form(self):
        if hasattr(self, 'current_production_order_id'):
            self.current_production_order_id = None
        if hasattr(self, 'current_book_states'):
            self.current_book_states = {}
        
        self.order_title_label.setText("Orden #")
        self.order_done_checkbox.setChecked(False)
        self.books_list_widget.clear()
        self.save_production_btn.setEnabled(False)

#* -------------------- ESTILOS --------------------
    def _apply_styles(self):
        self.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 16px;
            border: 2px solid #b0b0b0;
            border-radius: 10px;
            padding: 12px;
            background-color: #fff;
            margin-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #333;
        }

        QLabel {
            color: #222;
            font-size: 14px;
        }

        QLineEdit {
            background: #fafafa;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
        }

        QLineEdit:focus {
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
            padding-top: 11px;
            padding-bottom: 9px;
        }

        QListWidget {
            border: 1.5px solid #ccc;
            border-radius: 8px;
            background-color: #fff;
            font-size: 14px;
            outline: none;
            min-width: 600px;
        }

        QListWidget::item {
            padding: 8px;
            border: none;
            outline: none;
        }

        QListWidget::item:hover {
            background-color: #f2f2f2;
        }

        QListWidget::item:selected {
            background-color: #a6a6a6; 
            color: black;
            border-radius: 6px;
        }
        """)