from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFrame, QScrollArea, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QCursor
from utils import http_get
from urls import API_URL_CLIENTES
from datetime import datetime, timedelta


class BirthdayTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_birthday_tab()

    def _setup_birthday_tab(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 35, 40, 35)

        #? ---------------- ENCABEZADO ----------------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        header_icon = QLabel()
        header_icon.setPixmap(
            QPixmap("icons/birthday.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        header_title = QLabel("Cumpleaños del Próximo Mes")
        header_title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
            color: #222;
        """)

        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        #? ---------------- ÁREA DESPLAZABLE ----------------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #f1f1f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #b0b0b0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #8c8c8c;
            }
        """)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(18)
        self.cards_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(scroll_area)

        #? ---------------- BOTÓN ACTUALIZAR ----------------
        refresh_btn = QPushButton("Actualizar lista")
        refresh_btn.setFixedHeight(42)
        refresh_btn.clicked.connect(self._load_birthday_clients)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e2e2e;
                color: #f5f5f5;
                font-weight: 600;
                font-size: 14px;
                padding: 8px 20px;
                border-radius: 6px;
                border: 1px solid #444;
                min-width: 180px;
            }
            QPushButton:hover { background-color: #3a3a3a; }
            QPushButton:pressed { background-color: #1f1f1f; }
        """)
        main_layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)

        self._load_birthday_clients()

    def _load_birthday_clients(self):
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        try:
            response = http_get(API_URL_CLIENTES)
            if not response or response.status_code != 200:
                self._show_no_clients_message("❌ Error al cargar clientes.")
                return

            clients = response.json()
            today = datetime.now()

            birthday_clients = []
            for client in clients:
                identity = client.get('identity', '')
                if len(identity) >= 6:
                    try:
                        c_day = int(identity[4:6])
                        c_month = int(identity[2:4])
                        bday = datetime(year=today.year, month=c_month, day=c_day)
                        if bday < today:
                            bday = datetime(year=today.year + 1, month=c_month, day=c_day)
                        reminder_date = bday - timedelta(days=30)
                        if reminder_date.month == today.month and reminder_date.day == today.day:
                            birthday_clients.append(client)

                    except Exception:
                        continue
            if not birthday_clients:
                self._show_no_clients_message("🎉 No hay cumpleaños próximos.")
                return
            for client in birthday_clients:
                self._create_client_card(client)
        except Exception as e:
            self._show_no_clients_message("Error al cargar cumpleaños.")

    def _show_no_clients_message(self, message):
        label = QLabel(message)
        label.setStyleSheet("""
            font-size: 17px;
            color: #7f8c8d;
            padding: 40px;
        """)
        label.setAlignment(Qt.AlignCenter)
        self.cards_layout.addWidget(label)

    def _create_client_card(self, client):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #fefefe;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #f9f9f9;
                border-color: #bcbcbc;
            }
        """)
        card.setFixedHeight(120)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        #? --- Información del cliente ---
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setSpacing(8)

        name = QLabel(client.get('name', 'Cliente'))
        name.setStyleSheet("""
            font-size: 19px;
            font-weight: 600;
            color: #1c1c1c;
        """)

        #? --- Cumpleaños ---
        birthday_row = QHBoxLayout()
        birthday_row.setSpacing(10)
        birthday_icon = QLabel()
        birthday_icon.setPixmap(QPixmap("icons/upcoming.png").scaled(21, 21, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        identity = client.get('identity', '')
        birthday_text = "—"
        if len(identity) >= 6:
            try:
                c_day = int(identity[4:6])
                c_month = int(identity[2:4])
                birthday_text = f"{c_day:02d}/{c_month:02d}"
            except Exception:
                pass

        birthday_label = QLabel(f"{birthday_text}")
        birthday_label.setStyleSheet("""
            font-size: 14px;
            color: #333;
        """)

        birthday_row.addWidget(birthday_icon)
        birthday_row.addWidget(birthday_label)
        birthday_row.addStretch()

        #? --- Teléfono ---
        phone_row = QHBoxLayout()
        phone_row.setSpacing(10)
        phone_icon = QLabel()
        phone_icon.setPixmap(QPixmap("icons/call.png").scaled(21, 21, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        phone = client.get('phone_number', '—')
        phone_label = QLabel(phone)
        phone_label.setStyleSheet("""
            font-size: 14px;
            color: #0056b3;
            text-decoration: underline;
        """)
        phone_label.setCursor(QCursor(Qt.PointingHandCursor))
        phone_label.mousePressEvent = lambda event: self._copy_phone(phone)

        phone_row.addWidget(phone_icon)
        phone_row.addWidget(phone_label)
        phone_row.addStretch()

        info_layout.addWidget(name)
        info_layout.addLayout(birthday_row)
        info_layout.addLayout(phone_row)

        #? --- Botón de acción ---
        copy_btn = QPushButton("Copiar mensaje")
        copy_btn.setFixedSize(170, 40)
        copy_btn.clicked.connect(lambda: self._copy_birthday_message(client))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #d1d1d1;
                color: #1c1c1c;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #bfbfbf;
            }
            QPushButton:pressed {
                background-color: #a9a9a9;
            }
        """)

        layout.addWidget(info)
        layout.addStretch()
        layout.addWidget(copy_btn)
        self.cards_layout.addWidget(card)

    def _copy_phone(self, phone):
        if phone and phone != "—":
            QApplication.clipboard().setText(phone)
        else:
            QMessageBox.warning(self, "Sin número", "Este cliente no tiene número registrado.")

    def _copy_birthday_message(self, client):
        name = client.get('name', 'Cliente').split()[0]
        message = (
            f"🎉 ¡Hola {name}! 🎂\n\n"
            "¡Falta un mes para tu cumpleaños! 🥰\n"
            "Queremos que llegues a tu día con algo especial hecho para ti 💛\n"
            "Por eso hoy te damos un *10% de descuento exclusivo*🎁\n\n"
            "Así tendrás tu libro listo justo a tiempo para celebrarte 🎈"
        )
        QApplication.clipboard().setText(message)
        QMessageBox.information(
            self,
            "Mensaje copiado",
            f"Mensaje personalizado para {name} copiado al portapapeles."
        )
