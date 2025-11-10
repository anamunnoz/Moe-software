import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QListWidget, QMessageBox, QFormLayout, QSpinBox, QFrame,
    QListWidgetItem, QApplication, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from urls import API_URL_ADITIVOS, API_URL_MENSAJERIAS
from utils import http_get, http_post, http_patch, http_delete, make_icon_label
from price.get_rates import convert_to_currency


class GestionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.setObjectName("gestionPage")
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap("icons/gestion2.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Gestión ▸ Aditivos y Mensajerías")
        title.setStyleSheet("font-size: 35px; font-weight: 700; color: #222;")
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.main_tabs = QTabWidget()
        layout.addWidget(self.main_tabs, 1)

        #* ======== ADITIVOS ========
        self.tab_aditivos = QWidget()
        self._build_aditivos_tab()
        self.main_tabs.addTab(self.tab_aditivos, "Aditivos")

        #* ======== MENSAJERÍAS ========
        self.tab_mensajerias = QWidget()
        self._build_mensajerias_tab()
        self.main_tabs.addTab(self.tab_mensajerias, "Mensajerías")

#? =======================================================
#?                   ADITIVOS
#? =======================================================
    def _build_aditivos_tab(self):
        layout = QVBoxLayout(self.tab_aditivos)
        self.aditivos_tabs = QTabWidget()
        layout.addWidget(self.aditivos_tabs)

        # Subpestañas
        self._build_aditivo_insert()
        self._build_aditivo_update()
        self._build_aditivo_delete()
        self._build_aditivo_view()

#* ------------------- INSERTAR ADITIVO -------------------
    def _build_aditivo_insert(self):
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

        self.add_nombre = QLineEdit()
        self.add_precio = QDoubleSpinBox()
        self.add_precio.setRange(0.01, 100000.00)
        self.add_precio.setDecimals(2)
        self.add_precio.setSingleStep(5)
    

        self.add_nombre.returnPressed.connect(self._add_aditivo)

        inner_form.addRow(make_icon_label("icons/additive.png", "Nombre del aditivo"), self.add_nombre)
        inner_form.addRow(make_icon_label("icons/price.png", "Precio"), self.add_precio)

        form_layout.addWidget(form_card)

        spacer = QWidget()
        spacer.setFixedHeight(10)
        form_layout.addWidget(spacer)

        btn = QPushButton("Añadir aditivo")
        btn.setObjectName("primaryBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedWidth(200)

        btn.clicked.connect(self._add_aditivo)
        form_layout.addWidget(btn, alignment=Qt.AlignHCenter)

        main_layout.addWidget(form_block, alignment=Qt.AlignTop)

        self.aditivos_tabs.addTab(tab, "Añadir")

    def _add_aditivo(self):
        nombre = self.add_nombre.text().strip()
        precio = self.add_precio.value()

        if not nombre:
            QMessageBox.warning(self, "Validación", "Debe ingresar un nombre para el aditivo.")
            return

        r_check = http_get(API_URL_ADITIVOS)
        if r_check is None:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API para verificar duplicados.")
            return

        if r_check.status_code == 200:
            all_aditivos = r_check.json()
            nombre_lower = nombre.lower()

            existente = next((a for a in all_aditivos if a["name"].lower() == nombre_lower), None)
            if existente:
                QMessageBox.warning(
                    self,
                    "Aditivo existente",
                    f"⚠️ El aditivo '{nombre}' ya existe en la base de datos.\n\n"
                    f"📋 Información actual:\n"
                    f"✍️ Nombre: {existente['name']}\n"
                    f"💶 Precio: ${existente['price']}"
                )
                return
        else:
            QMessageBox.warning(self, "Error", f"No se pudo verificar duplicados. Código: {r_check.status_code}")
            return

        payload = {"name": nombre, "price": precio}
        r = http_post(API_URL_ADITIVOS, payload)

        if r is None:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API.")
            return

        if r.status_code in (200, 201):
            QMessageBox.information(
                self,
                "Éxito",
                f"🧪 Se ha agregado el aditivo:\n\n✍️ Nombre: {nombre}\n💶 Precio: {precio}\n"
            )
            self.add_nombre.clear()
            self.add_precio.setValue(0.01)
        else:
            QMessageBox.warning(self, "Fallo", f"No se pudo añadir el aditivo. Código: {r.status_code}")


#* ------------------- MODIFICAR ADITIVO -------------------
    def _build_aditivo_update(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignTop)

        self.search_aditivo_input = QLineEdit()
        self.search_aditivo_input.setPlaceholderText("Buscar por nombre de aditivo")
        self.search_aditivo_input.returnPressed.connect(self._search_aditivo)

        btn_search = QPushButton("Buscar aditivo")
        btn_search.setObjectName("primaryBtn")
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.clicked.connect(self._search_aditivo)

        left.addWidget(self.search_aditivo_input)
        left.addWidget(btn_search)

        self.search_aditivo_results = QListWidget()
        self.search_aditivo_results.itemSelectionChanged.connect(self._on_aditivo_selected)
        left.addWidget(self.search_aditivo_results, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QFormLayout(form_card)
        form_layout.setSpacing(12)

        self.edit_nombre = QLineEdit()
        self.edit_precio = QDoubleSpinBox()
        self.edit_precio.setRange(0.01, 100000.00)
        self.edit_precio.setDecimals(2)
        self.edit_precio.setSingleStep(5)

        form_layout.addRow(make_icon_label("icons/additive.png", "Nombre del aditivo"), self.edit_nombre)
        form_layout.addRow(make_icon_label("icons/price.png", "Precio"), self.edit_precio)

        self.btn_update_aditivo = QPushButton("Aplicar cambios")
        self.btn_update_aditivo.setObjectName("primaryBtn")
        self.btn_update_aditivo.setCursor(Qt.PointingHandCursor)
        self.btn_update_aditivo.setEnabled(False)
        self.btn_update_aditivo.clicked.connect(self._update_aditivo)

        form_layout.addRow(QWidget(), self.btn_update_aditivo)
        right.addWidget(form_card)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)

        self.aditivos_tabs.addTab(tab, "Modificar")


    def _search_aditivo(self):
        q = self.search_aditivo_input.text().strip()
        if not q:
            QMessageBox.information(self, "Input", "Escribe un nombre para buscar.")
            self.search_aditivo_results.clear()
            return

        r = http_get(API_URL_ADITIVOS)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al buscar aditivos.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        all_aditivos = r.json()
        q_lower = q.lower()

        data = [a for a in all_aditivos if q_lower in a["name"].lower()]

        self.search_aditivo_results.clear()
        self._aditivo_cache = {}

        if not data:
            self.search_aditivo_results.addItem("No se encontraron resultados")
            return

        for a in data:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            name = QLabel(a["name"])
            name.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            price = QLabel(f"${a['price']}")
            price.setStyleSheet("font-size: 13px; color: #666;")

            card_layout.addWidget(name)
            card_layout.addStretch()
            card_layout.addWidget(price)

            list_item = QListWidgetItem(self.search_aditivo_results)
            list_item.setSizeHint(card.sizeHint())
            self.search_aditivo_results.addItem(list_item)
            self.search_aditivo_results.setItemWidget(list_item, card)
            self._aditivo_cache[id(list_item)] = a


    def _on_aditivo_selected(self):
        items = self.search_aditivo_results.selectedItems()
        if not items:
            self.btn_update_aditivo.setEnabled(False)
            return

        list_item = items[0]
        aditivo = self._aditivo_cache.get(id(list_item))

        if aditivo is None:
            self.btn_update_aditivo.setEnabled(False)
            return

        # Rellenar los campos de la derecha con los datos del aditivo
        self.selected_aditivo_id = aditivo["idAdditive"]
        self.edit_nombre.setText(aditivo["name"])
        self.edit_precio.setValue(float(aditivo["price"]))

        self.btn_update_aditivo.setEnabled(True)


    def _update_aditivo(self):
        if not hasattr(self, "selected_aditivo_id"):
            QMessageBox.warning(self, "Error", "Seleccione un aditivo para actualizar.")
            return

        nombre = self.edit_nombre.text().strip()
        precio = self.edit_precio.value()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        payload = {"name": nombre, "price": precio}

        r = http_patch(f"{API_URL_ADITIVOS}{self.selected_aditivo_id}/", payload)
        if r is None:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API.")
            return

        if r.status_code in (200, 204):
            QMessageBox.information(
                self,
                "Actualizado",
                f"✅ Aditivo actualizado correctamente:\n\n✍️ Nombre: {nombre}\n💶 Precio: {precio}"
            )
            self._search_aditivo()
        else:
            QMessageBox.warning(self, "Fallo", f"No se pudo actualizar el aditivo. Código: {r.status_code}")


#* ------------------- ELIMINAR ADITIVO -------------------
    def _build_aditivo_delete(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.search_delete_aditivo = QLineEdit()
        self.search_delete_aditivo.setPlaceholderText("Buscar aditivo por nombre")
        self.search_delete_aditivo.returnPressed.connect(self._search_delete_aditivo)

        btn_search = QPushButton("Buscar")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._search_delete_aditivo)
        left.addWidget(self.search_delete_aditivo)
        left.addWidget(btn_search)

        self.list_delete_aditivo = QListWidget()
        self.list_delete_aditivo.itemSelectionChanged.connect(self._on_delete_aditivo_selected)
        left.addWidget(self.list_delete_aditivo, 1)

        right = QVBoxLayout()

        self.delete_info_container = QWidget()
        self.delete_info_container.setObjectName("infoContainer")
        self.delete_info_layout = QVBoxLayout(self.delete_info_container)
        self.delete_info_layout.setAlignment(Qt.AlignCenter)

        self._clear_delete_info(show_placeholder=True)

        right.addWidget(self.delete_info_container, 1)

        self.btn_delete_aditivo = QPushButton("Eliminar aditivo seleccionado")
        self.btn_delete_aditivo.setObjectName("dangerBtn")
        self.btn_delete_aditivo.setEnabled(False)
        self.btn_delete_aditivo.clicked.connect(self._delete_aditivo)
        right.addWidget(self.btn_delete_aditivo, alignment=Qt.AlignRight)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)
        self.aditivos_tabs.addTab(tab, "Eliminar")

    def _search_delete_aditivo(self):
        q = self.search_delete_aditivo.text().strip()
        if not q:
            QMessageBox.information(self, "Input", "Escribe un nombre para buscar.")
            self.list_delete_aditivo.clear()
            return

        r = http_get(API_URL_ADITIVOS)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al buscar aditivos.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        all_aditivos = r.json()
        q_lower = q.lower()

        data = [a for a in all_aditivos if q_lower in a["name"].lower()]

        self.list_delete_aditivo.clear()
        self._delete_aditivo_cache = {}

        if not data:
            self.list_delete_aditivo.addItem("No se encontraron resultados")
            return

        for a in data:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            name = QLabel(a["name"])
            name.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            price = QLabel(f"${a['price']}")
            price.setStyleSheet("font-size: 13px; color: #666;")

            card_layout.addWidget(name)
            card_layout.addStretch()
            card_layout.addWidget(price)

            list_item = QListWidgetItem(self.list_delete_aditivo)
            list_item.setSizeHint(card.sizeHint())
            self.list_delete_aditivo.addItem(list_item)
            self.list_delete_aditivo.setItemWidget(list_item, card)
            self._delete_aditivo_cache[id(list_item)] = a

    def _on_delete_aditivo_selected(self):
        items = self.list_delete_aditivo.selectedItems()
        if not items:
            self.btn_delete_aditivo.setEnabled(False)
            self._clear_delete_info(show_placeholder=True)
            return

        list_item = items[0]
        aditivo = self._delete_aditivo_cache.get(id(list_item))
        if not aditivo:
            self.btn_delete_aditivo.setEnabled(False)
            self._clear_delete_info(show_placeholder=True)
            return

        self.selected_delete_aditivo = aditivo
        self.btn_delete_aditivo.setEnabled(True)

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

        form.addRow(make_icon_line("icons/additive.png", f"Nombre: {aditivo['name']}"))
        form.addRow(make_icon_line("icons/price.png", f"Precio: ${aditivo['price']}"))

        self.delete_info_layout.addWidget(info_card, alignment=Qt.AlignCenter)

    def _clear_delete_info(self, show_placeholder=True):
        while self.delete_info_layout.count():
            child = self.delete_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not show_placeholder:
            return

        placeholder = QWidget()
        ph_layout = QVBoxLayout(placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_pix = QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pix)
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Seleccione un aditivo para ver los detalles.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon_label)
        ph_layout.addWidget(text_label)
        self.delete_info_layout.addWidget(placeholder)

    def _delete_aditivo(self):
        if not hasattr(self, "selected_delete_aditivo"):
            QMessageBox.warning(self, "Eliminar aditivo", "Selecciona un aditivo para eliminar.")
            return

        ad = self.selected_delete_aditivo
        msg = (
            f"¿Estás seguro de que deseas eliminar este aditivo?\n\n"
            f"✍️ Nombre: {ad['name']}\n"
            f"💶 Precio: ${ad['price']}"
        )

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            msg,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        r = http_delete(f"{API_URL_ADITIVOS}{ad['idAdditive']}/")
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al intentar eliminar el aditivo.")
            return

        if r.status_code in (200, 204):
            QMessageBox.information(
                self,
                "Aditivo eliminado",
                f"🧪 El aditivo '{ad['name']}' fue eliminado correctamente."
            )
            self._search_delete_aditivo()
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo eliminar el aditivo.\nCódigo: {r.status_code}\n{r.text}"
            )

#* ------------------- LISTAR ADITIVO -------------------
    def _build_aditivo_view(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(20)

        left = QVBoxLayout()
        left.setSpacing(12)

        search_layout = QVBoxLayout()
        search_layout.setSpacing(8)
        self.search_view_aditivo = QLineEdit()
        self.search_view_aditivo.setPlaceholderText("Buscar aditivo por nombre...")
        self.search_view_aditivo.returnPressed.connect(self._search_for_view_aditivo)
        self.search_view_aditivo.setClearButtonEnabled(True)

        btn = QPushButton("Buscar")
        btn.setObjectName("primaryBtn")
        btn.clicked.connect(self._search_for_view_aditivo)

        search_layout.addWidget(self.search_view_aditivo)
        search_layout.addWidget(btn)
        left.addLayout(search_layout)

        self.view_aditivo_results = QListWidget()
        self.view_aditivo_results.itemSelectionChanged.connect(self._on_view_selection_aditivo)
        left.addWidget(self.view_aditivo_results, 1)

        right = QVBoxLayout()
        right.setSpacing(12)

        self.view_info_container_aditivo = QWidget()
        self.view_info_container_aditivo.setObjectName("infoContainer")
        self.view_info_layout_aditivo = QVBoxLayout(self.view_info_container_aditivo)
        self.view_info_layout_aditivo.setAlignment(Qt.AlignCenter)

        self.view_placeholder_aditivo = QWidget()
        ph_layout = QVBoxLayout(self.view_placeholder_aditivo)
        ph_layout.setAlignment(Qt.AlignCenter)
        icon = QLabel()
        icon.setPixmap(QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        text = QLabel("Busca un aditivo y selecciona uno para ver sus detalles.")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")
        ph_layout.addWidget(icon)
        ph_layout.addWidget(text)
        self.view_info_layout_aditivo.addWidget(self.view_placeholder_aditivo)

        right.addWidget(self.view_info_container_aditivo, 1)
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(15)
        btns_layout.setAlignment(Qt.AlignCenter)

        self.btn_copy_selected = QPushButton("Copiar seleccionado")
        self.btn_copy_selected.setObjectName("primaryBtn")
        self.btn_copy_selected.setCursor(Qt.PointingHandCursor)
        self.btn_copy_selected.clicked.connect(self._copy_selected_aditivo)

        self.btn_copy_all = QPushButton("Copiar todos")
        self.btn_copy_all.setObjectName("primaryBtn")
        self.btn_copy_all.setCursor(Qt.PointingHandCursor)
        self.btn_copy_all.clicked.connect(self._copy_all_aditivos)

        btns_layout.addWidget(self.btn_copy_selected)
        btns_layout.addWidget(self.btn_copy_all)

        right.addLayout(btns_layout)

        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 1)
        self.aditivos_tabs.addTab(tab, "Copiar aditivo")

    def _search_for_view_aditivo(self):
        q = self.search_view_aditivo.text().strip()
        if not q:
            QMessageBox.information(self, "Entrada", "Escribe un nombre de aditivo para buscar.")
            self.view_aditivo_results.clear()
            return

        r = http_get(API_URL_ADITIVOS)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        all_aditivos = r.json()
        q_lower = q.lower()

        data = [a for a in all_aditivos if q_lower in a["name"].lower()]

        self.view_aditivo_results.clear()
        self._view_aditivo_cache = {}

        if not data:
            self.view_aditivo_results.addItem("No se encontraron resultafos")
            return

        for ad in data:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            name = QLabel(ad["name"])
            name.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            price = QLabel(f"${ad['price']}")
            price.setStyleSheet("font-size: 13px; color: #666;")

            card_layout.addWidget(name)
            card_layout.addStretch()
            card_layout.addWidget(price)

            list_item = QListWidgetItem(self.view_aditivo_results)
            list_item.setSizeHint(card.sizeHint())
            self.view_aditivo_results.addItem(list_item)
            self.view_aditivo_results.setItemWidget(list_item, card)
            self._view_aditivo_cache[id(list_item)] = ad

    def _on_view_selection_aditivo(self):
        items = self.view_aditivo_results.selectedItems()
        if not items:
            self._clear_view_info_aditivo(show_placeholder=True)
            return

        list_item = items[0]
        aditivo = self._view_aditivo_cache.get(id(list_item))
        if not aditivo:
            self._clear_view_info_aditivo(show_placeholder=True)
            return

        self._clear_view_info_aditivo(show_placeholder=False)

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

        form.addRow(make_icon_line("icons/additive.png", f"Nombre: {aditivo['name']}"))
        form.addRow(make_icon_line("icons/price.png", f"Precio: ${aditivo['price']}"))

        self.view_info_layout_aditivo.addWidget(info_card, alignment=Qt.AlignCenter)

    def _clear_view_info_aditivo(self, show_placeholder=True):
        while self.view_info_layout_aditivo.count():
            child = self.view_info_layout_aditivo.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not show_placeholder:
            return

        self.view_placeholder_aditivo = QWidget()
        ph_layout = QVBoxLayout(self.view_placeholder_aditivo)
        ph_layout.setAlignment(Qt.AlignCenter)

        icon = QLabel()
        icon.setPixmap(QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        text = QLabel("Busca un aditivo y selecciona uno para ver sus detalles.")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon)
        ph_layout.addWidget(text)
        self.view_info_layout_aditivo.addWidget(self.view_placeholder_aditivo)

    def _copy_selected_aditivo(self):
        items = self.view_aditivo_results.selectedItems()
        if not items:
            QMessageBox.information(self, "Copiar", "No hay ningún aditivo seleccionado.")
            return

        list_item = items[0]
        aditivo = self._view_aditivo_cache.get(id(list_item))
        if not aditivo:
            QMessageBox.warning(self, "Copiar", "Error al obtener el aditivo seleccionado.")
            return

        cup_price = convert_to_currency(aditivo['price'], 'USD', 'CUP')
        mlc_price = convert_to_currency(aditivo['price'], 'USD', 'MLC')

        text = f"💰{aditivo['name']}\nPrecio: {aditivo['price']} USD | {cup_price} CUP | {mlc_price} MLC"
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", f"✅ Se copió al portapapeles:\n\n{text}")

    def _copy_all_aditivos(self):
        """Copia todos los aditivos que existen en la base de datos."""
        r = http_get(API_URL_ADITIVOS)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al intentar obtener los aditivos.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error al obtener aditivos: {r.status_code}")
            return

        all_aditivos = r.json()
        if not all_aditivos:
            QMessageBox.information(self, "Copiar todos", "No hay aditivos en la base de datos.")
            return


        lines = [
            f"💰 {a['name']}\nPrecio: {a['price']} USD | {convert_to_currency(a['price'], 'USD', 'CUP')} CUP | {convert_to_currency(a['price'], 'USD', 'MLC')} MLC"
            for a in all_aditivos
        ]
        text = "\n".join(lines)

        QApplication.clipboard().setText(text)
        QMessageBox.information(
            self,
            "Copiado",
            f"✅ Se copiaron {len(lines)} aditivos de la base de datos al portapapeles."
        )




#? =======================================================
#?                   MENSAJERÍAS
#? =======================================================
    def _build_mensajerias_tab(self):
        layout = QVBoxLayout(self.tab_mensajerias)
        self.mensajerias_tabs = QTabWidget()
        layout.addWidget(self.mensajerias_tabs)

        # Subpestañas
        self._build_mensajeria_insert()
        self._build_mensajeria_update()
        self._build_mensajeria_delete()
        self._build_mensajeria_list()

#* ------------------- INSERTAR MENSAJERÍA -------------------
    def _build_mensajeria_insert(self):
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

        self.add_zona = QLineEdit()
        self.add_descripcion = QLineEdit()
        self.add_precio_m = QDoubleSpinBox()
        self.add_precio_m.setRange(1, 100000.00)
        self.add_precio_m.setDecimals(2)  
        self.add_precio_m.setSingleStep(5)

        self.add_zona.returnPressed.connect(self._add_mensajeria)
        self.add_descripcion.returnPressed.connect(self._add_mensajeria)

        inner_form.addRow(make_icon_label("icons/zone.png", "Zona"), self.add_zona)
        inner_form.addRow(make_icon_label("icons/description.png", "Descripción"), self.add_descripcion)
        inner_form.addRow(make_icon_label("icons/price.png", "Precio"), self.add_precio_m)

        form_layout.addWidget(form_card)

        spacer = QWidget()
        spacer.setFixedHeight(10)
        form_layout.addWidget(spacer)

        btn = QPushButton("Añadir mensajería")
        btn.setObjectName("primaryBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedWidth(200)
        btn.clicked.connect(self._add_mensajeria)

        form_layout.addWidget(btn, alignment=Qt.AlignHCenter)

        main_layout.addWidget(form_block, alignment=Qt.AlignTop)

        self.mensajerias_tabs.addTab(tab, "Añadir")


    def _add_mensajeria(self):
        zona = self.add_zona.text().strip()
        descripcion = self.add_descripcion.text().strip()
        precio = self.add_precio_m.value()

        if not zona or not descripcion:
            QMessageBox.warning(self, "Error", "Debe completar todos los campos.")
            return

        payload = {
            "zone": zona,
            "description": descripcion,
            "price": precio
        }

        r = http_post(API_URL_MENSAJERIAS, payload)

        if r is None:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API.")
            return

        try:
            data = r.json()
        except Exception:
            data = {}

        if r.status_code == 200 and data.get("error") == "exists":
            zona_existente = data.get("zone", "Desconocida")
            precio_existente = data.get("price", "N/A")
            descripcion_existente = data.get("description", "Sin descripción")

            QMessageBox.information(
                self,
                "Zona existente",
                f"⚠️ La zona '{zona_existente}' ya existe en la base de datos.\n\n"
                f"📋 Información actual:\n"
                f"💲 Precio actual: {precio_existente}\n"
                f"📝 Descripción: {descripcion_existente}"
            )
            return

        elif r.status_code in (200, 201):
            QMessageBox.information(
                self,
                "Éxito",
                f"✅ Mensajería añadida correctamente:\n\n"
                f"📍 Zona: {zona}\n"
                f"📝 Descripción: {descripcion}\n"
                f"💲 Precio: {precio}"
            )
            self.add_zona.clear()
            self.add_descripcion.clear()
            self.add_precio_m.setValue(1)
        else:
            QMessageBox.warning(self, "Fallo", f"No se pudo añadir: {r.status_code}")



#* ---------------------- MODIFICAR MENSAJERÍA ----------------------
    def _build_mensajeria_update(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.search_mensajeria_input = QLineEdit()
        self.search_mensajeria_input.setPlaceholderText("Buscar mensajería por zona")
        self.search_mensajeria_input.returnPressed.connect(self._search_mensajeria_update)

        btn_search = QPushButton("Buscar")
        btn_search.setObjectName("primaryBtn")
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.clicked.connect(self._search_mensajeria_update)

        left.addWidget(self.search_mensajeria_input)
        left.addWidget(btn_search)

        self.list_mensajeria_update = QListWidget()
        self.list_mensajeria_update.itemSelectionChanged.connect(self._on_mensajeria_update_selected)
        left.addWidget(self.list_mensajeria_update, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QFormLayout(form_card)
        form_layout.setSpacing(12)

        self.edit_zona_m = QLineEdit()
        self.edit_descripcion_m = QLineEdit()
        self.edit_precio_m = QDoubleSpinBox()
        self.edit_precio_m.setRange(0.01, 100000.00)
        self.edit_precio_m.setDecimals(2) 
        self.edit_precio_m.setSingleStep(5)

        form_layout.addRow(make_icon_label("icons/zone.png", "Zona"), self.edit_zona_m)
        form_layout.addRow(make_icon_label("icons/description.png", "Descripción"), self.edit_descripcion_m)
        form_layout.addRow(make_icon_label("icons/price.png", "Precio"), self.edit_precio_m)

        self.btn_update_mensajeria = QPushButton("Actualizar mensajería")
        self.btn_update_mensajeria.setObjectName("primaryBtn")
        self.btn_update_mensajeria.setCursor(Qt.PointingHandCursor)
        self.btn_update_mensajeria.setEnabled(False)
        self.btn_update_mensajeria.clicked.connect(self._update_mensajeria_submit)

        form_layout.addRow(QWidget(), self.btn_update_mensajeria)

        right.addWidget(form_card)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)
        self.mensajerias_tabs.addTab(tab, "Modificar")


    def _search_mensajeria_update(self):
        q = self.search_mensajeria_input.text().strip()
        if not q:
            QMessageBox.information(self, "Input", "Ingrese una zona para buscar.")
            self.list_mensajeria_update.clear()
            return

        r = http_get(API_URL_MENSAJERIAS)
        if r is None or r.status_code != 200:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API.")
            return

        all_mensajerias = r.json()
        q_lower = q.lower()
        filtered = [m for m in all_mensajerias if q_lower in m["zone"].lower()]

        self.list_mensajeria_update.clear()
        self._mensajeria_update_cache = {}

        if not filtered:
            self.list_mensajeria_update.addItem("No se encontraron resultados")
            return

        for a in filtered:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            zone = QLabel(a["zone"])
            zone.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            price = QLabel(f"${a['price']}")
            price.setStyleSheet("font-size: 13px; color: #666;")
            description = QLabel(a["description"])
            description.setStyleSheet("font-size: 13px; color: #666;")

            card_layout.addWidget(zone)
            card_layout.addStretch()
            card_layout.addWidget(price)
            card_layout.addWidget(description)

            list_item = QListWidgetItem(self.list_mensajeria_update)
            list_item.setSizeHint(card.sizeHint())
            self.list_mensajeria_update.addItem(list_item)
            self.list_mensajeria_update.setItemWidget(list_item, card)
            self._mensajeria_update_cache[id(list_item)] = a


    def _on_mensajeria_update_selected(self):
        items = self.list_mensajeria_update.selectedItems()
        if not items:
            self.btn_update_mensajeria.setEnabled(False)
            return

        list_item = items[0]
        m = self._mensajeria_update_cache.get(id(list_item))
        if not m:
            self.btn_update_mensajeria.setEnabled(False)
            return

        self.selected_mensajeria_id = m["idDelivery"]
        self.edit_zona_m.setText(m["zone"])
        self.edit_descripcion_m.setText(m["description"])
        self.edit_precio_m.setValue(float(m["price"]))
        self.btn_update_mensajeria.setEnabled(True)


    def _update_mensajeria_submit(self):
        if not hasattr(self, "selected_mensajeria_id"):
            QMessageBox.warning(self, "Error", "Debe seleccionar una mensajería para actualizar.")
            return

        zona = self.edit_zona_m.text().strip()
        descripcion = self.edit_descripcion_m.text().strip()
        precio = self.edit_precio_m.value()

        if not zona or not descripcion:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        payload = {"zone": zona, "description": descripcion, "price": precio}
        r = http_patch(f"{API_URL_MENSAJERIAS}{self.selected_mensajeria_id}/", payload)

        if r is None:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API.")
            return
        elif r.status_code in (200, 204):
            QMessageBox.information(
                self,
                "Actualizado",
                f"✅ Mensajería actualizada correctamente:\n\n"
                f"📍 Zona: {zona}\n"
                f"📝 Descripción: {descripcion}\n"
                f"💲 Precio: {precio}"
            )
            self._search_mensajeria_update()
        else:
            QMessageBox.warning(self, "Fallo", f"No se pudo actualizar: {r.status_code}")

#* ------------------- ELIMINAR MENSAJERÍA -------------------
    def _build_mensajeria_delete(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.search_delete_mensajeria = QLineEdit()
        self.search_delete_mensajeria.setPlaceholderText("Buscar mensajería por zona")
        self.search_delete_mensajeria.returnPressed.connect(self._search_delete_mensajeria)

        btn_search = QPushButton("Buscar")
        btn_search.setObjectName("primaryBtn")
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.clicked.connect(self._search_delete_mensajeria)

        left.addWidget(self.search_delete_mensajeria)
        left.addWidget(btn_search)

        self.list_delete_mensajeria = QListWidget()
        self.list_delete_mensajeria.itemSelectionChanged.connect(self._on_delete_mensajeria_selected)
        left.addWidget(self.list_delete_mensajeria, 1)

        right = QVBoxLayout()

        self.delete_info_container_m = QWidget()
        self.delete_info_container_m.setObjectName("infoContainer")
        self.delete_info_layout_m = QVBoxLayout(self.delete_info_container_m)
        self.delete_info_layout_m.setAlignment(Qt.AlignCenter)

        self._clear_delete_info_mensajeria(show_placeholder=True)

        right.addWidget(self.delete_info_container_m, 1)

        self.btn_delete_mensajeria = QPushButton("Eliminar mensajería seleccionada")
        self.btn_delete_mensajeria.setObjectName("dangerBtn")
        self.btn_delete_mensajeria.setEnabled(False)
        self.btn_delete_mensajeria.clicked.connect(self._delete_mensajeria)
        right.addWidget(self.btn_delete_mensajeria, alignment=Qt.AlignRight)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)

        self.mensajerias_tabs.addTab(tab, "Eliminar")


    def _search_delete_mensajeria(self):
        q = self.search_delete_mensajeria.text().strip()
        if not q:
            self.list_delete_mensajeria.clear()
            return

        r = http_get(API_URL_MENSAJERIAS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo obtener la lista.")
            return

        all_mensajerias = r.json()
        q_lower = q.lower()
        data = [m for m in all_mensajerias if q_lower in m["zone"].lower()]

        self.list_delete_mensajeria.clear()
        self._delete_mensajeria_cache = {}

        if not data:
            self.list_delete_mensajeria.addItem("No se encontraron resultados")
            return

        for a in data:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            zone = QLabel(a["zone"])
            zone.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            price = QLabel(f"${a['price']}")
            price.setStyleSheet("font-size: 13px; color: #666;")


            card_layout.addWidget(zone)
            card_layout.addStretch()
            card_layout.addWidget(price)

            list_item = QListWidgetItem(self.list_delete_mensajeria)
            list_item.setSizeHint(card.sizeHint())
            self.list_delete_mensajeria.addItem(list_item)
            self.list_delete_mensajeria.setItemWidget(list_item, card)
            self._delete_mensajeria_cache[id(list_item)] = a


    def _on_delete_mensajeria_selected(self):
        items = self.list_delete_mensajeria.selectedItems()
        if not items:
            self.btn_delete_mensajeria.setEnabled(False)
            self._clear_delete_info_mensajeria(show_placeholder=True)
            return

        list_item = items[0]
        mensajeria = self._delete_mensajeria_cache.get(id(list_item))  # CAMBIO AQUÍ
        if not mensajeria:
            self.btn_delete_mensajeria.setEnabled(False)
            self._clear_delete_info_mensajeria(show_placeholder=True)
            return

        self.selected_delete_mensajeria = mensajeria  # CAMBIO AQUÍ
        self.btn_delete_mensajeria.setEnabled(True)

        self._clear_delete_info_mensajeria(show_placeholder=False)
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

        form.addRow(make_icon_line("icons/zone.png", f"Zona: {mensajeria['zone']}"))  # CAMBIO AQUÍ
        form.addRow(make_icon_line("icons/description.png", f"Descripción: {mensajeria['description']}"))  # CAMBIO AQUÍ
        form.addRow(make_icon_line("icons/price.png", f"Precio: ${mensajeria['price']}"))  # CAMBIO AQUÍ

        self.delete_info_layout_m.addWidget(info_card, alignment=Qt.AlignCenter)


    def _clear_delete_info_mensajeria(self, show_placeholder=True):
        while self.delete_info_layout_m.count():
            child = self.delete_info_layout_m.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not show_placeholder:
            return

        placeholder = QWidget()
        ph_layout = QVBoxLayout(placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Seleccione una mensajería para ver los detalles.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon_label)
        ph_layout.addWidget(text_label)
        self.delete_info_layout_m.addWidget(placeholder)


    def _delete_mensajeria(self):
        if not hasattr(self, "selected_delete_mensajeria"):
            QMessageBox.warning(self, "Eliminar", "Seleccione una mensajería para eliminar.")
            return

        m = self.selected_delete_mensajeria
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Desea eliminar la mensajería?\n\n📍 Zona: {m['zone']}\n📝 Descripción: {m['description']}\n💲 Precio: {m['price']}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        r = http_delete(f"{API_URL_MENSAJERIAS}{m['idDelivery']}/")
        if r and r.status_code in (200, 204):
            QMessageBox.information(self, "Éxito", f"Mensajería '{m['zone']}' eliminada correctamente.")
            self._search_delete_mensajeria()
        else:
            QMessageBox.warning(self, "Fallo", "No se pudo eliminar la mensajería.")


#* ---------------------- LISTAR MENSAJERÍA ----------------------
    def _build_mensajeria_list(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.search_list_mensajeria = QLineEdit()
        self.search_list_mensajeria.setPlaceholderText("Buscar mensajería por zona")
        self.search_list_mensajeria.returnPressed.connect(self._search_list_mensajeria)

        btn_search = QPushButton("Buscar")
        btn_search.setObjectName("primaryBtn")
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.clicked.connect(self._search_list_mensajeria)

        left.addWidget(self.search_list_mensajeria)
        left.addWidget(btn_search)

        self.list_mensajeria_list = QListWidget()
        self.list_mensajeria_list.itemSelectionChanged.connect(self._on_list_mensajeria_selected)
        left.addWidget(self.list_mensajeria_list, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        self.info_container_list_m = QWidget()
        self.info_container_list_m.setObjectName("infoContainer")
        self.info_layout_list_m = QVBoxLayout(self.info_container_list_m)
        self.info_layout_list_m.setAlignment(Qt.AlignCenter)

        self._clear_list_info_mensajeria(show_placeholder=True)
        right.addWidget(self.info_container_list_m, 1)

        btns_layout = QHBoxLayout()
        self.btn_copy_selected_m = QPushButton("Copiar seleccionada")
        self.btn_copy_selected_m.setObjectName("primaryBtn")
        self.btn_copy_selected_m.setCursor(Qt.PointingHandCursor)
        self.btn_copy_selected_m.setEnabled(False)
        self.btn_copy_selected_m.clicked.connect(self._copy_selected_mensajeria)

        self.btn_copy_all_m = QPushButton("Copiar todas")
        self.btn_copy_all_m.setObjectName("primaryBtn")
        self.btn_copy_all_m.setCursor(Qt.PointingHandCursor)
        self.btn_copy_all_m.clicked.connect(self._copy_all_mensajerias)

        btns_layout.addWidget(self.btn_copy_selected_m)
        btns_layout.addWidget(self.btn_copy_all_m)
        right.addLayout(btns_layout)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)
        self.mensajerias_tabs.addTab(tab, "Copiar mensajería")


    def _search_list_mensajeria(self):
        q = self.search_list_mensajeria.text().strip()
        r = http_get(API_URL_MENSAJERIAS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo conectar con la API.")
            return

        all_mensajerias = r.json()
        if q:
            q_lower = q.lower()
            data = [m for m in all_mensajerias if q_lower in m["zone"].lower()]
        else:
            data = all_mensajerias

        self.list_mensajeria_list.clear()
        self._mensajeria_list_cache = {}

        if not data:
            self.list_mensajeria_list.addItem("No se encontraron resultados")
            return

        for a in data:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            zone = QLabel(a["zone"])
            zone.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            price = QLabel(f"${a['price']}")
            price.setStyleSheet("font-size: 13px; color: #666;")

            card_layout.addWidget(zone)
            card_layout.addStretch()
            card_layout.addWidget(price)

            list_item = QListWidgetItem(self.list_mensajeria_list)
            list_item.setSizeHint(card.sizeHint())
            self.list_mensajeria_list.addItem(list_item)
            self.list_mensajeria_list.setItemWidget(list_item, card)
            self._mensajeria_list_cache[id(list_item)] = a


    def _on_list_mensajeria_selected(self):
        items = self.list_mensajeria_list.selectedItems()
        if not items:
            self.btn_copy_selected_m.setEnabled(False)
            self._clear_list_info_mensajeria(show_placeholder=True)
            return

        list_item = items[0]
        mensajeria = self._mensajeria_list_cache.get(id(list_item))
        if not mensajeria:
            self.btn_copy_selected_m.setEnabled(False)
            self._clear_list_info_mensajeria(show_placeholder=True)
            return

        self.selected_list_mensajeria = mensajeria 
        self.btn_copy_selected_m.setEnabled(True)

        self._clear_list_info_mensajeria(show_placeholder=False)
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

        form.addRow(make_icon_line("icons/zone.png", f"Zona: {mensajeria['zone']}"))
        form.addRow(make_icon_line("icons/description.png", f"Descripción: {mensajeria['description']}"))
        form.addRow(make_icon_line("icons/price.png", f"Precio: ${mensajeria['price']}"))

        self.info_layout_list_m.addWidget(info_card, alignment=Qt.AlignCenter)


    def _clear_list_info_mensajeria(self, show_placeholder=True):
        while self.info_layout_list_m.count():
            child = self.info_layout_list_m.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not show_placeholder:
            return

        placeholder = QWidget()
        ph_layout = QVBoxLayout(placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(QPixmap("icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Seleccione una mensajería para ver los detalles.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon_label)
        ph_layout.addWidget(text_label)
        self.info_layout_list_m.addWidget(placeholder)


    def _copy_selected_mensajeria(self):
        if not hasattr(self, "selected_list_mensajeria"):
            QMessageBox.warning(self, "Copiar", "Seleccione una mensajería para copiar.")
            return

        m = self.selected_list_mensajeria
        text = f"📍 {m['zone']}\n📝 Descripción: {m['description']}\nPrecio: ${m['price']}"
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", f"Mensajería '{m['zone']}' copiada al portapapeles.")


    def _copy_all_mensajerias(self):
        r = http_get(API_URL_MENSAJERIAS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo obtener las mensajerías desde la API.")
            return

        all_mensajerias = r.json()
        if not all_mensajerias:
            QMessageBox.information(self, "Copiar", "No hay mensajerías en la base de datos.")
            return

        lines = []
        for m in all_mensajerias:
            lines.append(f"📍 {m['zone']}\n📝 Descripción: {m['description']}\nPrecio: ${m['price']}\n")

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", f"Se copiaron {len(lines)} mensajerías al portapapeles.")

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

