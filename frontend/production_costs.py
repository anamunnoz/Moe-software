import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QListWidget, QMessageBox, QFormLayout, QFrame, QListWidgetItem, QDoubleSpinBox,
    QSizePolicy, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from urls import API_URL_PRODUCTION_COSTS
from utils import http_get, http_post, http_patch, http_delete, make_icon_label

class ProductResultItem(QWidget):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setObjectName("productCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        name_layout = QHBoxLayout()
        name_label = QLabel(f"{product['product']}")
        name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1c1c1c;
        """)
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        price_layout = QHBoxLayout()
        price_label = QLabel(f"Precio: {product['product_price']:.2f} CUP")
        price_label.setStyleSheet("color: #555;")
        price_layout.addWidget(price_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        self.setStyleSheet("""
            QWidget#productCard {
                border: 2px solid #0078D7;
                border-radius: 10px;
                background: #fff;
                padding: 8px;
            }
            QWidget#productCard:hover {
                background: #f0f8ff;
                border-color: #005bb5;
            }
        """)


class ProductionCostsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.setObjectName("productionCostsPage")
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap("icons/production_costs.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Costos de Producción")
        title.setStyleSheet("font-size: 35px; font-weight: 700; color: #222;")
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.main_tabs = QTabWidget()
        layout.addWidget(self.main_tabs, 1)

        self._build_insert_tab()
        self._build_update_tab()
        self._build_delete_tab()
        self._build_view_tab()

#* ------------------- INSERTAR -------------------
    def _build_insert_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignTop)

        form_card = QFrame()
        form_card.setObjectName("card")
        form = QFormLayout(form_card)
        form.setSpacing(12)

        self.add_product = QLineEdit()
        self.add_product_price = QDoubleSpinBox()
        self.add_product_price.setRange(0.01, 1000000)
        self.add_product_price.setDecimals(2)
        self.add_product_price.setSingleStep(10)

        form.addRow(make_icon_label("icons/paper.png", "Producto"), self.add_product)
        form.addRow(make_icon_label("icons/budget.png", "Precio de producción"), self.add_product_price)
        layout.addWidget(form_card)

        btn = QPushButton("Añadir costo de producción")
        btn.setObjectName("primaryBtn")
        btn.clicked.connect(self._add_production_cost)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        self.main_tabs.addTab(tab, "Añadir")

    def _add_production_cost(self):
        name = self.add_product.text().strip()
        price = self.add_product_price.value()
        if not name:
            QMessageBox.warning(self, "Validación", "Debe ingresar un nombre de producto.")
            return

        payload = {"product": name, "product_price": price}
        r = http_post(API_URL_PRODUCTION_COSTS, payload)

        if r is None:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API.")
            return

        if r.status_code in (200, 201):
            QMessageBox.information(self, "Éxito", f"✅ Costo añadido:\n\n📦 {name}\n💰 ${price:.2f}")
            self.add_product.clear()
            self.add_product_price.setValue(0.01)
        else:
            QMessageBox.warning(self, "Fallo", f"No se pudo añadir el costo. Código: {r.status_code}")

#* ------------------- MODIFICAR -------------------
    def _build_update_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.search_product_input = QLineEdit()
        self.search_product_input.setPlaceholderText("Buscar producto por nombre")
        self.search_product_input.returnPressed.connect(self._search_product)

        btn_search = QPushButton("Buscar")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._search_product)

        left.addWidget(self.search_product_input)
        left.addWidget(btn_search)

        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self._on_product_selected)
        left.addWidget(self.results_list)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_card.setMinimumWidth(800)
        form_layout = QFormLayout(form_card)
        form_layout.setSpacing(12)

        self.edit_product_name = QLineEdit()
        self.edit_product_price = QDoubleSpinBox()
        self.edit_product_price.setRange(0.01, 1000000)
        self.edit_product_price.setDecimals(2)
        self.edit_product_price.setSingleStep(10)

        form_layout.addRow(make_icon_label("icons/paper.png", "Producto"), self.edit_product_name)
        form_layout.addRow(make_icon_label("icons/budget.png", "Precio de producción"), self.edit_product_price)

        self.btn_update = QPushButton("Guardar cambios")
        self.btn_update.setObjectName("primaryBtn")
        self.btn_update.setEnabled(False)
        self.btn_update.clicked.connect(self._update_product)

        right.addWidget(form_card, alignment=Qt.AlignHCenter)
        right.addWidget(self.btn_update, alignment=Qt.AlignHCenter)

        layout.addLayout(left, 2)
        layout.addLayout(right, 3)

        self.main_tabs.addTab(tab, "Modificar")


    def _search_product(self):
        q = self.search_product_input.text().strip()
        if not q:
            QMessageBox.information(self, "Input", "Escribe un nombre para buscar.")
            return

        r = http_get(API_URL_PRODUCTION_COSTS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "Error al obtener los datos.")
            return

        data = [p for p in r.json() if q.lower() in p["product"].lower()]
        self.results_list.clear()
        self._cache = {}

        for p in data:
            item = QListWidgetItem()
            widget = ProductResultItem(p)
            item.setSizeHint(widget.sizeHint())

            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)
            self._cache[id(item)] = p

    def _on_product_selected(self):
        items = self.results_list.selectedItems()
        if not items:
            self.btn_update.setEnabled(False)
            return

        p = self._cache.get(id(items[0]))
        if not p:
            return

        self.selected_id = p["idProduction_costs"]
        self.edit_product_name.setText(p["product"])
        self.edit_product_price.setValue(float(p["product_price"]))
        self.btn_update.setEnabled(True)

    def _update_product(self):
        payload = {
            "product": self.edit_product_name.text().strip(),
            "product_price": self.edit_product_price.value()
        }
        r = http_patch(f"{API_URL_PRODUCTION_COSTS}{self.selected_id}/", payload)

        if r and r.status_code in (200, 204):
            QMessageBox.information(self, "Actualizado", "✅ Costo de producción actualizado correctamente.")
            self._search_product()
        else:
            QMessageBox.warning(self, "Error", f"No se pudo actualizar. Código: {r.status_code if r else '???'}")

#* ------------------- ELIMINAR -------------------
    def _build_delete_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.delete_search_input = QLineEdit()
        self.delete_search_input.setPlaceholderText("Buscar producto para eliminar")
        self.delete_search_input.returnPressed.connect(self._search_product_to_delete)

        btn_search = QPushButton("Buscar")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._search_product_to_delete)

        left.addWidget(self.delete_search_input)
        left.addWidget(btn_search)

        self.delete_results_list = QListWidget()
        self.delete_results_list.itemSelectionChanged.connect(self._on_delete_product_selected)
        left.addWidget(self.delete_results_list)

        right = QVBoxLayout()

        container = QVBoxLayout()
        container.setAlignment(Qt.AlignCenter)

        self.delete_placeholder_label = QLabel("🛈 Seleccione un producto para ver los detalles")
        self.delete_placeholder_label.setStyleSheet("""
            font-size: 18px;
            color: #666;
            font-weight: 500;
            padding: 60px;
        """)
        self.delete_placeholder_label.setAlignment(Qt.AlignCenter)

        self.delete_info_card = QFrame()
        self.delete_info_card.setObjectName("card")
        self.delete_info_card.setVisible(False)
        self.delete_info_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        delete_info_main_layout = QVBoxLayout(self.delete_info_card)
        delete_info_main_layout.setAlignment(Qt.AlignRight)  

        name_layout = QHBoxLayout()
        name_icon_label = make_icon_label("icons/paper.png", "Producto:")
        self.delete_product_name = QLabel("")
        self.delete_product_name.setStyleSheet("color: #555;")
        name_layout.addWidget(name_icon_label)
        name_layout.addWidget(self.delete_product_name)
        name_layout.addStretch()

        price_layout = QHBoxLayout()
        price_icon_label = make_icon_label("icons/budget.png", "Precio:")
        self.delete_product_price = QLabel("")
        self.delete_product_price.setStyleSheet("color: #555;")
        price_layout.addWidget(price_icon_label)
        price_layout.addWidget(self.delete_product_price)
        price_layout.addStretch()

        delete_info_main_layout.addLayout(name_layout)
        delete_info_main_layout.addLayout(price_layout)

        self.btn_confirm_delete = QPushButton("Eliminar producto seleccionado")
        self.btn_confirm_delete.setObjectName("dangerBtn")
        self.btn_confirm_delete.setEnabled(False)
        self.btn_confirm_delete.clicked.connect(self._delete_product)

        container.addWidget(self.delete_placeholder_label, alignment=Qt.AlignCenter)
        container.addWidget(self.delete_info_card, alignment=Qt.AlignCenter)
        container.addWidget(self.btn_confirm_delete, alignment=Qt.AlignCenter)

        right.addStretch()
        right.addLayout(container)
        right.addStretch()

        layout.addLayout(left, 2)
        layout.addLayout(right, 3)

        self.main_tabs.addTab(tab, "Eliminar")

    def _search_product_to_delete(self):
        q = self.delete_search_input.text().strip()
        if not q:
            QMessageBox.information(self, "Búsqueda", "Escriba un nombre para buscar.")
            return

        r = http_get(API_URL_PRODUCTION_COSTS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "Error al obtener los datos.")
            return

        data = [p for p in r.json() if q.lower() in p["product"].lower()]
        self.delete_results_list.clear()
        self._delete_cache = {}

        for p in data:
            item = QListWidgetItem()
            widget = ProductResultItem(p)
            item.setSizeHint(widget.sizeHint())
            self.delete_results_list.addItem(item)
            self.delete_results_list.setItemWidget(item, widget)
            self._delete_cache[id(item)] = p

    def _on_delete_product_selected(self):
        items = self.delete_results_list.selectedItems()
        if not items:
            self.btn_confirm_delete.setEnabled(False)
            self.delete_info_card.setVisible(False)
            self.delete_placeholder_label.setVisible(True)
            self.delete_product_name.setText("")
            self.delete_product_price.setText("")
            return

        p = self._delete_cache.get(id(items[0]))
        if not p:
            return

        self.selected_delete_id = p["idProduction_costs"]
        self.selected_delete_name = p["product"]
        self.delete_product_name.setText(p["product"])
        self.delete_product_price.setText(f"{p['product_price']:.2f} CUP")

        self.btn_confirm_delete.setEnabled(True)
        self.delete_placeholder_label.setVisible(False)
        self.delete_info_card.setVisible(True)

    def _delete_product(self):
        if not hasattr(self, "selected_delete_id"):
            QMessageBox.warning(self, "Selección", "Seleccione un producto para eliminar.")
            return

        warning_msg = QMessageBox(self)
        warning_msg.setIcon(QMessageBox.Warning)
        warning_msg.setWindowTitle("⚠️ Advertencia crítica")
        warning_msg.setText(
            f"Está a punto de eliminar el producto:\n\n📦 {self.selected_delete_name}\n\n"
            "⚠️ *Eliminar un producto de producción puede causar errores internos graves.*\n\n"
            "¿Desea continuar?"
        )
        warning_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        warning_msg.setDefaultButton(QMessageBox.No)

        reply = warning_msg.exec()
        if reply != QMessageBox.Yes:
            return

        r = http_delete(f"{API_URL_PRODUCTION_COSTS}{self.selected_delete_id}/")
        if r and r.status_code in (200, 204):
            QMessageBox.information(self, "Eliminado", f"✅ '{self.selected_delete_name}' fue eliminado correctamente.")
            self._search_product_to_delete()
            self.delete_info_card.setVisible(False)
            self.delete_placeholder_label.setVisible(True)
            self.delete_product_name.setText("")
            self.delete_product_price.setText("")
            self.btn_confirm_delete.setEnabled(False)
        else:
            QMessageBox.warning(self, "Error", f"No se pudo eliminar. Código: {r.status_code if r else '???'}")


#* ------------------- VISUALIZAR -------------------
    def _build_view_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setAlignment(Qt.AlignTop)
        tab_layout.setContentsMargins(30, 30, 40, 30)
        tab_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap("icons/view_all.png").scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Costos de Producción")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #1b1b1b;")

        btn_reload = QPushButton("Recargar")
        btn_reload.setObjectName("secondaryBtn")
        btn_reload.setFixedHeight(36)
        btn_reload.clicked.connect(self._load_all_products)

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_reload)
        tab_layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 10px;
                background: #eee;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #0078D7;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #005bb5;
            }
        """)

        container = QWidget()
        self.products_layout = QVBoxLayout(container)
        self.products_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.products_layout.setSpacing(15)
        scroll.setWidget(container)

        tab_layout.addWidget(scroll)

        self.empty_label = QLabel("🛈 No hay productos registrados en este momento.")
        self.empty_label.setStyleSheet("color: #777; font-size: 17px; padding: 60px;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(self.empty_label)
        self.empty_label.hide()

        self.main_tabs.addTab(tab, "Ver todos")

        self._load_all_products()

    def _load_all_products(self):
        r = http_get(API_URL_PRODUCTION_COSTS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudieron obtener los productos.")
            return

        data = r.json()

        while self.products_layout.count():
            item = self.products_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            self.empty_label.show()
            return

        self.empty_label.hide()

        for p in data:
            card = ProductResultItem(p)
            card.setFixedWidth(450)
            self.products_layout.addWidget(card)

    
    def _apply_styles(self):
        self.setStyleSheet("""
        QFrame#card {
            background: #fff;
            border-radius: 10px;
            padding: 20px;
        }

        QLabel {
            color: #222;
            font-size: 14px;
        }
        QLineEdit, QDoubleSpinBox {
            background: #fafafa;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
        }

        QLineEdit:focus, QDoubleSpinBox:focus {
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
        """)
