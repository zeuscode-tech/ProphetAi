"""WSGI config for ProphetAI."""

import os
import sys
from pathlib import Path

# Add backend/ to sys.path so `prophetai` package is importable on Vercel
# (Vercel runs from repo root, so backend/ is not in sys.path by default)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prophetai.settings")

application = get_wsgi_application()
