from datetime import date, timedelta
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton, StatusChip
from ..auth import Session
from ..database.repos import SubscriptionRepo, UserRepo, SubscriptionRequestRepo
from ._layout import screen_shell

class SubscriptionsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="subscriptions", **kw)

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=12,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(Label(text="[b]ТАРИФИ[/b]", markup=True,
                                 color=theme.NEON_CYAN, font_size="13sp",
                                 size_hint_y=None, height=20,
                                 halign="left", valign="middle"))
        for t in SubscriptionRepo.types():
            content.add_widget(self._type_card(t))

        if Session.role in ("admin", "head_trainer", "director", "accountant"):
            content.add_widget(Label(text="[b]АКТИВНІ АБОНЕМЕНТИ[/b]", markup=True,
                                     color=theme.NEON_CYAN, font_size="13sp",
                                     size_hint_y=None, height=20,
                                     halign="left", valign="middle"))
            for s in SubscriptionRepo.all_with_clients():
                content.add_widget(self._admin_row(s))
        else:
            pending = [r for r in SubscriptionRequestRepo.pending_for_client(Session.user_id)
                       if r["status"] == "pending"]
            if pending:
                content.add_widget(Label(text="[b]ЗАЯВКИ НА РОЗГЛЯДІ[/b]", markup=True,
                                         color=theme.WARN_AMBER, font_size="13sp",
                                         size_hint_y=None, height=20,
                                         halign="left", valign="middle"))
                for r in pending:
                    content.add_widget(self._pending_request(r))

            content.add_widget(Label(text="[b]МОЇ АБОНЕМЕНТИ[/b]", markup=True,
                                     color=theme.NEON_CYAN, font_size="13sp",
                                     size_hint_y=None, height=20,
                                     halign="left", valign="middle"))
            for s in SubscriptionRepo.all_for_client(Session.user_id):
                content.add_widget(self._client_row(s))

        scroll.add_widget(content)
        active = "subs" if Session.role == "client" else "home"
        shell = screen_shell(scroll, title="Абонементи", back=None, active_nav=active)
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _type_card(self, t):
        card = GlassCard(size_hint_y=None, height=98, padding=14, spacing=4)
        top = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=28)
        title = Label(text=f"[b]{t['name']}[/b]", markup=True,
                      color=theme.TEXT_PRIMARY, font_size="16sp",
                      halign="left", valign="middle")
        title.bind(size=lambda *a: setattr(title, "text_size", title.size))
        price = Label(text=f"[b]{t['price']:.0f}₴[/b]", markup=True,
                      color=theme.NEON_CYAN, font_size="17sp",
                      size_hint_x=None, width=110, halign="right", valign="middle")
        price.bind(size=lambda *a: setattr(price, "text_size", price.size))
        top.add_widget(title)
        top.add_widget(price)
        card.add_widget(top)

        bal = f"{t['visit_limit']} відвідувань" if t["visit_limit"] else "Безлімітний"
        meta = Label(text=f"{t['duration_days']} днів  •  {bal}  •  заморозка {t['freeze_days_allowed']} дн.",
                     color=theme.TEXT_SECONDARY, font_size="11sp", size_hint_y=None, height=18,
                     halign="left", valign="middle")
        meta.bind(size=lambda *a: setattr(meta, "text_size", meta.size))
        card.add_widget(meta)

        if Session.role == "client":
            buy = NeonButton(text="ПРИДБАТИ", size_hint_y=None, height=36)
            buy.bind(on_release=lambda *_, tt=t: self._confirm_buy(tt))
            card.add_widget(buy)
            card.height = 130
        return card

    def _confirm_buy(self, t):
        bal = f"{t['visit_limit']} відвідувань" if t["visit_limit"] else "Безлімітний"
        body = BoxLayout(orientation="vertical", padding=14, spacing=8)
        body.add_widget(Label(
            text="[b]Підтвердження покупки[/b]", markup=True,
            color=theme.NEON_CYAN, font_size="15sp",
            size_hint_y=None, height=24,
            halign="center", valign="middle"))
        name = Label(text=f"[b]{t['name']}[/b]", markup=True,
                     color=theme.TEXT_PRIMARY, font_size="17sp",
                     size_hint_y=None, height=28,
                     halign="center", valign="middle")
        name.bind(size=lambda *a: setattr(name, "text_size", name.size))
        body.add_widget(name)
        meta = Label(
            text=(f"{t['duration_days']} днів  •  {bal}\n"
                  f"Заморозка: {t['freeze_days_allowed']} дн."),
            color=theme.TEXT_SECONDARY, font_size="12sp",
            size_hint_y=None, height=38,
            halign="center", valign="middle")
        meta.bind(size=lambda *a: setattr(meta, "text_size", meta.size))
        body.add_widget(meta)
        price = Label(text=f"[b]{t['price']:.0f}₴[/b]", markup=True,
                      color=theme.ENERGY_GREEN, font_size="26sp",
                      size_hint_y=None, height=40,
                      halign="center", valign="middle")
        price.bind(size=lambda *a: setattr(price, "text_size", price.size))
        body.add_widget(price)
        body.add_widget(Label(
            text="Заявка буде відправлена адміністратору\nна підтвердження.",
            color=theme.TEXT_MUTED, font_size="11sp",
            size_hint_y=None, height=32,
            halign="center", valign="middle"))

        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=46)
        cancel = GhostButton(text="ВІДХИЛИТИ")
        confirm = NeonButton(text="ПІДТВЕРДИТИ")
        actions.add_widget(cancel)
        actions.add_widget(confirm)
        body.add_widget(actions)

        popup = Popup(title="", content=body, size_hint=(0.9, None), height=360,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            SubscriptionRequestRepo.create(Session.user_id, t["type_id"])
            popup.dismiss()
            self.on_enter()
        confirm.bind(on_release=do)
        popup.open()

    def _pending_request(self, r):
        card = GlassCard(size_hint_y=None, height=64, padding=12, spacing=4,
                         border_color=[*theme.WARN_AMBER[:3], 0.4])
        top = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=24)
        t = Label(text=f"[b]{r['type_name']}[/b]", markup=True,
                  color=theme.TEXT_PRIMARY, font_size="14sp",
                  halign="left", valign="middle",
                  shorten=True, shorten_from="right")
        t.bind(size=lambda *a: setattr(t, "text_size", t.size))
        top.add_widget(t)
        price = Label(text=f"{r['price']:.0f}₴", color=theme.WARN_AMBER, font_size="13sp",
                      size_hint_x=None, width=80, halign="right", valign="middle")
        price.bind(size=lambda *a: setattr(price, "text_size", price.size))
        top.add_widget(price)
        card.add_widget(top)
        meta = Label(text=f"Заявка від {r['requested_at'][:16]}  •  очікує підтвердження",
                     color=theme.TEXT_MUTED, font_size="11sp",
                     size_hint_y=None, height=18,
                     halign="left", valign="middle",
                     shorten=True, shorten_from="right")
        meta.bind(size=lambda *a: setattr(meta, "text_size", meta.size))
        card.add_widget(meta)
        return card

    def _client_row(self, s):
        card = GlassCard(size_hint_y=None, height=68, padding=12, spacing=8)
        top = BoxLayout(orientation="horizontal", spacing=10)
        t = Label(text=f"[b]{s['type_name']}[/b]\n[size=11sp]{s['start_date']} — {s['end_date']}[/size]",
                  markup=True, color=theme.TEXT_PRIMARY, font_size="14sp",
                  halign="left", valign="middle")
        t.bind(size=lambda *a: setattr(t, "text_size", t.size))
        top.add_widget(t)
        top.add_widget(StatusChip(status=s["status"]))
        card.add_widget(top)
        return card

    def _admin_row(self, s):
        card = GlassCard(size_hint_y=None, padding=12, spacing=6)
        card.bind(minimum_height=card.setter("height"))
        top = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=None, height=34)
        info = Label(text=f"[b]{s['full_name']}[/b]   [size=11sp][color=#9EA8CE]"
                          f"{s['type_name']}  •  до {s['end_date']}[/color][/size]",
                     markup=True, color=theme.TEXT_PRIMARY, font_size="13sp",
                     halign="left", valign="middle",
                     shorten=True, shorten_from="right")
        info.bind(size=lambda *a: setattr(info, "text_size", info.size))
        top.add_widget(info)
        top.add_widget(StatusChip(status=s["status"]))
        card.add_widget(top)

        actions = BoxLayout(orientation="horizontal", spacing=6,
                            size_hint_y=None, height=34, padding=[0, 2, 0, 0])
        if s["status"] == "active":
            freeze = GhostButton(text="❋ ЗАМОРОЗИТИ", height=32)
            freeze.bind(on_release=lambda *_, sid=s["sub_id"]:
                        (SubscriptionRepo.freeze(sid), self.on_enter()))
            actions.add_widget(freeze)
        elif s["status"] == "frozen":
            unfreeze = NeonButton(text="▶ РОЗМОРОЗИТИ", height=32)
            unfreeze.bind(on_release=lambda *_, sid=s["sub_id"]:
                          (SubscriptionRepo.unfreeze(sid), self.on_enter()))
            actions.add_widget(unfreeze)

        if s["status"] != "cancelled":
            cancel = GhostButton(text="АНУЛЮВАТИ", height=32)
            cancel.bind(on_release=lambda *_, ss=s: self._confirm_cancel(ss))
            actions.add_widget(cancel)

        delete = GhostButton(text="ВИДАЛИТИ", height=32)
        delete.bind(on_release=lambda *_, ss=s: self._confirm_delete_sub(ss))
        actions.add_widget(delete)
        card.add_widget(actions)
        return card

    def _confirm_cancel(self, s):
        body = BoxLayout(orientation="vertical", padding=14, spacing=10)
        msg = Label(
            text=(f"Анулювати абонемент «{s['type_name']}» "
                  f"клієнта «{s['full_name']}»?\n"
                  "Він стане неактивним, але історія збережеться."),
            color=theme.TEXT_PRIMARY, font_size="13sp",
            halign="center", valign="middle")
        msg.bind(size=lambda *a: setattr(msg, "text_size", msg.size))
        body.add_widget(msg)
        row = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=None, height=44)
        cancel = GhostButton(text="НАЗАД")
        confirm = NeonButton(text="АНУЛЮВАТИ")
        row.add_widget(cancel)
        row.add_widget(confirm)
        body.add_widget(row)
        popup = Popup(title="Анулювання абонементу", content=body,
                      size_hint=(0.9, None), height=240,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.WARN_AMBER,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            SubscriptionRepo.cancel(s["sub_id"])
            popup.dismiss()
            self.on_enter()
        confirm.bind(on_release=do)
        popup.open()

    def _confirm_delete_sub(self, s):
        body = BoxLayout(orientation="vertical", padding=14, spacing=10)
        msg = Label(
            text=(f"Видалити абонемент «{s['type_name']}» "
                  f"клієнта «{s['full_name']}» назавжди?\n"
                  "Цю дію не можна відмінити."),
            color=theme.TEXT_PRIMARY, font_size="13sp",
            halign="center", valign="middle")
        msg.bind(size=lambda *a: setattr(msg, "text_size", msg.size))
        body.add_widget(msg)
        row = BoxLayout(orientation="horizontal", spacing=8,
                        size_hint_y=None, height=44)
        cancel = GhostButton(text="НАЗАД")
        confirm = NeonButton(text="ВИДАЛИТИ")
        row.add_widget(cancel)
        row.add_widget(confirm)
        body.add_widget(row)
        popup = Popup(title="Видалення абонементу", content=body,
                      size_hint=(0.9, None), height=240,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.DANGER_RED,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            SubscriptionRepo.delete(s["sub_id"])
            popup.dismiss()
            self.on_enter()
        confirm.bind(on_release=do)
        popup.open()
