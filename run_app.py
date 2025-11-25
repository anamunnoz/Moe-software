import os
import sys
import threading
import time
import socket
import django
from django.core.management import call_command
import traceback
from frontend.main import main as frontend_main

if getattr(sys, 'frozen', False):
    sys.stdout = open("output.log", "w", encoding="utf-8")
    sys.stderr = open("error.log", "w", encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MOE.settings")

os.chdir(BASE_DIR)
django.setup()

def start_django_server():
    try:
        call_command(
            'runserver',
            '0.0.0.0:8000',
            use_reloader=False,
            verbosity=0
        )
    except Exception as e:
        with open("django_error.log", "w", encoding="utf-8") as f:
            f.write(str(e))


t = threading.Thread(target=start_django_server, daemon=True)
t.start()


def wait_for_server(host='127.0.0.1', port=8000, timeout=40):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            time.sleep(0.3)
    return False

if not wait_for_server():
    with open("startup.log", "w", encoding="utf-8") as f:
        f.write("ERROR: El servidor Django no arrancó en tiempo.")

try:
    if getattr(sys, 'frozen', False):
        os.environ["DJANGO_BASE_DIR"] = os.path.dirname(sys.executable)

        basedir = sys._MEIPASS
        dll_path = os.path.join(basedir, "PySide6")
        if not os.path.exists(dll_path):
            dll_path = os.path.join(basedir, "_internal", "PySide6")

        os.environ["PATH"] += os.pathsep + dll_path
        os.environ["QT_PLUGIN_PATH"] = os.path.join(dll_path, "plugins")
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(dll_path, "plugins", "platforms")
    frontend_main()
except Exception as e:
    with open("fatal_error.log", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())