import os, sys, threading, time, socket, django
from django.core.management import call_command
import PySide6, PySide6.QtCore
from frontend.main import main as frontend_main
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MOE.settings")

os.chdir(BASE_DIR)

django.setup()

def start_django_server():
    call_command('runserver', '127.0.0.1:8000', use_reloader=False)

t = threading.Thread(target=start_django_server, daemon=True)
t.start()

def wait_for_server(host='127.0.0.1', port=8000, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            time.sleep(0.3)
    return False

if not wait_for_server():
    print("ERROR: El servidor Django no arrancó en 30s. Revisa logs.")

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
    traceback.print_exc()