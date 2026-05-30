from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.properties import ListProperty, NumericProperty

from .. import theme

class GlassCard(BoxLayout):
    fill_color   = ListProperty(theme.GLASS_TINT)
    border_color = ListProperty(theme.GLASS_BORDER)
    glow_color   = ListProperty([0, 0, 0, 0])
    radius       = NumericProperty(theme.RADIUS_CARD)

    def __init__(self, **kw):
        kw.setdefault("orientation", "vertical")
        kw.setdefault("padding", theme.PADDING)
        kw.setdefault("spacing", theme.GAP)
        super().__init__(**kw)
        with self.canvas.before:
            self._glow_col = Color(*self.glow_color)
            self._glow = RoundedRectangle(radius=[self.radius + 6] * 4)
            self._fill_col = Color(*self.fill_color)
            self._fill = RoundedRectangle(radius=[self.radius] * 4)
            self._border_col = Color(*self.border_color)
            self._border = Line(width=1.2, rounded_rectangle=(0, 0, 0, 0, self.radius))
        self.bind(size=self._sync, pos=self._sync,
                  fill_color=self._update_fill, border_color=self._update_border,
                  glow_color=self._update_glow, radius=self._update_radius)

    def _sync(self, *_):
        self._glow.pos = (self.x - 4, self.y - 4)
        self._glow.size = (self.width + 8, self.height + 8)
        self._fill.pos = self.pos
        self._fill.size = self.size
        self._border.rounded_rectangle = (*self.pos, *self.size, self.radius)

    def _update_fill(self, *_):   self._fill_col.rgba   = self.fill_color
    def _update_border(self, *_): self._border_col.rgba = self.border_color
    def _update_glow(self, *_):   self._glow_col.rgba   = self.glow_color
    def _update_radius(self, *_):
        self._fill.radius = [self.radius] * 4
        self._glow.radius = [self.radius + 6] * 4
        self._sync()

    def animate_in(self, delay: float = 0.0):
        self.opacity = 0

        Animation(opacity=1, d=theme.DUR_NORMAL, t=theme.EASE).start(self)

    def flash(self, color=None):
        color = color or theme.GLOW_CYAN
        self.glow_color = list(color)
        Animation(glow_color=[color[0], color[1], color[2], 0],
                  d=theme.DUR_SLOW, t="out_cubic").start(self)
