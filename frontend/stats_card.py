from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QListWidgetItem, QFrame)
from PySide6.QtGui import QPixmap, QPen, QColor, QPainter
from PySide6.QtCore import Qt, QDateTime
from datetime import datetime
import requests
from urls import API_URL_DASHBOARD

class StatCard(QFrame):
    def __init__(self, title, value, icon_path, color="#3498db"):
        super().__init__()
        self.color = color
        self.icon_path = icon_path
        self.value_label = None
        self.setup_ui(title, value)

    def setup_ui(self, title, value):
        self.setFixedSize(210, 110)
        self.setStyleSheet(f"""
            QFrame {{
                border: none;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        pixmap = QPixmap(self.icon_path).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #555; font-size: 13px; font-weight: 600;")

        self.value_label = QLabel(str(value))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"color: {self.color}; font-size: 28px; font-weight: bold;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        if self.value_label:
            self.value_label.setText(str(value))


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_statistics()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                font-family: 'Segoe UI';
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        header = self.create_header()
        layout.addWidget(header)

        stats_widget = self.create_stats_cards()
        layout.addWidget(stats_widget)

        charts_widget = self.create_charts_section()
        layout.addWidget(charts_widget)

        refresh_btn = QPushButton("Actualizar estadísticas")
        refresh_btn.clicked.connect(self.load_statistics)
        refresh_btn.setFixedHeight(40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

    def create_header(self):
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)


        welcome_label = QLabel("Bienvenido a MOE LIBROS")
        welcome_label.setStyleSheet("""
            font-size: 30px;
            font-weight: 700;
            color: #2c3e50;
        """)
        welcome_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        layout.addStretch()
        layout.addWidget(welcome_label)
        layout.addStretch()

        return header

    def create_stats_cards(self):
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                border: none;
                border-radius: 10px;
            }
        """)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.orders_card = StatCard("Total pedidos", "0", "icons/orders.png", "#e74c3c")
        self.clients_card = StatCard("Total clientes", "0", "icons/client.png", "#3498db")
        self.month_orders_card = StatCard("Pedidos este mes", "0", "icons/calendar.png", "#27ae60")
        self.books_ordered_card = StatCard("Libros pedidos", "0", "icons/bookcount.png", "#f39c12")
        self.month_income_card = StatCard("Ingresos del mes", "$0", "icons/price.png", "#16a085")

        layout.addStretch()
        layout.addWidget(self.orders_card)
        layout.addWidget(self.clients_card)
        layout.addWidget(self.month_orders_card)
        layout.addWidget(self.books_ordered_card)
        layout.addWidget(self.month_income_card)
        layout.addStretch()
        return widget

    def create_charts_section(self):
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                border: none;
                border-radius: 10px;
            }
        """)
        layout = QHBoxLayout(widget)

        # --- Contenedor de la gráfica ---
        chart_container = QFrame()
        chart_container.setStyleSheet("""
            QFrame {
                background-color: #f5f6fa;
                border-radius: 10px;
                border: none;
            }
        """)
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(15, 0, 15, 5)
        chart_layout.setSpacing(0)

        # --- Título con icono ---
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        icon_label = QLabel()
        pixmap = QPixmap("icons/diagram.png").scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignTop)

        chart_title = QLabel("Pedidos del mes")
        chart_title.setStyleSheet("""
            font-size: 17px;
            font-weight: 600;
            color: #2c3e50;
            padding-top: 0px;
            margin-bottom: 0px; 
            margin-top: 0px; 
        """)
        chart_title.setAlignment(Qt.AlignTop)

        title_layout.addWidget(icon_label)
        title_layout.addWidget(chart_title)
        title_layout.addStretch()

        self.chart_view = QChartView()
        self.chart_view.setFixedHeight(400)
        self.chart_view.setStyleSheet("""
            QChartView {
                margin: 0px;
                padding: 0px;
                border: none;
            }
        """)

        chart_layout.addLayout(title_layout)
        chart_layout.addSpacing(2)
        chart_layout.addWidget(self.chart_view)

        # --- Top libros ---
        books_container = QFrame()
        books_container.setStyleSheet("""
            QFrame {
                background-color: #f5f6fa;
                border-radius: 10px;
                border: none;
            }
        """)
        books_layout = QVBoxLayout(books_container)
        books_layout.setContentsMargins(15, 5, 15, 15)
        books_layout.setSpacing(10) 

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        icon_label = QLabel()
        pixmap = QPixmap("icons/trophy.png").scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignTop)

        books_title = QLabel("Top 5 libros del mes")
        books_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
            margin-top: 3px;
        """)

        title_layout.addWidget(icon_label)
        title_layout.addWidget(books_title)
        title_layout.addStretch()

        self.books_list = QListWidget()
        self.books_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                font-size: 14px;
                color: #2c3e50;
                padding-top: 5px;
            }
            QListWidget::item {
                margin-bottom: 4px;
                border-bottom: 1px solid #f0f0f0;
            }
        """)

        books_layout.addLayout(title_layout)
        books_layout.addWidget(self.books_list)

        layout.addWidget(chart_container, 2)
        layout.addWidget(books_container, 1)

        return widget

    def load_statistics(self):
        try:
            response = requests.get(f'{API_URL_DASHBOARD}main_stats/')
            if response.status_code == 200:
                data = response.json()
                current_month = datetime.now().month
                if data.get('month_orders_date'):
                    valid_orders = [o for o in data['month_orders_date'] if datetime.fromisoformat(o['date']).month == current_month]
                    month_total = sum(o['count'] for o in valid_orders)
                else:
                    month_total = data.get('month_orders', 0)

                self.orders_card.set_value(data['total_orders'])
                self.clients_card.set_value(data['total_clients'])
                self.month_orders_card.set_value(month_total)
                self.books_ordered_card.set_value(data.get('total_books_ordered', 0))
                month_income = data.get('month_income', 0)
                self.month_income_card.set_value(f"${month_income:,.2f}")

            self.load_chart_data()
            self.load_top_books()
        except Exception as e:
            print("Error:", e)

    def load_chart_data(self):
        try:
            response = requests.get(f'{API_URL_DASHBOARD}monthly_orders_chart/')
            if response.status_code == 200:
                data = response.json()
                self.create_chart(data['chart_data'])
        except Exception as e:
            print("Error gráfica:", e)

    def load_top_books(self):
        try:
            response = requests.get(f'{API_URL_DASHBOARD}top_books_month/')
            if response.status_code == 200:
                data = response.json()
                self.books_list.clear()

                current_month = datetime.now().month
                for i, book in enumerate(data['top_books'], 1):
                    if 'month' in book and int(book['month']) != current_month:
                        continue

                    item_widget = QWidget()
                    item_layout = QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(4, 8, 4, 8)
                    item_layout.setSpacing(10)

                    num_label = QLabel(f"{i}")
                    num_label.setFixedWidth(18)
                    num_label.setAlignment(Qt.AlignCenter)
                    num_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 15px;")


                    book_label = QLabel(book['book'])
                    book_label.setStyleSheet("""
                        color: #2c3e50;
                        font-size: 14px;
                        font-weight: 500;
                    """)
                    book_label.setWordWrap(True)
                    badge = QLabel(f"{book['orders']} veces")
                    badge.setStyleSheet("""
                        background-color: #ecf0f1;
                        color: #555;
                        border-radius: 8px;
                        padding: 4px 8px;
                        font-size: 12px;
                        font-weight: 600;
                    """)
                    badge.setAlignment(Qt.AlignCenter)
                    item_layout.addWidget(num_label)
                    item_layout.addWidget(book_label)
                    item_layout.addStretch()
                    item_layout.addWidget(badge)
                    list_item = QListWidgetItem()
                    list_item.setSizeHint(item_widget.sizeHint())
                    self.books_list.addItem(list_item)
                    self.books_list.setItemWidget(list_item, item_widget)

        except Exception as e:
            print("Error top libros:", e)

    def create_chart(self, chart_data):
        series = QLineSeries()
        pen = QPen(QColor("#2c3e50"))
        pen.setWidth(2)
        series.setPen(pen)

        for point in chart_data:
            date = QDateTime.fromString(point['date'], "yyyy-MM-dd")
            series.append(date.toMSecsSinceEpoch(), point['orders'])

        chart = QChart()
        chart.addSeries(series)
        chart.setBackgroundBrush(Qt.white)
        chart.legend().hide()
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd MMM")
        axis_x.setTitleText("")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        self.chart_view.setRenderHint(QPainter.Antialiasing, True)
        self.chart_view.setChart(chart)
