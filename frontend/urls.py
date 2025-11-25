import os
from dotenv import load_dotenv
import sys

def load_env_for_pyinstaller():
    if getattr(sys, 'frozen', False):
        env_path = os.path.join(sys._MEIPASS, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    else:
        load_dotenv()
load_env_for_pyinstaller()

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")

BASE_URL = f"http://{API_HOST}:{API_PORT}/api"

API_URL_BOOKS = f"{BASE_URL}/books/"
API_URL_CLIENTES = f"{BASE_URL}/clients/"
API_URL_ADITIVOS = f"{BASE_URL}/additives/"
API_URL_MENSAJERIAS = f"{BASE_URL}/deliveries/"
API_URL_ORDERS = f"{BASE_URL}/orders/"
API_URL_REQUESTED_BOOKS = f"{BASE_URL}/requested_books/"
API_URL_REQUESTED_BOOK_ADDITIVES = f"{BASE_URL}/requested_book_additives/"
API_URL_BOOK_ON_ORDER = f"{BASE_URL}/books_on_order/"
API_URL_DASHBOARD = f"{BASE_URL}/dashboard/"
API_URL_PRODUCTION_COSTS = f"{BASE_URL}/production_costs/"




