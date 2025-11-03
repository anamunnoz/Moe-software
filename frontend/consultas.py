from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QListWidget, QMessageBox, QLabel, QTabWidget,
    QHBoxLayout, QFrame, QListWidgetItem, QApplication, QComboBox, QListView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap,  QStandardItemModel, QStandardItem
from utils import http_get
from urls import API_URL_BOOKS, API_URL_ADITIVOS, API_URL_MENSAJERIAS
from price.get_rates import convert_to_currency
from price.price import calculate_price
import json


with open('./price/fabrication.json', 'r', encoding='utf-8') as f:
    costs = json.load(f)


class MultiSelectComboBox(QComboBox):
    selection_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.setView(QListView(self))
        self.view().pressed.connect(self._on_item_pressed)
        self.view().viewport().installEventFilter(self) 

        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Selecciona uno o más aditivos...")
        self.lineEdit().setAlignment(Qt.AlignLeft)

        self._selected_items = []

    def add_checkable_item(self, text, data=None):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        item.setData(data, Qt.UserRole)
        self.model().appendRow(item)

    def _on_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        item.setCheckState(new_state)
        self._update_selection()

    def eventFilter(self, source, event):
        from PySide6.QtCore import QEvent
        if source is self.view().viewport() and event.type() == QEvent.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                self._on_item_pressed(index)
                return True
        return super().eventFilter(source, event)

    def _update_selection(self):
        self._selected_items = [
            self.model().item(i).data(Qt.UserRole)
            for i in range(self.model().rowCount())
            if self.model().item(i).checkState() == Qt.Checked
        ]

        selected_texts = [
            self.model().item(i).text()
            for i in range(self.model().rowCount())
            if self.model().item(i).checkState() == Qt.Checked
        ]
        self.lineEdit().setText(", ".join(selected_texts))
        self.selection_changed.emit(self._selected_items)

    def selected_items(self):
        return self._selected_items



class ConsultasPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_cache = {}
        self.setObjectName("consultasPage")
        self._build_ui()
        self._apply_styles()


    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap("icons/asking.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Consulta de precios")
        title.setStyleSheet("font-size: 35px; font-weight: 700; color: #222;")
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_books_tab()
        self._build_mensajerias_tab()
        self._build_aditivos_tab()

#? -------------------------------
#? Libros
#? -------------------------------
    def _build_books_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignTop)
        

        self.search_book_input = QLineEdit()
        self.search_book_input.setPlaceholderText("Buscar libro por título...")
        self.search_book_input.returnPressed.connect(self._buscar_libros)

        btn_search = QPushButton("Buscar libro")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._buscar_libros)

        left.addWidget(self.search_book_input)
        left.addWidget(btn_search)

        self.search_results = QListWidget()
        self.search_results.itemSelectionChanged.connect(self._on_book_selected)
        left.addWidget(self.search_results, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        self.detail_container = QFrame()
        self.detail_container.setObjectName("card")
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setAlignment(Qt.AlignTop)
        self.detail_layout.setSpacing(8)

        self.detail_placeholder = QLabel("Selecciona un libro para ver los detalles")
        self.detail_placeholder.setAlignment(Qt.AlignCenter)
        self.detail_placeholder.setStyleSheet("""
            font-size: 16px;
            color: #777;
            font-weight: 500;
        """)

        placeholder_layout = QVBoxLayout()
        placeholder_layout.addStretch()
        placeholder_layout.addWidget(self.detail_placeholder, alignment=Qt.AlignCenter)
        placeholder_layout.addStretch()

        self.detail_placeholder_container = QWidget()
        self.detail_placeholder_container.setLayout(placeholder_layout)

        self.detail_layout.addWidget(self.detail_placeholder_container)

        right.addWidget(self.detail_container, 1)

        self.btn_copy_msg = QPushButton("Copiar mensaje")
        self.btn_copy_msg.setObjectName("primaryBtn")
        
        self.btn_copy_msg.setEnabled(False)
        self.btn_copy_msg.clicked.connect(self._copiar_mensaje)
        right.addWidget(self.btn_copy_msg, alignment=Qt.AlignRight)

        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 2)
        self.tabs.addTab(tab, "Libros")

    def _buscar_libros(self):
        q = self.search_book_input.text().strip()
        if not q:
            QMessageBox.warning(self, "Atención", "Debe ingresar el título del libro.")
            return

        r = http_get(API_URL_BOOKS, {"title": q})
        if r is None or r.status_code != 200:
            QMessageBox.critical(self, "Error", "No se pudo conectar con la API.")
            return

        data = r.json()
        self._search_cache = {}

        self.search_results.blockSignals(True)
        self.search_results.clear()

        if not data:
            self.search_results.addItem("No se encontraron coincidencias.")
            self.search_results.blockSignals(False)
            return

        for b in data:
            card = QWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)

            title = QLabel(b['title'])
            title.setStyleSheet("font-weight: 600; font-size: 16px; color: #1c1c1c;")
            author = QLabel(b['author'])

            card_layout.addWidget(title)
            card_layout.addWidget(author)

            list_item = QListWidgetItem(self.search_results)
            list_item.setSizeHint(card.sizeHint())
            self.search_results.addItem(list_item)
            self.search_results.setItemWidget(list_item, card)
            list_item.book_data = b

        self.search_results.blockSignals(False)

        self._show_placeholder()
        self.btn_copy_msg.setEnabled(False)



    def _on_book_selected(self):
        items = self.search_results.selectedItems()
        if not items:
            self.btn_copy_msg.setEnabled(False)
            self._show_placeholder()
            return

        item = items[0]
        if not hasattr(item, "book_data"):
            return

        book = item.book_data
        self.selected_book = book
        self._show_book_details(book)
        self.btn_copy_msg.setEnabled(True)

    def _show_placeholder(self):
        for i in reversed(range(self.detail_layout.count())):
            widget = self.detail_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if not hasattr(self, "detail_placeholder_container") or self.detail_placeholder_container is None:
            self._recreate_placeholder()
        else:
            try:

                _ = self.detail_placeholder_container.layout()
            except RuntimeError:
                self._recreate_placeholder()

        self.detail_layout.addWidget(self.detail_placeholder_container)



    def _recreate_placeholder(self):
        self.detail_placeholder = QLabel("Selecciona un libro para ver los detalles")
        self.detail_placeholder.setAlignment(Qt.AlignCenter)
        self.detail_placeholder.setStyleSheet("""
            font-size: 16px;
            color: #777;
            font-weight: 500;
        """)

        placeholder_layout = QVBoxLayout()
        placeholder_layout.addStretch()
        placeholder_layout.addWidget(self.detail_placeholder, alignment=Qt.AlignCenter)
        placeholder_layout.addStretch()

        self.detail_placeholder_container = QWidget()
        self.detail_placeholder_container.setLayout(placeholder_layout)




    def _show_book_details(self, book):
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


        card = QFrame()
        card.setObjectName("detailCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel(book['title'])
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #111;")
        card_layout.addWidget(title)

        author = QLabel(f"Autor: {book['author']}")
        author.setStyleSheet("font-size: 15px; color: #333; margin-bottom: 4px;")
        card_layout.addWidget(author)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #ccc; margin-top: 5px; margin-bottom: 5px;")
        card_layout.addWidget(line)

        info_layout = QFormLayout()
        info_layout.setLabelAlignment(Qt.AlignLeft)
        info_layout.setFormAlignment(Qt.AlignTop)

        info_layout.addRow("Páginas:", QLabel(str(book.get('number_pages', '-'))))
        info_layout.addRow("Formato de impresión:", QLabel(book.get('printing_format', '-')))
        info_layout.addRow("Páginas a color:", QLabel(str(book.get('color_pages', 0))))

        for i in range(info_layout.rowCount()):
            field = info_layout.itemAt(i, QFormLayout.FieldRole).widget()
            if field:
                field.setStyleSheet("color: #444; font-size: 14px;")

        card_layout.addLayout(info_layout)

        card_layout.addSpacing(8)

        precios_label = QLabel("Tipos de carátulas")
        precios_label.setStyleSheet("font-size: 17px; font-weight: 600; color: #111; margin-top: 10px;")
        card_layout.addWidget(precios_label)

        precios = self._calcular_precios(book)

        precios_frame = QFrame()
        precios_layout = QVBoxLayout(precios_frame)
        precios_layout.setContentsMargins(10, 5, 10, 5)
        precios_layout.setSpacing(5)

        for p in precios:
            lbl = QLabel(p)
            lbl.setStyleSheet("""
                font-size: 14px;
                color: #333;
                background: #f7f7f7;
                border-radius: 6px;
                padding: 6px 8px;
            """)
            precios_layout.addWidget(lbl)

        card_layout.addWidget(precios_frame)

        aditivos_label = QLabel("Selecciona un aditivo para incluir en el precio:")
        aditivos_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #111; margin-top: 15px;")
        card_layout.addWidget(aditivos_label)

        self.aditivo_combo = MultiSelectComboBox()

        r = http_get(API_URL_ADITIVOS)
        if r and r.status_code == 200:
            aditivos = r.json()
            for a in aditivos:
                self.aditivo_combo.add_checkable_item(f"{a['name']} (+${a['price']})", a)
        else:
            self.aditivo_combo.add_checkable_item("No se pudieron cargar aditivos", None)

        card_layout.addWidget(self.aditivo_combo)

        self.detail_layout.addWidget(card)

    def _calcular_precios(self, book):
        precios = []
        number_of_pages = book.get("number_pages", 0)
        color_pages = book.get("color_pages", 0)
        printing_format = book.get("printing_format", "NORMAL")
        precio_regular = calculate_price(number_of_pages, color_pages, printing_format, costs)
        cup_price = convert_to_currency(precio_regular, 'USD', 'CUP')
        mlc_price = convert_to_currency(precio_regular, 'USD', 'MLC')
        precios.append(f"Regular: {precio_regular} USD | {cup_price} CUP | {mlc_price} MLC")

        r = http_get(API_URL_ADITIVOS)
        if r and r.status_code == 200:
            aditivos = r.json()
            car_dura = next((a for a in aditivos if a["name"].lower() == "carátula dura"), None)
            solapa = next((a for a in aditivos if a["name"].lower() == "solapa"), None)

            if car_dura:
                cup_price = convert_to_currency(precio_regular + car_dura['price'], 'USD', 'CUP')
                mlc_price = convert_to_currency(precio_regular + car_dura['price'], 'USD', 'MLC')
                precios.append(f"Carátula Dura: {precio_regular + car_dura['price']} USD | {cup_price} CUP | {mlc_price} MLC")
            if solapa:
                cup_price = convert_to_currency(precio_regular + solapa['price'], 'USD', 'CUP')
                mlc_price = convert_to_currency(precio_regular + solapa['price'], 'USD', 'MLC')
                precios.append(f"Solapa: {precio_regular + solapa['price']} USD | {cup_price} CUP | {mlc_price} MLC")

        return precios

    def _copiar_mensaje(self):
        if not hasattr(self, "selected_book"):
            return

        b = self.selected_book
        precios = self._calcular_precios(b)

        aditivos_seleccionados = []
        if hasattr(self, "aditivo_combo"):
            aditivos_seleccionados = self.aditivo_combo.selected_items() #or []

        precio_base = b.get("number_pages", 0)
        total_final = precio_base + sum(a["price"] for a in aditivos_seleccionados if a)


        if aditivos_seleccionados:
            aditivos_txt = "\n".join([f"  • ➕{a['name']} (+${a['price']})" for a in aditivos_seleccionados])
        else:
            aditivos_txt = ""

        msg = f"📚 Título: {b['title']} | 👤 Autor: {b['author']} | 📑 Páginas: {b['number_pages']}\n\n"
        msg += "Tipos de portadas:\n" + "\n".join(precios)

        if aditivos_txt != "": 
            msg += f"\n\nServicios adicionales:\n{aditivos_txt}"
            #msg += f"\n💰 Total final: ${total_final}"

        clipboard = QApplication.clipboard()
        clipboard.setText(msg)
        QMessageBox.information(self, "Copiado", "Mensaje copiado al portapapeles.")


#? -------------------------------
#? Mensajerías
#? -------------------------------
    def _build_mensajerias_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignTop)

        self.search_zone = QLineEdit()
        self.search_zone.setPlaceholderText("Buscar mensajería por zona...")
        self.search_zone.returnPressed.connect(self._consultar_mensajeria)

        btn_search = QPushButton("Buscar mensajería")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._consultar_mensajeria)

        left.addWidget(self.search_zone)
        left.addWidget(btn_search)

        self.result_mensajeria = QListWidget()
        self.result_mensajeria.itemSelectionChanged.connect(self._on_mensajeria_selected)
        left.addWidget(self.result_mensajeria, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        self.mensajeria_detail = QFrame()
        self.mensajeria_detail.setObjectName("card")
        self.mensajeria_detail_layout = QVBoxLayout(self.mensajeria_detail)
        self.mensajeria_detail_layout.setAlignment(Qt.AlignTop)
        self.mensajeria_detail_layout.setSpacing(12)

        self.mensajeria_placeholder = QLabel("Selecciona una zona para ver los detalles")
        self.mensajeria_placeholder.setAlignment(Qt.AlignCenter)
        self.mensajeria_placeholder.setStyleSheet("""
            font-size: 16px;
            color: #777;
            font-weight: 500;
        """)
        self.mensajeria_detail_layout.addWidget(self.mensajeria_placeholder)

        right.addWidget(self.mensajeria_detail, 1)

        buttons_main_layout = QVBoxLayout()
        buttons_main_layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.btn_copy_one = QPushButton("Copiar mensajería seleccionada")
        self.btn_copy_one.setObjectName("primaryBtn")
        self.btn_copy_one.setEnabled(False)
        self.btn_copy_one.clicked.connect(self._copiar_mensajeria)
        top_row.addWidget(self.btn_copy_one)
        buttons_main_layout.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.btn_copy_group = QPushButton("Copiar mensajerías del municipio")
        self.btn_copy_group.setObjectName("primaryBtn")
        self.btn_copy_group.setEnabled(False)
        self.btn_copy_group.clicked.connect(self._copiar_mensajerias_municipio)

        self.btn_copy_all = QPushButton("Copiar todas las mensajerías")
        self.btn_copy_all.setObjectName("primaryBtn")
        self.btn_copy_all.setEnabled(True)
        self.btn_copy_all.clicked.connect(self._copiar_todas_mensajerias)

        bottom_row.addWidget(self.btn_copy_group)
        bottom_row.addWidget(self.btn_copy_all)

        buttons_main_layout.addLayout(bottom_row)
        right.addLayout(buttons_main_layout)


        main_layout.addLayout(left, 1) 
        main_layout.addLayout(right, 2) 
        self.tabs.addTab(tab, "Mensajerías")



    def _consultar_mensajeria(self):
        zone = self.search_zone.text().strip()
        params = {"zone": zone} if zone else {}

        r = http_get(API_URL_MENSAJERIAS, params)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo conectar con la API.")
            return

        data = r.json()
        self.result_mensajeria.clear()
        self._mensajerias_data = data
        self.btn_copy_all.setEnabled(bool(data))

        if not data:
            self.result_mensajeria.addItem("No se encontraron mensajerías para la búsqueda.")
            return

        for d in data:
            card = QWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 6, 10, 6)
            card_layout.setSpacing(3)

            title = QLabel(f"{d['zone']} — ${d['price']}")
            title.setStyleSheet("font-weight: 600; font-size: 16px; color: #1c1c1c;")

            desc = QLabel(d['description'])
            desc.setStyleSheet("color: #555; font-size: 13px;")
            desc.setWordWrap(True)

            card_layout.addWidget(title)
            card_layout.addWidget(desc)

            item = QListWidgetItem(self.result_mensajeria)
            item.setSizeHint(card.sizeHint())
            self.result_mensajeria.addItem(item)
            self.result_mensajeria.setItemWidget(item, card)
            item.mensajeria_data = d


    def _on_mensajeria_selected(self):
        items = self.result_mensajeria.selectedItems()
        if not items:
            self._show_mensajeria_placeholder()
            self.btn_copy_one.setEnabled(False)
            self.btn_copy_group.setEnabled(False)
            return

        item = items[0]
        if not hasattr(item, "mensajeria_data"):
            return

        d = item.mensajeria_data
        self.btn_copy_one.setEnabled(True)
        self.btn_copy_group.setEnabled(True)
        self._show_mensajeria_detail(d)



    def _show_mensajeria_placeholder(self):
        for i in reversed(range(self.mensajeria_detail_layout.count())):
            widget = self.mensajeria_detail_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        placeholder = QLabel("Selecciona una zona para ver los detalles")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            font-size: 16px;
            color: #777;
            font-weight: 500;
        """)
        self.mensajeria_detail_layout.addWidget(placeholder)



    def _show_mensajeria_detail(self, d):
        while self.mensajeria_detail_layout.count():
            item = self.mensajeria_detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        card = QFrame()
        card.setObjectName("detailCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        zone_lbl = QLabel(f"Municipio: {d['zone']}")
        zone_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #111;")

        price_lbl = QLabel(f"Precio: ${d['price']}")
        price_lbl.setStyleSheet("font-size: 17px; font-weight: 600;")

        desc_title = QLabel("Descripción:")
        desc_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #111;")

        desc_lbl = QLabel(d['description'])
        desc_lbl.setStyleSheet("""
            font-size: 14px;
            color: #444;
            background: #f9f9f9;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 6px;
        """)
        desc_lbl.setWordWrap(True)

        layout.addWidget(zone_lbl)
        layout.addWidget(price_lbl)
        layout.addWidget(desc_title)
        layout.addWidget(desc_lbl)

        self.mensajeria_detail_layout.addWidget(card)



    def _copiar_mensajeria(self):
        items = self.result_mensajeria.selectedItems()
        if not items or not hasattr(items[0], "mensajeria_data"):
            return

        d = items[0].mensajeria_data
        msg = f"📍 Municipio: {d['zone']}\n📝 {d['description']}\nPrecio: ${d['price']}"

        QApplication.clipboard().setText(msg)
        QMessageBox.information(self, "Copiado", f"Mensajería de zona '{d['zone']}' copiada al portapapeles.")


    def _copiar_todas_mensajerias(self):
        r = http_get(API_URL_MENSAJERIAS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo conectar con la API.")
            return

        data = r.json()
        if not data:
            QMessageBox.warning(self, "Atención", "No hay mensajerías registradas en la base de datos.")
            return

        data = [d for d in data if d["zone"].strip().lower() != "recogida"]

        if not data:
            QMessageBox.warning(self, "Atención", "No hay mensajerías válidas para copiar (todas eran 'Recogida').")
            return

        msgs = [
            f"📍 Municipio: {d['zone']}\n📝 {d['description']}\nPrecio: ${d['price']}"
            for d in data
        ]

        QApplication.clipboard().setText("\n\n".join(msgs))
        QMessageBox.information(
            self,
            "Copiado",
            f"Se copiaron {len(data)} mensajerías desde la base de datos al portapapeles."
        )



    def _copiar_mensajerias_municipio(self):
        if hasattr(self, "result_mensajeria"):
            items = self.result_mensajeria.selectedItems()
        else:
            items = []

        base = None

        if items and hasattr(items[0], "mensajeria_data"):
            d = items[0].mensajeria_data
            zone_name = d["zone"]
            import re
            match = re.match(r"([A-Za-záéíóúÁÉÍÓÚñÑ]+)", zone_name)
            if match:
                base = match.group(1).strip()

        if not base:
            zone_text = self.search_zone.text().strip()
            if zone_text:
                import re
                match = re.match(r"([A-Za-záéíóúÁÉÍÓÚñÑ]+)", zone_text)
                if match:
                    base = match.group(1).strip()

        if not base:
            QMessageBox.warning(self, "Atención", "Selecciona una mensajería o escribe una zona en la búsqueda.")
            return

        if not hasattr(self, "_mensajerias_data") or not self._mensajerias_data:
            QMessageBox.warning(self, "Atención", "No hay mensajerías cargadas para copiar.")
            return

        municipios = [
            x for x in self._mensajerias_data
            if x["zone"].lower().startswith(base.lower()) and x["zone"].strip().lower() != "recogida"
        ]

        if not municipios:
            QMessageBox.warning(self, "Atención", f"No se encontraron zonas válidas que comiencen con '{base}'.")
            return

        msgs = [
            f"📍 Municipio: {x['zone']}\n📝 {x['description']}\nPrecio: ${x['price']}"
            for x in municipios
        ]

        QApplication.clipboard().setText("\n\n".join(msgs))
        QMessageBox.information(
            self,
            "Copiado",
            f"Todas las mensajerías del municipio '{base}' fueron copiadas al portapapeles."
        )


#? -------------------------------  
#? Aditivos  
#? -------------------------------  
    def _build_aditivos_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignTop)

        self.search_aditivo = QLineEdit()
        self.search_aditivo.setPlaceholderText("Buscar aditivo por nombre...")
        self.search_aditivo.returnPressed.connect(self._consultar_aditivo)

        btn_search = QPushButton("Buscar aditivo")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._consultar_aditivo)

        left.addWidget(self.search_aditivo)
        left.addWidget(btn_search)

        self.result_aditivo = QListWidget()
        self.result_aditivo.itemSelectionChanged.connect(self._on_aditivo_selected)
        left.addWidget(self.result_aditivo, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        self.aditivo_detail = QFrame()
        self.aditivo_detail.setObjectName("card")
        self.aditivo_detail_layout = QVBoxLayout(self.aditivo_detail)
        self.aditivo_detail_layout.setAlignment(Qt.AlignTop)
        self.aditivo_detail_layout.setSpacing(12)

        self.aditivo_placeholder = QLabel("Selecciona un aditivo para ver los detalles")
        self.aditivo_placeholder.setAlignment(Qt.AlignCenter)
        self.aditivo_placeholder.setStyleSheet("""
            font-size: 16px;
            color: #777;
            font-weight: 500;
        """)
        self.aditivo_detail_layout.addWidget(self.aditivo_placeholder)

        right.addWidget(self.aditivo_detail, 1)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.btn_copy_one_aditivo = QPushButton("Copiar aditivo seleccionado")
        self.btn_copy_one_aditivo.setObjectName("primaryBtn")
        self.btn_copy_one_aditivo.setEnabled(False)
        self.btn_copy_one_aditivo.clicked.connect(self._copiar_aditivo)

        self.btn_copy_all_aditivos = QPushButton("Copiar todos los aditivos")
        self.btn_copy_all_aditivos.setObjectName("primaryBtn")
        self.btn_copy_all_aditivos.setEnabled(True)
        self.btn_copy_all_aditivos.clicked.connect(self._copiar_todos_aditivos)

        buttons_layout.addWidget(self.btn_copy_one_aditivo)
        buttons_layout.addWidget(self.btn_copy_all_aditivos)

        right.addLayout(buttons_layout)


        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 2)
        self.tabs.addTab(tab, "Aditivos")


    def _consultar_aditivo(self):
        name = self.search_aditivo.text().strip()
        params = {"name": name} if name else {}

        r = http_get(API_URL_ADITIVOS, params)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo conectar con la API.")
            return

        data = r.json()
        self.result_aditivo.clear()
        self._aditivos_data = data
        self.btn_copy_all_aditivos.setEnabled(bool(data))

        if not data:
            self.result_aditivo.addItem("No se encontraron aditivos para la búsqueda.")
            return

        for a in data:
            card = QWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 6, 10, 6)
            card_layout.setSpacing(3)

            title = QLabel(f"{a['name']} — ${a['price']}")
            title.setStyleSheet("font-weight: 600; font-size: 16px; color: #1c1c1c;")

            card_layout.addWidget(title)

            item = QListWidgetItem(self.result_aditivo)
            item.setSizeHint(card.sizeHint())
            self.result_aditivo.addItem(item)
            self.result_aditivo.setItemWidget(item, card)
            item.aditivo_data = a


    def _on_aditivo_selected(self):
        items = self.result_aditivo.selectedItems()
        if not items:
            self._show_aditivo_placeholder()
            self.btn_copy_one_aditivo.setEnabled(False)
            return

        item = items[0]
        if not hasattr(item, "aditivo_data"):
            return

        d = item.aditivo_data
        self.btn_copy_one_aditivo.setEnabled(True)
        self._show_aditivo_detail(d)


    def _show_aditivo_placeholder(self):
        for i in reversed(range(self.aditivo_detail_layout.count())):
            widget = self.aditivo_detail_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        placeholder = QLabel("Selecciona un aditivo para ver los detalles")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            font-size: 16px;
            color: #777;
            font-weight: 500;
        """)
        self.aditivo_detail_layout.addWidget(placeholder)


    def _show_aditivo_detail(self, d):
        while self.aditivo_detail_layout.count():
            item = self.aditivo_detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        card = QFrame()
        card.setObjectName("detailCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        name_lbl = QLabel(d['name'])
        name_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #111;")

        cup_price = convert_to_currency(d['price'], 'USD', 'CUP')
        mlc_price = convert_to_currency(d['price'], 'USD', 'MLC')

        price_lbl = QLabel(f"Precio: {d['price']} USD | {cup_price} CUP | {mlc_price} MLC")
        price_lbl.setStyleSheet("font-size: 17px; font-weight: 600;")



        layout.addWidget(name_lbl)
        layout.addWidget(price_lbl)

        self.aditivo_detail_layout.addWidget(card)


    def _copiar_aditivo(self):
        items = self.result_aditivo.selectedItems()
        if not items or not hasattr(items[0], "aditivo_data"):
            return

        d = items[0].aditivo_data

        cup_price = convert_to_currency(d['price'], 'USD', 'CUP')
        mlc_price = convert_to_currency(d['price'], 'USD', 'MLC')

        msg = f"💰 {d['name']}\nPrecio: {d['price']} USD | {cup_price} CUP | {mlc_price} MLC"
    
        QApplication.clipboard().setText(msg)
        QMessageBox.information(self, "Copiado", f"Aditivo '{d['name']}' copiado al portapapeles.")



    def _copiar_todos_aditivos(self):
        r = http_get(API_URL_ADITIVOS)
        if r is None or r.status_code != 200:
            QMessageBox.warning(self, "Error", "No se pudo conectar con la API.")
            return

        data = r.json()
        if not data:
            QMessageBox.warning(self, "Atención", "No hay aditivos registrados en la base de datos.")
            return

        msgs = [
            f"💰 {a['name']}\nPrecio: {a['price']} USD | {convert_to_currency(a['price'], 'USD', 'CUP')} CUP | {convert_to_currency(a['price'], 'USD', 'MLC')} MLC" for a in data]

        QApplication.clipboard().setText("\n\n".join(msgs))
        QMessageBox.information(
            self,
            "Copiado",
            f"Se copiaron {len(data)} aditivos desde la base de datos al portapapeles."
        )




    
#* ------------------- STYLE -------------------
    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget#booksPage {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f8f8, stop:1 #e0e0e0);
            }

            QFrame#card {
                background: #fff;
                border-radius: 10px;
                padding: 15px;
            }

            QLineEdit, QSpinBox {
                background: #fafafa;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 8px;
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
                padding-top: 11px;   /* Simula el “hundido” */
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
                min-height: 5px;
            }

            QComboBox:hover {
                border: 1px solid #888;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ccc;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background: #eee;
            }

            QComboBox::down-arrow {
                image: url(icons/arrow.png);
                width: 15px;
                height: 15px;
            }
            QFrame#detailCard {
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 12px;
                padding: 12px;
            }

            QFrame#detailCard:hover {
                border: 1px solid #bbb;
            }

        """)

