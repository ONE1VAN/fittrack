from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton
from ..auth import Session
from ..database.repos import SubscriptionRequestRepo
from ._layout import screen_shell


class SubscriptionRequestsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="sub_requests", **kw)

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=12,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        pending = SubscriptionRequestRepo.all_with_clients(status="pending")
        resolved = SubscriptionRequestRepo.all_with_clients(status=None)
        resolved = [r for r in resolved if r["status"] != "pending"][:10]

        content.add_widget(Label(
            text=f"[b]ОЧІКУЮТЬ ({len(pending)})[/b]", markup=True,
            color=theme.WARN_AMBER, font_size="13sp",
            size_hint_y=None, height=22,
            halign="left", valign="middle"))
        if not pending:
            empty = GlassCard(size_hint_y=None, height=72)
            empty.add_widget(Label(text="Немає нових заявок",
                                   color=theme.TEXT_MUTED,
                                   font_size="13sp"))
            content.add_widget(empty)
        else:
            for r in pending:
                content.add_widget(self._request_card(r, pending_view=True))

        if resolved:
            content.add_widget(Label(
                text="[b]ОСТАННІ РІШЕННЯ[/b]", markup=True,
                color=theme.TEXT_SECONDARY, font_size="12sp",
                size_hint_y=None, height=22,
                halign="left", valign="middle"))
            for r in resolved:
                content.add_widget(self._request_card(r, pending_view=False))

        scroll.add_widget(content)
        shell = screen_shell(scroll, title="Заявки на абонементи",
                             back="home_admin", active_nav="home")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _request_card(self, r, pending_view: bool):
        accent = theme.WARN_AMBER if pending_view else (
            theme.ENERGY_GREEN if r["status"] == "approved" else theme.DANGER_RED)
        card = GlassCard(size_hint_y=None, padding=14, spacing=6,
                         border_color=[*accent[:3], 0.4])
        card.bind(minimum_height=card.setter("height"))

        top = BoxLayout(orientation="horizontal", spacing=10,
                        size_hint_y=None, height=26)
        name = Label(text=f"[b]{r['full_name']}[/b]", markup=True,
                     color=theme.TEXT_PRIMARY, font_size="15sp",
                     halign="left", valign="middle",
                     shorten=True, shorten_from="right")
        name.bind(size=lambda *a: setattr(name, "text_size", name.size))
        top.add_widget(name)
        price = Label(text=f"[b]{r['price']:.0f}₴[/b]", markup=True,
                      color=accent, font_size="15sp",
                      size_hint_x=None, width=90,
                      halign="right", valign="middle")
        price.bind(size=lambda *a: setattr(price, "text_size", price.size))
        top.add_widget(price)
        card.add_widget(top)

        bal = f"{r['visit_limit']} відвідувань" if r["visit_limit"] else "Безлімітний"
        meta = Label(
            text=f"{r['type_name']}  •  {r['duration_days']} дн.  •  {bal}",
            color=theme.TEXT_SECONDARY, font_size="12sp",
            size_hint_y=None, height=18,
            halign="left", valign="middle",
            shorten=True, shorten_from="right")
        meta.bind(size=lambda *a: setattr(meta, "text_size", meta.size))
        card.add_widget(meta)


        phone = r["phone"]
        when = Label(
            text=f"Заявка: {r['requested_at'][:16]}"
                 + (f"  •  {phone}" if phone else ""),
            color=theme.TEXT_MUTED, font_size="11sp",
            size_hint_y=None, height=16,
            halign="left", valign="middle",
            shorten=True, shorten_from="right")
        when.bind(size=lambda *a: setattr(when, "text_size", when.size))
        card.add_widget(when)

        if pending_view:
            actions = BoxLayout(orientation="horizontal", spacing=8,
                                size_hint_y=None, height=42, padding=[0, 6, 0, 0])
            reject = GhostButton(text="ВІДХИЛИТИ", height=36)
            approve = NeonButton(text="ПІДТВЕРДИТИ", height=36)
            reject.bind(on_release=lambda *_, rid=r["req_id"]:
                        (SubscriptionRequestRepo.reject(rid), self.on_enter()))
            approve.bind(on_release=lambda *_, rid=r["req_id"]:
                         (SubscriptionRequestRepo.approve(rid), self.on_enter()))
            actions.add_widget(reject)
            actions.add_widget(approve)
            card.add_widget(actions)
        else:
            badge = Label(
                text=("✓ Підтверджено" if r["status"] == "approved"
                      else "✗ Відхилено"),
                color=accent, font_size="11sp", bold=True,
                size_hint_y=None, height=16,
                halign="left", valign="middle")
            badge.bind(size=lambda *a: setattr(badge, "text_size", badge.size))
            card.add_widget(badge)
        return card
