from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import StringProperty

from .. import theme
from ..auth import Session
from ..widgets import AnimatedBackground

class TopBar(BoxLayout):
    def __init__(self, title: str, back_screen: str | None = None, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 56)
        kw.setdefault("padding", [16, 8, 16, 8])
        kw.setdefault("spacing", 12)
        super().__init__(**kw)
        self.back_screen = back_screen
        if back_screen:
            back = NavIconButton(symbol="◄", on_press_screen=back_screen, direction="right")
            self.add_widget(back)

        title_lbl = Label(
            text=f"[b]{title}[/b]", markup=True,
            font_size="18sp", color=theme.TEXT_PRIMARY,
            shorten=True, shorten_from="right",
            halign="left", valign="middle",
        )
        title_lbl.bind(size=lambda *a: setattr(title_lbl, "text_size", title_lbl.size))
        self.add_widget(title_lbl)

        user_lbl = Label(
            text=Session.full_name or "",
            color=theme.TEXT_SECONDARY, font_size="11sp",
            shorten=True, shorten_from="right",
            size_hint_x=None, width=110, halign="right", valign="middle",
        )
        user_lbl.bind(size=lambda *a: setattr(user_lbl, "text_size", user_lbl.size))
        self.add_widget(user_lbl)

class NavIconButton(ButtonBehavior, Label):
    def __init__(self, symbol: str, on_press_screen: str, direction: str = "left",
                 active: bool = False, **kw):
        super().__init__(
            text=f"[size=22sp]{symbol}[/size]",
            markup=True,
            color=theme.NEON_CYAN if active else theme.TEXT_SECONDARY,
            size_hint=(None, None), size=(48, 48), **kw)
        self._target = on_press_screen
        self._direction = direction
        active_rgba = list(theme.NEON_CYAN[:3]) + [0.12]
        with self.canvas.before:
            self._bg_c = Color(*(active_rgba if active else (0, 0, 0, 0)))
            self._bg = RoundedRectangle(radius=[14])
        self.bind(size=self._sync, pos=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def on_release(self):
        if self.parent is None or self.parent.parent is None:
            return

        node = self.parent
        while node is not None and not hasattr(node, "go"):
            node = node.parent
        if node is not None:
            node.go(self._target, direction=self._direction)

class BottomNav(BoxLayout):
    def __init__(self, active: str = "home", **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 64)
        kw.setdefault("padding", [8, 6, 8, 6])
        kw.setdefault("spacing", 4)
        super().__init__(**kw)
        with self.canvas.before:
            Color(*theme.BG_SURFACE[:3], 0.85)
            self._bg = RoundedRectangle(radius=[22, 22, 0, 0])
        self.bind(size=self._sync, pos=self._sync)

        items = self._items_for_role(Session.role)
        for sym, label, screen, key in items:
            btn = _BottomNavItem(symbol=sym, label=label, target=screen,
                                 active=(key == active))
            self.add_widget(btn)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    @staticmethod
    def _items_for_role(role: str):
        if role == "client":
            return [
                ("◉", "Головна",    _home_for(role),  "home"),
                ("▣", "Розклад",    "schedule",        "schedule"),
                ("◆", "Абонементи", "subscriptions",   "subs"),
                ("▶", "Відео",      "video_feed",      "video"),
                ("●", "Профіль",    "profile",         "profile"),
            ]
        return [
            ("◉", "Головна", _home_for(role), "home"),
            ("▣", "Розклад", "schedule",      "schedule"),
            ("▶", "Відео",   "video_feed",    "video"),
            ("●", "Профіль", "profile",       "profile"),
        ]

def _home_for(role: str) -> str:
    return {
        "client": "home_client",
        "trainer": "home_trainer",
    }.get(role, "home_admin")

class _BottomNavItem(ButtonBehavior, BoxLayout):
    def __init__(self, symbol: str, label: str, target: str, active: bool, **kw):
        kw.setdefault("orientation", "vertical")
        kw.setdefault("spacing", 1)
        super().__init__(**kw)
        self._target = target
        color = theme.NEON_CYAN if active else theme.TEXT_SECONDARY
        active_rgba = list(theme.NEON_CYAN[:3]) + [0.08]
        with self.canvas.before:
            self._bg_c = Color(*(active_rgba if active else (0, 0, 0, 0)))
            self._bg = RoundedRectangle(radius=[14])
        self.bind(size=self._sync, pos=self._sync)
        sym = Label(text=symbol, font_size="22sp", color=color, size_hint_y=None, height=28)
        lbl = Label(text=label, font_size="10sp", color=color, size_hint_y=None, height=14)
        self.add_widget(sym)
        self.add_widget(lbl)

    def _sync(self, *_):
        self._bg.pos = (self.x + 4, self.y + 4)
        self._bg.size = (self.width - 8, self.height - 8)

    def on_release(self):
        node = self.parent
        while node is not None and not hasattr(node, "go"):
            node = node.parent
        if node is not None and node.current != self._target:
            node.fade_to(self._target)

def screen_shell(content_widget, title: str, back: str | None = None,
                 active_nav: str = "home", show_bottom_nav: bool = True):
    bg = AnimatedBackground(density=18)
    root = BoxLayout(orientation="vertical")
    root.add_widget(TopBar(title, back_screen=back))
    root.add_widget(content_widget)
    if show_bottom_nav and Session.is_authenticated():
        root.add_widget(BottomNav(active=active_nav))
    bg.add_widget(root)
    return bg
