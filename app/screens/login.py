from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation

from .. import theme
from ..widgets import AnimatedBackground, GlassCard, NeonButton, GhostButton
from ..auth import authenticate

class _NeonInput(TextInput):
    def __init__(self, **kw):
        kw.setdefault("background_color", [1, 1, 1, 0.06])
        kw.setdefault("foreground_color", theme.TEXT_PRIMARY)
        kw.setdefault("cursor_color", theme.NEON_CYAN)
        kw.setdefault("font_size", "16sp")
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 50)
        kw.setdefault("padding", [14, 14, 14, 14])
        kw.setdefault("multiline", False)
        kw.setdefault("write_tab", False)
        super().__init__(**kw)

class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="login", **kw)
        bg = AnimatedBackground(density=30)

        outer = FloatLayout()
        card = GlassCard(
            size_hint=(0.86, None),
            height=460,
            pos_hint={"center_x": 0.5, "center_y": 0.52},
            padding=24,
            spacing=14,
        )

        card.add_widget(Label(
            text="[b]FIT[/b][color=#00F0FF]TRACK[/color]",
            markup=True, font_size="34sp", color=theme.TEXT_PRIMARY,
            size_hint_y=None, height=54,
        ))
        card.add_widget(Label(
            text="Вхід в систему",
            font_size="14sp", color=theme.TEXT_SECONDARY,
            size_hint_y=None, height=18,
        ))

        self.email = _NeonInput(hint_text="Email", hint_text_color=theme.TEXT_MUTED)
        self.password = _NeonInput(hint_text="Пароль", password=True, hint_text_color=theme.TEXT_MUTED)
        card.add_widget(Label(text="", size_hint_y=None, height=6))
        card.add_widget(self.email)
        card.add_widget(self.password)

        self.error_lbl = Label(
            text="", color=theme.DANGER_RED, font_size="13sp",
            size_hint_y=None, height=18,
        )
        card.add_widget(self.error_lbl)

        login_btn = NeonButton(text="УВІЙТИ")
        login_btn.bind(on_release=self._do_login)
        card.add_widget(login_btn)

        demo_hint = Label(
            text="[i]Demo: admin@gym.ua / admin123\n",
            markup=True, font_size="11sp", color=theme.TEXT_MUTED,
            size_hint_y=None, height=58, halign="center",
        )
        demo_hint.bind(size=lambda *a: setattr(demo_hint, "text_size", demo_hint.size))
        card.add_widget(demo_hint)

        outer.add_widget(card)
        bg.add_widget(outer)
        self.add_widget(bg)
        self._card = card

    def on_pre_enter(self):
        self._card.opacity = 0
        self._card.y -= 30

    def on_enter(self):
        Animation(opacity=1, y=self._card.y + 30, d=theme.DUR_NORMAL, t="out_back").start(self._card)

    def _do_login(self, *_):
        email = self.email.text.strip().lower()
        password = self.password.text
        user = authenticate(email, password)
        if user is None:
            self.error_lbl.text = "Невірний email або пароль"
            self._card.flash(theme.DANGER_RED)

            anim = (Animation(x=self._card.x - 12, d=0.05)
                    + Animation(x=self._card.x + 12, d=0.05)
                    + Animation(x=self._card.x, d=0.05))
            anim.start(self._card)
            return
        self.error_lbl.text = ""
        self._card.flash(theme.NEON_CYAN)
        self.manager.go_home()
