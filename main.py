import os
import logging
from kivy.config import Config

Config.set("graphics", "width",  "420")
Config.set("graphics", "height", "880")
Config.set("graphics", "resizable", "0")
Config.set("input",    "mouse",  "mouse,multitouch_on_demand")

from kivy.logger import Logger

class _SuppressVideoImageLoadErrors(logging.Filter):
    _exts = (".mp4", ".MP4", ".mov", ".MOV", ".webm", ".WEBM", ".m4v")
    def filter(self, record):
        try:
            msg = record.getMessage()
        except Exception:
            return True
        if "Error loading" not in msg:
            return True
        return not any(ext in msg for ext in self._exts)

Logger.addFilter(_SuppressVideoImageLoadErrors())

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from pathlib import Path

from app.theme import BG_DEEP
from app.navigation import AppNav
from app.database import get_db
from app.screens import ALL_SCREENS

ROOT = Path(__file__).resolve().parent
_dv_regular = ROOT / "assets" / "fonts" / "DejaVuSans.ttf"
_dv_bold    = ROOT / "assets" / "fonts" / "DejaVuSans-Bold.ttf"
if _dv_regular.exists():
    LabelBase.register(
        name="Roboto",
        fn_regular=str(_dv_regular),
        fn_bold=str(_dv_bold) if _dv_bold.exists() else str(_dv_regular),
    )


class FitTrackApp(App):
    title = "FitTrack"

    def build(self):
        Window.clearcolor = BG_DEEP

        get_db()

        nav = AppNav()
        for screen_cls in ALL_SCREENS:
            nav.add_widget(screen_cls())
        nav.current = "splash"
        return nav


if __name__ == "__main__":
    FitTrackApp().run()
