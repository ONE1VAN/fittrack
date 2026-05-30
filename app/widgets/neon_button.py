from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.properties import ListProperty, NumericProperty, StringProperty

from .. import theme

class _BaseBtn(ButtonBehavior, Label):
    bg_color    = ListProperty([0, 0, 0, 0])
    border_color = ListProperty([0, 0, 0, 0])
    glow_color  = ListProperty([0, 0, 0, 0])
    radius      = NumericProperty(theme.RADIUS_BUTTON)

    def __init__(self, **kw):
        kw.setdefault("color", theme.TEXT_PRIMARY)
        kw.setdefault("font_size", "12sp")
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 42)
        kw.setdefault("bold", True)
        kw.setdefault("halign", "center")
        kw.setdefault("valign", "middle")
        kw.setdefault("shorten", True)
        kw.setdefault("shorten_from", "right")
        super().__init__(**kw)
        with self.canvas.before:
            self._glow_col = Color(*self.glow_color)
            self._glow = RoundedRectangle(radius=[self.radius + 6] * 4)
            self._bg_col = Color(*self.bg_color)
            self._bg = RoundedRectangle(radius=[self.radius] * 4)
            self._brd_col = Color(*self.border_color)
            self._brd = Line(width=1.4, rounded_rectangle=(0, 0, 0, 0, self.radius))
        self.bind(size=self._sync, pos=self._sync,
                  bg_color=lambda *_: setattr(self._bg_col, "rgba", self.bg_color),
                  border_color=lambda *_: setattr(self._brd_col, "rgba", self.border_color),
                  glow_color=lambda *_: setattr(self._glow_col, "rgba", self.glow_color))
        self.bind(size=self._fit_text)
        self._fit_text()

    def _fit_text(self, *_):
        pad_x = 14
        self.text_size = (max(self.width - pad_x * 2, 1), self.height)

    def _sync(self, *_):
        self._bg.pos = self.pos;   self._bg.size = self.size
        self._glow.pos = (self.x - 4, self.y - 4)
        self._glow.size = (self.width + 8, self.height + 8)
        self._brd.rounded_rectangle = (*self.pos, *self.size, self.radius)

    def on_press(self):
        Animation.cancel_all(self, "glow_color")
        target = list(theme.GLOW_CYAN)
        target[3] = 0.85
        Animation(glow_color=target, d=0.08).start(self)

    def on_release(self):
        Animation.cancel_all(self, "glow_color")
        Animation(glow_color=[*theme.GLOW_CYAN[:3], 0], d=theme.DUR_SLOW, t="out_cubic").start(self)

class NeonButton(_BaseBtn):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bg_color = [theme.NEON_CYAN[0], theme.NEON_CYAN[1], theme.NEON_CYAN[2], 0.18]
        self.border_color = list(theme.NEON_CYAN)
        self.color = theme.NEON_CYAN

class GhostButton(_BaseBtn):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bg_color = [1, 1, 1, 0.03]
        self.border_color = [1, 1, 1, 0.2]
        self.color = theme.TEXT_PRIMARY

class DangerButton(_BaseBtn):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bg_color = [theme.DANGER_RED[0], theme.DANGER_RED[1], theme.DANGER_RED[2], 0.15]
        self.border_color = list(theme.DANGER_RED)
        self.color = theme.DANGER_RED
