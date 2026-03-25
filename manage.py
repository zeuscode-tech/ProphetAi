"""Root-level Django management entry point.

Delegates to the Django project inside the ``backend/`` directory so that
management commands (e.g. ``python manage.py createsuperuser``) can be run
from the repository root without ``cd backend`` first.
"""

import os
import sys


def main():
    # Insert the backend directory at the front of sys.path so that the
    # Django project package (``prophetai``) and its apps are importable.
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prophetai.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
