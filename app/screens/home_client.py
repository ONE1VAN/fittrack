from datetime import date
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.clock import Clock

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton, StatusChip, PulseRing
from ..auth import Session
from ..database.repos import SubscriptionRepo, ScheduleRepo
from ._layout import screen_shell

class HomeClientScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="home_client", **kw)

    def on_enter(self):

        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=14,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        sub = SubscriptionRepo.active_for_client(Session.user_id)
        content.add_widget(self._hero_card(sub))

        actions = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=54)
        b1 = NeonButton(text="▣  ЗАПИСАТИСЬ")
        b1.bind(on_release=lambda *_: self.manager.go("schedule"))
        b2 = GhostButton(text="▶  ВІДЕО")
        b2.bind(on_release=lambda *_: self.manager.go("video_feed"))
        actions.add_widget(b1)
        actions.add_widget(b2)
        content.add_widget(actions)

        content.add_widget(self._bookings_section())

        scroll.add_widget(content)
        shell = screen_shell(scroll, title=f"Привіт, {Session.full_name.split()[0]}!",
                             active_nav="home")
        self.add_widget(shell)

        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _hero_card(self, sub):
        card = GlassCard(size_hint_y=None, height=240, padding=18, spacing=10)
        if sub is None:
            card.add_widget(Label(text="У вас немає активного абонементу",
                                  color=theme.TEXT_SECONDARY, font_size=theme.SIZE_H2))
            buy = NeonButton(text="ПРИДБАТИ АБОНЕМЕНТ")
            buy.bind(on_release=lambda *_: self.manager.go("subscriptions"))
            card.add_widget(buy)
            return card

        top = BoxLayout(size_hint_y=None, height=32, spacing=10)
        title = Label(text=f"[b]{sub['type_name']}[/b]", markup=True,
                      color=theme.TEXT_PRIMARY, font_size=theme.SIZE_H2,
                      halign="left", valign="middle")
        title.bind(size=lambda *a: setattr(title, "text_size", title.size))
        top.add_widget(title)
        top.add_widget(StatusChip(status=sub["status"]))
        card.add_widget(top)

        body = BoxLayout(orientation="horizontal", spacing=18)

        end = date.fromisoformat(sub["end_date"])
        start = date.fromisoformat(sub["start_date"])
        today = date.today()
        total_days = (end - start).days or 1
        days_left = max(0, (end - today).days)
        progress = max(0.0, min(1.0, days_left / total_days))

        ring_color = list(theme.STATUS_COLORS.get(sub["status"], theme.NEON_CYAN))
        ring_wrap = FloatLayout(size_hint_x=None, width=160)
        ring = PulseRing(size=(150, 150), ring_color=ring_color,
                         pos_hint={"center_x": 0.5, "center_y": 0.5})
        ring_wrap.add_widget(ring)
        big_text = Label(
            text=f"[b][size=28sp]{days_left}[/size][/b]\n[size=11sp]днів[/size]",
            markup=True, color=theme.TEXT_PRIMARY, halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.5})
        ring_wrap.add_widget(big_text)
        body.add_widget(ring_wrap)
        Clock.schedule_once(lambda *_: ring.animate_to(progress), 0.05)

        stats = BoxLayout(orientation="vertical", spacing=6)
        stats.add_widget(self._stat("До", end.strftime("%d.%m.%Y"), theme.NEON_CYAN))
        if sub["balance"] is not None:
            stats.add_widget(self._stat("Залишилось візитів", str(sub["balance"]), theme.ENERGY_GREEN))
        else:
            stats.add_widget(self._stat("Тип", "Безлімітний", theme.ENERGY_GREEN))
        stats.add_widget(self._stat("Freeze use", f"{sub['freeze_days_used']} / {sub['freeze_days_allowed']}",
                                    theme.WARN_AMBER))
        body.add_widget(stats)
        card.add_widget(body)
        return card

    @staticmethod
    def _stat(label: str, value: str, color):
        box = BoxLayout(orientation="vertical", spacing=2, size_hint_y=None, height=48)
        l = Label(text=label, color=theme.TEXT_MUTED, font_size="11sp",
                  size_hint_y=None, height=14, halign="left", valign="middle")
        l.bind(size=lambda *a: setattr(l, "text_size", l.size))
        v = Label(text=f"[b]{value}[/b]", markup=True, color=color,
                  font_size="17sp", size_hint_y=None, height=22,
                  halign="left", valign="middle")
        v.bind(size=lambda *a: setattr(v, "text_size", v.size))
        box.add_widget(l)
        box.add_widget(v)
        return box

    def _bookings_section(self):
        wrap = GlassCard(size_hint_y=None, padding=14, spacing=8)
        wrap.add_widget(Label(text="[b]МОЇ ЗАПИСИ[/b]", markup=True,
                              color=theme.NEON_CYAN, font_size="13sp",
                              size_hint_y=None, height=20,
                              halign="left", valign="middle"))
        bookings = ScheduleRepo.client_bookings(Session.user_id)
        if not bookings:
            wrap.add_widget(Label(text="Ви ще не записалися на жодне заняття",
                                  color=theme.TEXT_MUTED, font_size="13sp",
                                  size_hint_y=None, height=24))
        else:
            for b in bookings[:5]:
                wrap.add_widget(self._booking_row(b))
        wrap.height = 60 + max(1, min(len(bookings), 5)) * 56
        return wrap

    @staticmethod
    def _booking_row(b):
        from datetime import datetime
        row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=52,
                        padding=[10, 0, 10, 0])
        dt = datetime.fromisoformat(b["start_time"])
        when = Label(text=f"[b]{dt.strftime('%d.%m')}\n{dt.strftime('%H:%M')}[/b]",
                     markup=True, color=theme.NEON_CYAN, font_size="13sp",
                     size_hint_x=None, width=56, halign="center", valign="middle")
        when.bind(size=lambda *a: setattr(when, "text_size", when.size))
        info = BoxLayout(orientation="vertical")
        t = Label(text=b["title"], color=theme.TEXT_PRIMARY, font_size="14sp",
                  halign="left", valign="middle")
        t.bind(size=lambda *a: setattr(t, "text_size", t.size))
        meta = Label(text=f"{b['category']}  •  {b['trainer']}",
                     color=theme.TEXT_SECONDARY, font_size="11sp",
                     halign="left", valign="middle")
        meta.bind(size=lambda *a: setattr(meta, "text_size", meta.size))
        info.add_widget(t)
        info.add_widget(meta)
        row.add_widget(when)
        row.add_widget(info)
        row.add_widget(StatusChip(status=b["bk_status"]))
        return row
