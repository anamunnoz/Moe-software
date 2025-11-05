import os
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QProgressBar, QFrame, QComboBox, QCheckBox,
    QScrollArea, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QClipboard
from utils import http_get, http_put
from urls import API_URL_ORDERS, API_URL_CLIENTES
from datetime import datetime 
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
import calendar


class BirthdayTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_birthday_tab()

    def _setup_birthday_tab(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 35, 40, 35)

        # ---------------- ENCABEZADO ----------------
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

        today_label = QLabel(datetime.now().strftime("%d/%m/%Y"))
        today_label.setStyleSheet("""
            font-size: 15px;
            color: #666;
            font-weight: 500;
        """)

        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(today_label)
        main_layout.addLayout(header_layout)

        # ---------------- ÁREA DESPLAZABLE ----------------
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

        # ---------------- BOTÓN ACTUALIZAR ----------------
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
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1f1f1f;
            }
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
            day, month, year = today.day, today.month, today.year

            next_month = month + 1 if month < 12 else 1
            next_year = year + 1 if next_month == 1 else year
            last_day = calendar.monthrange(next_year, next_month)[1]
            valid_day = min(day, last_day)
            print('DIA', valid_day)
            print('MES', next_month)

            birthday_clients = []
            for client in clients:
                identity = client.get('identity', '')
                if len(identity) >= 6:
                    try:
                        c_day = int(identity[4:6])
                        c_month = int(identity[2:4])

                        # --- Mes y año actual ---
                        today = datetime.now()
                        day, month, year = today.day, today.month, today.year

                        # --- Mes siguiente ---
                        next_month = month + 1 if month < 12 else 1
                        next_year = year + 1 if next_month == 1 else year

                        # --- Último día del mes actual y del siguiente ---
                        last_day_current = calendar.monthrange(year, month)[1]
                        last_day_next = calendar.monthrange(next_year, next_month)[1]

                        # --- Día de inicio: el mismo día actual si existe, o el último del próximo mes ---
                        start_day = min(day, last_day_next)

                        # Si el mes cumple con el siguiente mes y el día está desde start_day hasta el último día del mes siguiente
                        next_month = 3
                        start_day = 28
                        if c_month == next_month and c_day >= start_day:
                            birthday_clients.append(client)

                    except Exception:
                        continue


            if not birthday_clients:
                self._show_no_clients_message(
                    f"🎉 No hay cumpleaños el {valid_day:02d}/{next_month:02d}."
                )
                return

            for client in birthday_clients:
                self._create_client_card(client)

        except Exception as e:
            print(f"❌ Error: {e}")
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
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 10px;
                padding: 18px;
            }
            QFrame:hover {
                background-color: #f7f7f7;
                border-color: #b0b0b0;
            }
        """)
        card.setFixedHeight(120)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        # --- Info ---
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setSpacing(6)

        name = QLabel(client.get('name', 'Cliente'))
        name.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #222;
        """)

        details = QHBoxLayout()
        details.setSpacing(15)

        identity = QLabel(f"🆔 {client.get('identity', '—')}")
        phone = QLabel(f"📞 {client.get('phone_number', '—')}")
        for label in (identity, phone):
            label.setStyleSheet("font-size: 13px; color: #555;")
        details.addWidget(identity)
        details.addWidget(phone)
        details.addStretch()

        info_layout.addWidget(name)
        info_layout.addLayout(details)

        # --- Botón copiar ---
        copy_btn = QPushButton("Copiar mensaje")
        copy_btn.setFixedSize(150, 36)
        copy_btn.clicked.connect(lambda: self._copy_birthday_message(client))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #f2f2f2;
                color: #222;
                font-weight: 600;
                border-radius: 6px;
                border: 1px solid #ccc;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #cfcfcf;
            }
        """)

        layout.addWidget(info)
        layout.addStretch()
        layout.addWidget(copy_btn)

        self.cards_layout.addWidget(card)


    def _copy_birthday_message(self, client):
        name = client.get('name', 'Cliente')
        message = (
            f"🎉 ¡Hola {name.split()[0]}! 🎂\n\n"
            "🎈 Queremos adelantarte nuestros mejores deseos por tu cumpleaños. "
            "Gracias por ser parte de nuestra familia 💛.\n\n"
            "Para celebrarlo, te regalamos un *10% de descuento* en tu próximo pedido. "
            "🎁 Válido durante todo el mes de tu cumpleaños.\n\n"
            "¡Que tengas un día increíble lleno de alegría y cosas lindas! 🥳"
        )

        QApplication.clipboard().setText(message)
        QMessageBox.information(
            self,
            "Mensaje copiado",
            f"✅ Mensaje personalizado para {name} copiado al portapapeles."
        )
        
