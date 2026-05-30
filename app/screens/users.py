from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton
from ..auth import Session
from ..database.repos import UserRepo
from ._layout import screen_shell


ROLE_LABELS_UA = {
    "admin":   "Адмін",
    "trainer": "Тренер",
    "client":  "Клієнт",
}

ROLE_COLORS = {
    "admin":   theme.NEON_MAGENTA,
    "trainer": theme.NEON_CYAN,
    "client":  theme.ENERGY_GREEN,
}


class UsersScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="users", **kw)

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=10,
                            padding=[14, 12, 14, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        users = UserRepo.all_with_roles()

        by_role: dict[str, list] = {}
        for u in users:
            by_role.setdefault(u["role_name"], []).append(u)

        for role in sorted(by_role.keys(), key=lambda r: (r != "client", r)):
            label = ROLE_LABELS_UA.get(role, role).upper()
            content.add_widget(Label(
                text=f"[b]{label}  ({len(by_role[role])})[/b]",
                markup=True,
                color=ROLE_COLORS.get(role, theme.NEON_CYAN),
                font_size="12sp",
                size_hint_y=None, height=22,
                halign="left", valign="middle"))
            for u in by_role[role]:
                content.add_widget(self._user_card(u))

        scroll.add_widget(content)
        shell = screen_shell(scroll, title="Користувачі",
                             back="home_admin", active_nav="home")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _user_card(self, u):
        card = GlassCard(size_hint_y=None, padding=12, spacing=4)
        card.bind(minimum_height=card.setter("height"))

        top = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=None, height=24)
        name = Label(text=f"[b]{u['full_name']}[/b]", markup=True,
                     color=theme.TEXT_PRIMARY, font_size="14sp",
                     halign="left", valign="middle",
                     shorten=True, shorten_from="right")
        name.bind(size=lambda *a: setattr(name, "text_size", name.size))
        top.add_widget(name)
        role_lbl = Label(
            text=ROLE_LABELS_UA.get(u["role_name"], u["role_name"]),
            color=ROLE_COLORS.get(u["role_name"], theme.NEON_CYAN),
            font_size="11sp", bold=True,
            size_hint_x=None, width=110,
            halign="right", valign="middle")
        role_lbl.bind(size=lambda *a: setattr(role_lbl, "text_size", role_lbl.size))
        top.add_widget(role_lbl)
        card.add_widget(top)

        meta_text = u["email"]
        if u["phone"]:
            meta_text += f"  •  {u['phone']}"
        if u["card_id_skud"]:
            meta_text += f"  •  {u['card_id_skud']}"
        meta = Label(text=meta_text, color=theme.TEXT_SECONDARY,
                     font_size="11sp",
                     size_hint_y=None, height=18,
                     halign="left", valign="middle",
                     shorten=True, shorten_from="right")
        meta.bind(size=lambda *a: setattr(meta, "text_size", meta.size))
        card.add_widget(meta)

        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=38, padding=[0, 4, 0, 0])
        role_btn = GhostButton(text="ЗМІНИТИ РОЛЬ", height=34)
        role_btn.bind(on_release=lambda *_, uu=u: self._change_role_dialog(uu))
        del_btn = GhostButton(text="ВИДАЛИТИ", height=34)
        del_btn.bind(on_release=lambda *_, uu=u: self._confirm_delete(uu))

        if u["user_id"] == Session.user_id:
            del_btn.disabled = True
            del_btn.text = "ЦЕ ВИ"
        actions.add_widget(role_btn)
        actions.add_widget(del_btn)
        card.add_widget(actions)
        return card

    def _change_role_dialog(self, u):
        body = BoxLayout(orientation="vertical", padding=14, spacing=8)
        body.add_widget(Label(
            text=f"[b]Роль для «{u['full_name']}»[/b]",
            markup=True, color=theme.NEON_CYAN, font_size="14sp",
            size_hint_y=None, height=24,
            halign="center", valign="middle"))

        chosen = {"role": u["role_name"]}
        chips = []

        def pick(role_name):
            chosen["role"] = role_name
            for ch in chips:
                ch.set_active(ch.role_name == role_name)

        grid = BoxLayout(orientation="vertical", spacing=6,
                         size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        row = BoxLayout(orientation="horizontal", spacing=6,
                        size_hint_y=None, height=40)
        per_row = 0
        for r in UserRepo.roles():
            chip = _RoleChip(r["role_name"],
                             active=(r["role_name"] == chosen["role"]),
                             on_choose=pick)
            chips.append(chip)
            row.add_widget(chip)
            per_row += 1
            if per_row == 3:
                grid.add_widget(row)
                row = BoxLayout(orientation="horizontal", spacing=6,
                                size_hint_y=None, height=40)
                per_row = 0
        if per_row:

            while per_row < 3:
                row.add_widget(Label())
                per_row += 1
            grid.add_widget(row)
        body.add_widget(grid)

        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=44)
        cancel = GhostButton(text="СКАСУВАТИ")
        save = NeonButton(text="ЗБЕРЕГТИ")
        actions.add_widget(cancel)
        actions.add_widget(save)
        body.add_widget(actions)

        popup = Popup(title="Зміна ролі", content=body,
                      size_hint=(0.92, None), height=340,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            UserRepo.set_role(u["user_id"], chosen["role"])
            popup.dismiss()
            self.on_enter()
        save.bind(on_release=do)
        popup.open()

    def _confirm_delete(self, u):
        body = BoxLayout(orientation="vertical", padding=14, spacing=10)
        msg = Label(
            text=(f"Видалити «{u['full_name']}»?\n"
                  f"Усі його бронювання, абонементи та коментарі будуть видалені."),
            color=theme.TEXT_PRIMARY, font_size="13sp",
            halign="center", valign="middle")
        msg.bind(size=lambda *a: setattr(msg, "text_size", msg.size))
        body.add_widget(msg)
        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=44)
        cancel = GhostButton(text="СКАСУВАТИ")
        confirm = NeonButton(text="ВИДАЛИТИ")
        actions.add_widget(cancel)
        actions.add_widget(confirm)
        body.add_widget(actions)
        popup = Popup(title="Підтвердження", content=body,
                      size_hint=(0.88, None), height=220,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.DANGER_RED,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            UserRepo.delete(u["user_id"])
            popup.dismiss()
            self.on_enter()
        confirm.bind(on_release=do)
        popup.open()


class _RoleChip(ButtonBehavior, Label):
    def __init__(self, role_name: str, active: bool, on_choose, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 36)
        kw.setdefault("font_size", "11sp")
        kw.setdefault("bold", True)
        super().__init__(text=ROLE_LABELS_UA.get(role_name, role_name), **kw)
        self.role_name = role_name
        self._on_choose = on_choose
        active_bg = list(theme.NEON_CYAN[:3]) + [0.18]
        with self.canvas.before:
            self._bg_c = Color(*(active_bg if active else (1, 1, 1, 0.04)))
            self._bg = RoundedRectangle(radius=[12])
            self._brd_c = Color(*(list(theme.NEON_CYAN) if active else (1, 1, 1, 0.12)))
            self._brd = Line(width=1.2, rounded_rectangle=(0, 0, 0, 0, 12))
        self.color = theme.NEON_CYAN if active else theme.TEXT_SECONDARY
        self.bind(size=self._sync, pos=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._brd.rounded_rectangle = (*self.pos, *self.size, 12)

    def set_active(self, active: bool):
        active_bg = list(theme.NEON_CYAN[:3]) + [0.18]
        self._bg_c.rgba = active_bg if active else (1, 1, 1, 0.04)
        self._brd_c.rgba = list(theme.NEON_CYAN) if active else (1, 1, 1, 0.12)
        self.color = theme.NEON_CYAN if active else theme.TEXT_SECONDARY

    def on_release(self):
        self._on_choose(self.role_name)
