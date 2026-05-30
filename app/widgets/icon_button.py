from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.properties import ListProperty

from .. import theme


class _IconBase(ButtonBehavior, Widget):
    fill_color   = ListProperty([0, 0, 0, 0])
    stroke_color = ListProperty(theme.TEXT_PRIMARY)
    border_color = ListProperty([0, 0, 0, 0])

    def __init__(self, **kw):
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (38, 38))
        super().__init__(**kw)
        with self.canvas:
            self._fill_c = Color(*self.fill_color)
            self._disc = Ellipse(pos=self.pos, size=self.size)
            self._brd_c = Color(*self.border_color)
            self._brd = Line(width=1.2, ellipse=(0, 0, 0, 0))
            self._stroke_c = Color(*self.stroke_color)
        self.bind(size=self._sync, pos=self._sync,
                  fill_color=self._update_fill,
                  stroke_color=self._update_stroke,
                  border_color=self._update_border)
        self._draw_glyph()
        self._sync()

    def _draw_glyph(self):
        pass

    def _sync(self, *_):
        self._disc.pos = self.pos
        self._disc.size = self.size
        self._brd.ellipse = (self.x, self.y, self.width, self.height)
        self._update_glyph()

    def _update_glyph(self):
        pass

    def _update_fill(self, *_):    self._fill_c.rgba = self.fill_color
    def _update_stroke(self, *_):  self._stroke_c.rgba = self.stroke_color
    def _update_border(self, *_):  self._brd_c.rgba = self.border_color


class CheckIcon(_IconBase):
    def __init__(self, **kw):
        kw.setdefault("fill_color", [*theme.ENERGY_GREEN[:3], 0.18])
        kw.setdefault("border_color", [*theme.ENERGY_GREEN[:3], 0.9])
        kw.setdefault("stroke_color", theme.ENERGY_GREEN)
        super().__init__(**kw)

    def _draw_glyph(self):
        with self.canvas:
            self._line = Line(points=[0, 0, 0, 0, 0, 0], width=2.2, cap="round", joint="round")

    def _update_glyph(self):
        cx, cy = self.center_x, self.center_y
        s = min(self.width, self.height)

        p1 = (cx - s * 0.22, cy - s * 0.02)
        p2 = (cx - s * 0.05, cy - s * 0.18)
        p3 = (cx + s * 0.22, cy + s * 0.16)
        self._line.points = [*p1, *p2, *p3]


class CrossIcon(_IconBase):
    def __init__(self, **kw):
        kw.setdefault("fill_color", [*theme.DANGER_RED[:3], 0.16])
        kw.setdefault("border_color", [*theme.DANGER_RED[:3], 0.9])
        kw.setdefault("stroke_color", theme.DANGER_RED)
        super().__init__(**kw)

    def _draw_glyph(self):
        with self.canvas:
            self._l1 = Line(points=[0, 0, 0, 0], width=2.2, cap="round")
            self._l2 = Line(points=[0, 0, 0, 0], width=2.2, cap="round")

    def _update_glyph(self):
        cx, cy = self.center_x, self.center_y
        s = min(self.width, self.height) * 0.22
        self._l1.points = [cx - s, cy - s, cx + s, cy + s]
        self._l2.points = [cx - s, cy + s, cx + s, cy - s]


class MinusIcon(_IconBase):
    def __init__(self, **kw):
        kw.setdefault("fill_color", list(theme.DANGER_RED))
        kw.setdefault("border_color", [*theme.DANGER_RED[:3], 1.0])
        kw.setdefault("stroke_color", theme.TEXT_PRIMARY)
        super().__init__(**kw)

    def _draw_glyph(self):
        with self.canvas:
            self._bar = Line(points=[0, 0, 0, 0], width=2.4, cap="round")

    def _update_glyph(self):
        cx, cy = self.center_x, self.center_y
        s = min(self.width, self.height) * 0.26
        self._bar.points = [cx - s, cy, cx + s, cy]
