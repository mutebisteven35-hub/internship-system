import os
import sys

from dotenv import load_dotenv


project_folder = os.path.expanduser("~/ILES")
backend_path = os.path.join(project_folder, "backend")

load_dotenv(os.path.join(project_folder, ".env"))

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iles_backend.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
