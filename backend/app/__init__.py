"""Echo Base backend application package."""

import sys
from pathlib import Path

__version__ = "0.1.0"

# Dynamically loaded plugins (plugins/<id>/plugin.py) live outside this
# package and are imported via importlib. They need `backend/` on
# sys.path so `from app.plugins import ReceiverPlugin` works regardless
# of how the server process was launched (uvicorn, gunicorn, pytest...).
_BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)
