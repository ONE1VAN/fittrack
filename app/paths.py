import os
import sys
from pathlib import Path

from kivy.utils import platform


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def writable_root() -> Path:
    if platform == "android":
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app is not None and app.user_data_dir:
                return Path(app.user_data_dir)
        except Exception:
            pass
        android_private = os.environ.get("ANDROID_PRIVATE")
        if android_private:
            return Path(android_private)
        return PROJECT_ROOT
    if _is_frozen():
        if sys.platform.startswith("win"):
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            return Path(base) / "FitTrack"
        return Path.home() / ".fittrack"
    return PROJECT_ROOT


def data_dir() -> Path:
    d = writable_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def videos_dir() -> Path:
    d = data_dir() / "videos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def thumbnails_dir() -> Path:
    d = data_dir() / "thumbnails"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return data_dir() / "fittrack.db"
