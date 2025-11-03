import requests
import unicodedata
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

def normalize_text(text):
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return text.lower()

def http_get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=5)
        return r
    except Exception as e:
        print(f"[ERROR GET] {e}")
        return None

def http_post(url, data):
    try:
        r = requests.post(url, json=data, timeout=5)
        return r
    except Exception as e:
        print(f"[ERROR POST] {e}")
        return None

def http_delete(url, params=None):
    try:
        r = requests.delete(url, params=params, timeout=5)
        return r
    except Exception as e:
        print(f"[ERROR DELETE] {e}")
        return None

def http_patch(url, data=None, params=None):
    try:
        r = requests.patch(url, json=data, params=params, timeout=5)
        return r
    except Exception as e:
        print(f"[ERROR PATCH] {e}")
        return None

def http_put(url, data):
    try:        
        response = requests.put(
            url,
            json=data,
            headers={'Content-Type': 'application/json'}
        )        
        return response
    except Exception as e:
        return None

def make_icon_label(icon_path, text):
        label = QWidget()
        layout = QHBoxLayout(label)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        icon = QLabel()
        pixmap = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon.setPixmap(pixmap)

        text_label = QLabel(text)
        text_label.setStyleSheet("font-weight: 500;")

        layout.addWidget(icon)
        layout.addWidget(text_label)
        layout.addStretch()
        return label



