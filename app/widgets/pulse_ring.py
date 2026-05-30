from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty, ListProperty
from kivy.animation import Animation

from .. import theme

class PulseRing(Widget):
    progress = NumericProperty(0.0)
    ring_color = ListProperty(list(theme.NEON_CYAN))
    label_text = NumericProperty(0)

    def __init__(self, **kw):
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (180, 180))
        super().__init__(**kw)
        with self.canvas:
            self._bg_col = Color(*self.ring_color[:3], 0.15)
            self._bg = Line(width=3, circle=(0, 0, 0))
            self._arc_col = Color(*self.ring_color[:3], 1)
            self._arc = Line(width=4, circle=(0, 0, 0, 0, 0))
        self.bind(size=self._sync, pos=self._sync, progress=self._sync, ring_color=self._cols)

    def _cols(self, *_):
        self._bg_col.rgba = [*self.ring_color[:3], 0.15]
        self._arc_col.rgba = [*self.ring_color[:3], 1]

    def _sync(self, *_):
        cx = self.center_x
        cy = self.center_y
        r = min(self.width, self.height) / 2 - 6
        self._bg.circle = (cx, cy, r)
        end_angle = 360 * max(0, min(self.progress, 1))
        self._arc.circle = (cx, cy, r, 0, end_angle)

    def animate_to(self, target: float):
        Animation.cancel_all(self, "progress")
        Animation(progress=target, d=theme.DUR_SLOW, t=theme.EASE_BACK).start(self)
