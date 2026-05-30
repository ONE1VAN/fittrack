from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.animation import Animation

from .. import theme
from ..widgets import AnimatedBackground, PulseRing

class SplashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="splash", **kw)
        bg = AnimatedBackground(density=40)
        wrap = FloatLayout()

        self.ring = PulseRing(
            size=(220, 220),
            ring_color=list(theme.NEON_CYAN),
            pos_hint={"center_x": 0.5, "center_y": 0.55},
        )
        wrap.add_widget(self.ring)

        title = Label(
            text="[b]FIT[/b][color=#00F0FF]TRACK[/color]",
            markup=True,
            font_size="40sp",
            color=theme.TEXT_PRIMARY,
            pos_hint={"center_x": 0.5, "center_y": 0.55},
        )
        wrap.add_widget(title)

        subtitle = Label(
            text="Інформаційна система тренажерного залу",
            font_size="14sp",
            color=theme.TEXT_SECONDARY,
            pos_hint={"center_x": 0.5, "center_y": 0.38},
        )
        wrap.add_widget(subtitle)

        bg.add_widget(wrap)
        self.add_widget(bg)

    def on_enter(self):
        self.ring.progress = 0
        self.ring.animate_to(1.0)
        Clock.schedule_once(self._next, 1.4)

    def _next(self, *_):
        self.manager.fade_to("login")
