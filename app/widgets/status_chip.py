from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty

from .. import theme

class StatusChip(Label):
    status = StringProperty("active")

    def __init__(self, status: str = "active", **kw):
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("height", 26)
        kw.setdefault("font_size", "12sp")
        kw.setdefault("bold", True)
        kw.setdefault("padding", (12, 4))
        super().__init__(**kw)
        with self.canvas.before:
            self._bg_col = Color(0, 0, 0, 0)
            self._bg = RoundedRectangle(radius=[theme.RADIUS_CHIP])
        self.bind(size=self._sync, pos=self._sync, status=self._refresh, texture_size=self._tex)
        self.status = status

    def _tex(self, *_):

        self.width = self.texture_size[0] + 22

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _refresh(self, *_):
        col = theme.STATUS_COLORS.get(self.status, theme.TEXT_MUTED)
        self._bg_col.rgba = [col[0], col[1], col[2], 0.18]
        self.color = col
        self.text = theme.STATUS_LABELS_UA.get(self.status, self.status)
