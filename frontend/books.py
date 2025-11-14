import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QListWidget, QMessageBox, QFormLayout, QSpinBox, QFrame, QComboBox,
    QListWidgetItem
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from difflib import SequenceMatcher
import unicodedata
from frontend.urls import API_URL_BOOKS
from frontend.utils import http_get, http_post, http_patch, http_delete, make_icon_label


SIMILARITY_THRESHOLD = 0.7


def normalize_text(text):
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return text.lower()

#* Item de libro para búsqueda
class BookResultItem(QWidget):
    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.book = book
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("bookResultCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        title_label = QLabel(f"📘 {self.book['title']}")
        title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        author_label = QLabel(f"✍️ {self.book['author']}")
        pages_label = QLabel(f"📄 {self.book.get('number_pages', '-') } páginas")
        format_label = QLabel(f"🖨 {self.book.get('printing_format', '-') }")
        color_pages_label = QLabel(f"🌈 {self.book.get('color_pages', 0)} a color")

        for lbl in [title_label, author_label, pages_label, format_label, color_pages_label]:
            info_layout.addWidget(lbl)

        layout.addLayout(info_layout)
        layout.addStretch()

        self.setStyleSheet("""
            QWidget#bookResultCard {
                background: #fff;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 8px;
            }
            QWidget#bookResultCard:hover {
                border: 1px solid #666;
                background: #f4f4f4;
            }
        """)

#* Item de libro para eliminación
class DeleteBookResultItem(QWidget):
    def __init__(self, book):
        super().__init__()
        self.book = book
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("deleteBookCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)

        title_label = QLabel(self.book['title'])
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1c1c1c;
        """)

        author_label = QLabel(f"Autor: {self.book['author']}")
        author_label.setStyleSheet("font-size: 13px; color: #555;")

        layout.addWidget(title_label)
        layout.addWidget(author_label)

        self.setStyleSheet("""
            QWidget#deleteBookCard {
                background: #ffffff;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 10px;
                padding: 1px;

            }
            QWidget#deleteBookCard:hover {
                background: #f9f9f9;
                border: 1px solid rgba(0,0,0,0.25);
            }
        """)

#* Item de libro para listado
class ViewBookCard(QWidget):
    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.book = book
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("viewBookResultCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)

        title_label = QLabel(self.book['title'])
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1c1c1c;")

        author_label = QLabel(f"Autor: {self.book['author']}")
        author_label.setStyleSheet("font-size: 13px; color: #555;")

        layout.addWidget(title_label)
        layout.addWidget(author_label)
        self.setStyleSheet("""
            QWidget#viewBookCard {
                background: #ffffff;
                border-radius: 10px;
                border: 1px solid rgba(0,0,0,0.1);
            }
            QWidget#viewBookCard:hover {
                background: #f7f7f7;
                border: 1px solid rgba(0,0,0,0.25);
            }
        """)

class BooksPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_cache = {}
        self.setObjectName("booksPage")
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap("frontend/icons/book.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Manejo de libros")
        title.setStyleSheet("font-size: 35px; font-weight: 700; color: #222;")
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._init_insert_tab()
        self._init_update_tab()
        self._init_delete_tab()
        self._init_view_tab()

#* ------------------- INSERT -------------------
    def _init_insert_tab(self):
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

        self.insert_title = QLineEdit()
        self.insert_author = QLineEdit()
        self.insert_pages = QSpinBox()
        self.insert_pages.setRange(1, 100000)
        self.insert_format = QComboBox()
        self.insert_format.addItems(["Normal", "Grande"])
        self.insert_color_pages = QSpinBox()
        self.insert_color_pages.setRange(0, 100000)

        inner_form.addRow(make_icon_label("frontend/icons/title.png", "Título"), self.insert_title)
        inner_form.addRow(make_icon_label("frontend/icons/autor.png", "Autor"), self.insert_author)
        inner_form.addRow(make_icon_label("frontend/icons/cant_pag.png", "Número de páginas"), self.insert_pages)
        inner_form.addRow(make_icon_label("frontend/icons/format.png", "Formato de impresión"), self.insert_format)
        inner_form.addRow(make_icon_label("frontend/icons/cant-pag-col.png", "Cantidad de páginas a color"), self.insert_color_pages)

        form_layout.addWidget(form_card)
        spacer = QWidget()
        spacer.setFixedHeight(10)
        form_layout.addWidget(spacer)

        btn = QPushButton("Insertar libro")
        btn.clicked.connect(self._on_insert)
        btn.setObjectName("primaryBtn")
        form_layout.addWidget(btn, alignment=Qt.AlignHCenter)

        self.insert_title.returnPressed.connect(self._on_insert)
        self.insert_author.returnPressed.connect(self._on_insert)

        main_layout.addWidget(form_block, alignment=Qt.AlignTop)

        self.tabs.addTab(tab, "Añadir")


    def _on_insert(self):
        title = self.insert_title.text().strip()
        author = self.insert_author.text().strip()
        pages = self.insert_pages.value()
        format_ = self.insert_format.currentText()
        color_pages = self.insert_color_pages.value()

        if not title or not author or not format_:
            QMessageBox.warning(self, "Validación", "Título, Autor y Formato de impresión son obligatorios.")
            return

        r = http_get(API_URL_BOOKS)
        similar_books = []
        if r and r.status_code == 200:
            norm_title = normalize_text(title)
            all_books = r.json()
            for b in all_books:
                existing_title = normalize_text(b["title"])
                similarity = SequenceMatcher(None, norm_title, existing_title).ratio()
                if similarity >= SIMILARITY_THRESHOLD:
                    similar_books.append(b)


        if similar_books:
            msg_text = "⚠️ Se han encontrado libros con títulos similares:\n\n"
            for b in similar_books:
                msg_text += f"📘 {b['title']} — ✍️ {b['author']}\n"
            msg_text += "\n¿Deseas insertar el nuevo libro de todas formas?"
            reply = QMessageBox.question(self, "Títulos similares encontrados", msg_text,
                                        QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        payload = {
            "title": title,
            "author": author,
            "number_pages": pages,
            "printing_format": format_,
            "color_pages": color_pages,
        }

        r = http_post(API_URL_BOOKS, payload)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al contactar la API.")
            return
        if r.status_code in (200, 201):
            QMessageBox.information(
                self,
                "📚 Libro agregado",
                f"Se ha agregado el libro:\n\n"
                f"📘 Título: {title}\n✍️ Autor: {author}\n📄 Páginas: {pages}\n"
                f"🖨 Formato: {format_}\n🌈 Páginas a color: {color_pages}"
            )
            self.insert_title.clear()
            self.insert_author.clear()
            self.insert_pages.setValue(1)
            self.insert_format.setCurrentIndex(0)
            self.insert_color_pages.setValue(0)
        else:
            QMessageBox.warning(self, "Falló la inserción", f"Insert failed: {r.status_code}\n{r.text}")


#* ------------------- UPDATE -------------------
    def _init_update_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignTop)

        self.search_update_input = QLineEdit()
        self.search_update_input.setPlaceholderText("Buscar por título")
        self.search_update_input.returnPressed.connect(self._search_for_update)

        btn_search = QPushButton("Buscar libro")
        btn_search.setObjectName("primaryBtn")
        btn_search.clicked.connect(self._search_for_update)

        left.addWidget(self.search_update_input)
        left.addWidget(btn_search)

        self.search_update_results = QListWidget()
        self.search_update_results.itemSelectionChanged.connect(self._on_update_selection)
        left.addWidget(self.search_update_results, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignTop)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QFormLayout(form_card)
        form_layout.setSpacing(12)

        self.update_title = QLineEdit()
        self.update_author = QLineEdit()
        self.update_pages = QSpinBox()
        self.update_pages.setRange(1, 100000)
        self.update_format = QComboBox()
        self.update_format.addItems(["Normal", "Grande"])
        self.update_color_pages = QSpinBox()
        self.update_color_pages.setRange(0, 100000)

        form_layout.addRow(make_icon_label("frontend/icons/title.png", "Título"), self.update_title)
        form_layout.addRow(make_icon_label("frontend/icons/autor.png", "Autor"), self.update_author)
        form_layout.addRow(make_icon_label("frontend/icons/cant_pag.png", "Número de páginas"), self.update_pages)
        form_layout.addRow(make_icon_label("frontend/icons/format.png", "Formato de impresión"), self.update_format)
        form_layout.addRow(make_icon_label("frontend/icons/cant-pag-col.png", "Cantidad de páginas a color"), self.update_color_pages)

        self.btn_update = QPushButton("Aplicar cambios")
        self.btn_update.setObjectName("primaryBtn")
        self.btn_update.clicked.connect(self._apply_update)
        self.btn_update.setEnabled(False)
        form_layout.addRow(QWidget(), self.btn_update)
        right.addWidget(form_card)

        layout.addLayout(left, 2)
        layout.addLayout(right, 2)

        self.tabs.addTab(tab, "Modificar")


    def _search_for_update(self):
        q = self.search_update_input.text().strip()
        if not q:
            QMessageBox.information(self, "Input", "Escribe un título para buscar.")
            self.search_update_results.clear()
            return

        r = http_get(API_URL_BOOKS)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        all_books = r.json()
        q_norm = normalize_text(q)

        data = [
            b for b in all_books
            if q_norm in normalize_text(b["title"]) or q_norm in normalize_text(b["author"])
        ]

        self.search_update_results.clear()
        self._search_cache = {}

        if not data:
            self.search_update_results.addItem("No se encontraron resultados")
            return

        for b in data:
            item_widget = BookResultItem(b)
            list_item = QListWidgetItem(self.search_update_results)
            list_item.setSizeHint(item_widget.sizeHint())
            self.search_update_results.addItem(list_item)
            self.search_update_results.setItemWidget(list_item, item_widget)
            list_item.book_data = b


    def _on_update_selection(self):
        items = self.search_update_results.selectedItems()
        if not items:
            self.btn_update.setEnabled(False)
            return

        list_item = items[0]
        widget = self.search_update_results.itemWidget(list_item)
        if widget is None or not hasattr(list_item, "book_data"):
            self.btn_update.setEnabled(False)
            return

        book = list_item.book_data
        self.selected_update_id = book["idBook"]

        self.update_title.setText(book.get("title", ""))
        self.update_author.setText(book.get("author", ""))
        self.update_pages.setValue(book.get("number_pages", 1))
        self.update_format.setCurrentText(book.get("printing_format", "normal"))
        self.update_color_pages.setValue(book.get("color_pages", 0))

        self.btn_update.setEnabled(True)


    def _apply_update(self):
        payload = {
            "title": self.update_title.text().strip(),
            "author": self.update_author.text().strip(),
            "number_pages": self.update_pages.value(),
            "printing_format": self.update_format.currentText().strip(),
            "color_pages": self.update_color_pages.value(),
        }
        r = http_patch(f"{API_URL_BOOKS}{self.selected_update_id}/", payload)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red.")
            return
        if r.status_code in (200, 204):
            QMessageBox.information(self, "Actualizado", "Libro actualizado correctamente.")
            self._search_for_update()
        else:
            QMessageBox.warning(self, "Fallo", f"Falló la actualización: {r.status_code}\n{r.text}")

#* ------------------- DELETE -------------------
    def _init_delete_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        left = QVBoxLayout()
        self.search_delete_input = QLineEdit()
        self.search_delete_input.setPlaceholderText("Buscar por título o autor")
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
        icon_pix = QPixmap("frontend/icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pix)
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Seleccione un libro para ver los detalles.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon_label)
        ph_layout.addWidget(text_label)

        self.delete_info_layout.addWidget(self.delete_placeholder)

        right.addWidget(self.delete_info_container, 1)

        self.btn_delete = QPushButton("Eliminar libro seleccionado")
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
            QMessageBox.information(self, "Input", "Escribe un título para buscar.")
            self.search_delete_results.clear()
            return

        r = http_get(API_URL_BOOKS)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        all_books = r.json()
        q_norm = normalize_text(q)
        data = [
            b for b in all_books
            if q_norm in normalize_text(b["title"]) or q_norm in normalize_text(b["author"])
        ]

        self.search_delete_results.clear()
        self._delete_cache = {}

        if not data:
            self.search_delete_results.addItem("(no results)")
            return

        for a in data:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            title = QLabel(a["title"])
            title.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            author = QLabel(f"{a['author']}")
            author.setStyleSheet("font-size: 13px; color: #666;")

            card_layout.addWidget(title)
            card_layout.addStretch()
            card_layout.addWidget(author)

            list_item = QListWidgetItem(self.search_delete_results)
            list_item.setSizeHint(card.sizeHint())
            self.search_delete_results.addItem(list_item)
            self.search_delete_results.setItemWidget(list_item, card)
            self._delete_cache[id(list_item)] = a


    def _on_delete_selection(self):
        items = self.search_delete_results.selectedItems()
        if not items:
            self.btn_delete.setEnabled(False)
            self._clear_delete_info(show_placeholder=True)
            return

        list_item = items[0]
        book = self._delete_cache.get(id(list_item))
        if not book:
            self.btn_delete.setEnabled(False)
            self._clear_delete_info(show_placeholder=True)
            return

        self.selected_delete_id = book["idBook"]
        self.btn_delete.setEnabled(True)

        self._clear_delete_info(show_placeholder=False)

        info_card = QFrame()
        info_card.setObjectName("card")
        form = QFormLayout(info_card)
        form.setSpacing(10)

        form.addRow(make_icon_label("frontend/icons/title.png", f"Título: {book['title']}"))
        form.addRow(make_icon_label("frontend/icons/autor.png", f"Autor: {book['author']}"))
        form.addRow(make_icon_label("frontend/icons/cant_pag.png", f"Número de páginas: {book.get('number_pages', '-')}"))
        form.addRow(make_icon_label("frontend/icons/format.png", f"Formato de impresión: {book.get('printing_format', '-')}"))
        form.addRow(make_icon_label("frontend/icons/cant-pag-col.png", f"Páginas a color: {book.get('color_pages', '-')}"))

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
        icon_pix = QPixmap("frontend/icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pix)
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Seleccione un libro para ver los detalles.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon_label)
        ph_layout.addWidget(text_label)
        self.delete_info_layout.addWidget(self.delete_placeholder)


    def _perform_delete(self):
        items = self.search_delete_results.selectedItems()
        if not items:
            QMessageBox.information(self, "Eliminar libro", "Selecciona un libro para eliminar.")
            return

        list_item = items[0]
        book = self._delete_cache.get(id(list_item))
        if not book:
            QMessageBox.warning(self, "Eliminar libro", "No se pudo obtener la información del libro seleccionado.")
            return

        msg_text = (
            f"¿Estás seguro que quieres eliminar este libro?\n\n"
            f"📘 Título: {book['title']}\n"
            f"✍️ Autor: {book['author']}\n"
            f"📄 Número de páginas: {book.get('number_pages', '-')}\n"
            f"🖨 Formato de impresión: {book.get('printing_format', '-')}\n"
            f"🌈 Páginas a color: {book.get('color_pages', '-')}\n"
        )

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            msg_text,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        r = http_delete(f"{API_URL_BOOKS}{book['idBook']}/")
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red al intentar eliminar el libro.")
            return

        if r.status_code in (200, 204):
            QMessageBox.information(
                self,
                "Libro eliminado",
                f"El libro '{book['title']}' fue eliminado correctamente."
            )
            self._search_for_delete()
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo eliminar el libro.\nCódigo: {r.status_code}\n{r.text}"
            )

#* ------------------- VIEW -------------------

    def _init_view_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(20)

        left = QVBoxLayout()
        left.setSpacing(12)

        search_layout = QVBoxLayout()
        search_layout.setSpacing(8)
        self.search_view_input = QLineEdit()
        self.search_view_input.setPlaceholderText("Buscar por título...")
        self.search_view_input.returnPressed.connect(self._search_for_view)

        self.search_view_input.setClearButtonEnabled(True)

        btn = QPushButton("Buscar")
        btn.setObjectName("primaryBtn")
        btn.clicked.connect(self._search_for_view)

        search_layout.addWidget(self.search_view_input)
        search_layout.addWidget(btn)
        left.addLayout(search_layout)


        self.view_results = QListWidget()
        self.view_results.itemSelectionChanged.connect(self._on_view_selection)
        left.addWidget(self.view_results, 1)

        right = QVBoxLayout()
        right.setSpacing(12)

        self.view_info_container = QWidget()
        self.view_info_container.setObjectName("infoContainer")
        self.view_info_layout = QVBoxLayout(self.view_info_container)
        self.view_info_layout.setAlignment(Qt.AlignCenter)

        self.view_placeholder = QWidget()
        ph_layout = QVBoxLayout(self.view_placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)
        icon = QLabel()
        icon.setPixmap(QPixmap("frontend/icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        text = QLabel("Busca un libro y selecciona uno para ver sus detalles.")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")
        ph_layout.addWidget(icon)
        ph_layout.addWidget(text)
        self.view_info_layout.addWidget(self.view_placeholder)

        right.addWidget(self.view_info_container, 1)

        main_layout.addLayout(left, 2)
        main_layout.addLayout(right, 2)
        self.tabs.addTab(tab, "Información de los libros")


    def _search_for_view(self):
        q = self.search_view_input.text().strip()
        if not q:
            QMessageBox.information(self, "Entrada", "Escribe un título o autor para buscar.")
            self.view_results.clear()
            return

        r = http_get(API_URL_BOOKS)
        if r is None:
            QMessageBox.critical(self, "Error", "Error de red.")
            return
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {r.status_code}")
            return

        all_books = r.json()
        q_norm = normalize_text(q)

        data = [
            b for b in all_books
            if q_norm in normalize_text(b["title"]) or q_norm in normalize_text(b["author"])
        ]

        self.view_results.clear()
        self._view_cache = {}

        if not data:
            self.view_results.addItem("(sin resultados)")
            return

        for a in data:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(8)

            title = QLabel(a["title"])
            title.setStyleSheet("font-size: 14px; font-weight: 600; color: #333;")
            author = QLabel(f"{a['author']}")
            author.setStyleSheet("font-size: 13px; color: #666;")

            card_layout.addWidget(title)
            card_layout.addStretch()
            card_layout.addWidget(author)

            list_item = QListWidgetItem(self.view_results)
            list_item.setSizeHint(card.sizeHint())
            self.view_results.addItem(list_item)
            self.view_results.setItemWidget(list_item, card)
            self._view_cache[id(list_item)] = a

    def _on_view_selection(self):
        items = self.view_results.selectedItems()
        if not items:
            self._clear_view_info(show_placeholder=True)
            return

        list_item = items[0]
        book = self._view_cache.get(id(list_item))
        if not book:
            self._clear_view_info(show_placeholder=True)
            return

        self._clear_view_info(show_placeholder=False)

        info_card = QFrame()
        info_card.setObjectName("card")
        form = QFormLayout(info_card)
        form.setSpacing(10)

        form.addRow(make_icon_label("frontend/icons/title.png", f"Título: {book['title']}"))
        form.addRow(make_icon_label("frontend/icons/autor.png", f"Autor: {book['author']}"))
        form.addRow(make_icon_label("frontend/icons/cant_pag.png", f"Número de páginas: {book.get('number_pages', '-')}"))
        form.addRow(make_icon_label("frontend/icons/format.png", f"Formato de impresión: {book.get('printing_format', '-')}"))
        form.addRow(make_icon_label("frontend/icons/cant-pag-col.png", f"Páginas a color: {book.get('color_pages', '-')}"))

        self.view_info_layout.addWidget(info_card, alignment=Qt.AlignCenter)


    def _clear_view_info(self, show_placeholder=True):
        while self.view_info_layout.count():
            child = self.view_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not show_placeholder:
            return

        self.view_placeholder = QWidget()
        ph_layout = QVBoxLayout(self.view_placeholder)
        ph_layout.setAlignment(Qt.AlignCenter)

        icon = QLabel()
        icon.setPixmap(QPixmap("frontend/icons/select.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        text = QLabel("Busca un libro y selecciona uno para ver sus detalles.")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("font-size: 15px; color: #555; font-weight: 500;")

        ph_layout.addWidget(icon)
        ph_layout.addWidget(text)
        self.view_info_layout.addWidget(self.view_placeholder)

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
            image: url(frontend/icons/arrow.png);
            width: 15px;
            height: 15px;
        }


        """)
