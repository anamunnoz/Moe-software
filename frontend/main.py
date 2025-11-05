from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QHBoxLayout, QGraphicsDropShadowEffect, QStackedWidget
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QColor, QPixmap, QFont
import sys
from books import BooksPage
from client import ClientsPage
from gestion import GestionPage
from consultas import ConsultasPage
from order import OrderWidget
from production import ProductionStatusTab
from vouchers import VouchersTab
from generate_excel import ExcelTab
from birthday import BirthdayTab

class SidebarButton(QPushButton):
    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(22, 22))
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1C1818;
                text-align: left;
                border: none;
                padding-left: 15px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                color: black;
                opacity: 0.2;
                border-radius: 6px;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
            }
        """)


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = True
        self.initUI()

    def initUI(self):
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(3, 0)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(8)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(10)

        title_label = QLabel("MOE LIBROS")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addWidget(header)

        self.btn_books = SidebarButton("icons/books.png", "Libros")
        self.btn_precio = SidebarButton("icons/price.png", "Precio")
        self.btn_clientes = SidebarButton("icons/client.png", "Clientes")
        self.btn_gestion = SidebarButton("icons/gestion.png", "Mensajería y aditivos")
        self.btn_ordenes = SidebarButton("icons/order.png", "Órdenes")
        self.btn_production = SidebarButton("icons/selected_book.png", "Estado de producción")
        self.btn_vauchers = SidebarButton("icons/tickets.png", "Generar vales")
        self.btn_excel = SidebarButton("icons/xls.png", "Generar excel")
        self.btn_birthday = SidebarButton("icons/cake.png", "Cumpleaños de clientes")

        layout.addWidget(self.btn_precio)
        layout.addWidget(self.btn_ordenes)
        layout.addWidget(self.btn_clientes)
        layout.addWidget(self.btn_production)
        layout.addWidget(self.btn_vauchers)
        layout.addWidget(self.btn_excel)
        layout.addWidget(self.btn_books)
        layout.addWidget(self.btn_gestion)
        layout.addWidget(self.btn_birthday)
        

        layout.addStretch()

        toggle_btn = QPushButton("⫶")
        toggle_btn.setStyleSheet("""
            QPushButton {
                color: #888;
                border: none;
                background: transparent;
                font-size: 20px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        toggle_btn.clicked.connect(self.toggle_sidebar)

        self.setLayout(layout)

    def toggle_sidebar(self):
        width = 200 if self.expanded else 60
        new_width = 60 if self.expanded else 200
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(width)
        self.animation.setEndValue(new_width)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()
        self.expanded = not self.expanded


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MOE LIBROS - Panel de Control")
        self.setGeometry(200, 100, 1000, 600)

        container = QWidget()
        layout = QHBoxLayout(container)

        self.sidebar = Sidebar()

        self.stack = QStackedWidget()
        self.books_page = BooksPage()
        self.client_page = ClientsPage()
        self.gestion_page = GestionPage()
        self.consultas_page = ConsultasPage()
        self.order_page = OrderWidget()
        self.production_page = ProductionStatusTab()
        self.vauchers_page = VouchersTab()
        self.generate_excel_page = ExcelTab()
        self.birthday_page = BirthdayTab()
        self.default_page = QWidget()
        


        self.default_page.setStyleSheet("background-color: #FFFFFF;")

        self.stack.addWidget(self.default_page)
        self.stack.addWidget(self.consultas_page)
        self.stack.addWidget(self.books_page)
        self.stack.addWidget(self.client_page)
        self.stack.addWidget(self.gestion_page)
        self.stack.addWidget(self.order_page)
        self.stack.addWidget(self.production_page)
        self.stack.addWidget(self.vauchers_page)
        self.stack.addWidget(self.generate_excel_page)
        self.stack.addWidget(self.birthday_page)



        self.sidebar.btn_books.clicked.connect(lambda: self.stack.setCurrentWidget(self.books_page))
        self.sidebar.btn_clientes.clicked.connect(lambda: self.stack.setCurrentWidget(self.client_page))
        self.sidebar.btn_gestion.clicked.connect(lambda: self.stack.setCurrentWidget(self.gestion_page))
        self.sidebar.btn_precio.clicked.connect(lambda: self.stack.setCurrentWidget(self.consultas_page))
        self.sidebar.btn_ordenes.clicked.connect(lambda: self.stack.setCurrentWidget(self.order_page))
        self.sidebar.btn_production.clicked.connect(lambda: self.stack.setCurrentWidget(self.production_page))
        self.sidebar.btn_vauchers.clicked.connect(lambda: self.stack.setCurrentWidget(self.vauchers_page))
        self.sidebar.btn_excel.clicked.connect(lambda: self.stack.setCurrentWidget(self.generate_excel_page))
        self.sidebar.btn_birthday.clicked.connect(lambda: self.stack.setCurrentWidget(self.birthday_page))




        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        layout.setStretch(1, 1)

        self.setCentralWidget(container)
        self.stack.setCurrentWidget(self.default_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
