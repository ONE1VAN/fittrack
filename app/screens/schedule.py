from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton, StatusChip
from ..widgets import CheckIcon, CrossIcon, MinusIcon
from ..auth import Session
from ..database.repos import ScheduleRepo
from ._layout import screen_shell


def _strip_role(name: str) -> str:
    if not name:
        return ""
    s = name.strip()
    for prefix in ("Тренер ", "тренер "):
        if s.startswith(prefix):
            return s[len(prefix):]
    return s


class ScheduleScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="schedule", **kw)

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=12,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        if Session.role == "trainer":
            classes = ScheduleRepo.trainer_schedule(Session.user_id)
            my_bookings = set()
            title = "Мій розклад"
        else:
            classes = ScheduleRepo.upcoming_classes()
            my_bookings = {b["class_id"] for b in ScheduleRepo.client_bookings(Session.user_id)
                           if b["bk_status"] != "cancelled"}
            title = "Розклад занять"

        if not classes:
            content.add_widget(self._empty())
        else:
            current_date = None
            for c in classes:
                dt = datetime.fromisoformat(c["start_time"])
                d_str = dt.strftime("%A, %d %B")
                if d_str != current_date:
                    current_date = d_str
                    content.add_widget(self._date_header(d_str))
                content.add_widget(self._class_card(c, booked=c["class_id"] in my_bookings))

        scroll.add_widget(content)
        shell = screen_shell(scroll, title=title, active_nav="schedule")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    @staticmethod
    def _date_header(text: str):
        l = Label(text=f"[b]{text.upper()}[/b]", markup=True,
                  color=theme.NEON_CYAN, font_size="12sp",
                  size_hint_y=None, height=24,
                  halign="left", valign="middle")
        l.bind(size=lambda *a: setattr(l, "text_size", l.size))
        return l

    @staticmethod
    def _empty():
        c = GlassCard(size_hint_y=None, height=120)
        c.add_widget(Label(text="Немає запланованих занять",
                           color=theme.TEXT_SECONDARY, font_size=theme.SIZE_BODY))
        return c

    def _class_card(self, c, booked: bool):

        card = GlassCard(size_hint_y=None, padding=14, spacing=6,
                         orientation="vertical")
        card.bind(minimum_height=card.setter("height"))

        dt = datetime.fromisoformat(c["start_time"])
        end = datetime.fromisoformat(c["end_time"])


        top = BoxLayout(orientation="horizontal", spacing=10,
                        size_hint_y=None)
        top.bind(minimum_height=top.setter("height"))

        time_lbl = Label(
            text=f"[b]{dt.strftime('%H:%M')}—{end.strftime('%H:%M')}[/b]",
            markup=True, color=theme.NEON_CYAN, font_size="13sp",
            size_hint=(None, None), size=(105, 30),
            halign="left", valign="top")
        time_lbl.bind(size=lambda *a: setattr(time_lbl, "text_size", time_lbl.size))

        title = Label(text=c["title"],
                      color=theme.TEXT_PRIMARY, font_size="15sp", bold=True,
                      halign="left", valign="top",
                      size_hint_y=None)
        title.bind(
            width=lambda *a: setattr(title, "text_size", (title.width, None)),
            texture_size=lambda *a: setattr(title, "height",
                                            max(title.texture_size[1], 22)))

        top.add_widget(time_lbl)
        top.add_widget(title)
        card.add_widget(top)


        trainer = _strip_role(c.get("trainer", "")) if hasattr(c, "get") else _strip_role(c["trainer"])
        line1 = Label(
            text=f"{c['category']}  •  {c['room']}",
            color=theme.TEXT_SECONDARY, font_size="11sp",
            halign="left", valign="middle",
            size_hint_y=None, height=18)
        line1.bind(size=lambda *a: setattr(line1, "text_size", line1.size))
        card.add_widget(line1)


        line2 = Label(
            text=f"Тренер {trainer}  •  {c['booked_count']}/{c['capacity']} зайнято",
            color=theme.TEXT_SECONDARY, font_size="11sp",
            halign="left", valign="middle",
            size_hint_y=None, height=18,
            shorten=True, shorten_from="right")
        line2.bind(size=lambda *a: setattr(line2, "text_size", line2.size))
        card.add_widget(line2)


        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=40,
                            padding=[0, 4, 0, 0])
        if Session.role == "client":
            if booked:
                btn = GhostButton(text="ВІДМІНИТИ", height=36)
                btn.bind(on_release=lambda *_: self._cancel(c["class_id"], card))
            else:
                btn = NeonButton(text="ЗАПИСАТИСЬ", height=36)
                btn.bind(on_release=lambda *_: self._book(c["class_id"], card))
            actions.add_widget(Label())
            actions.add_widget(btn)
        elif Session.role == "trainer":
            btn = NeonButton(text=f"УЧАСНИКИ ({c['booked_count']})", height=36)
            btn.bind(on_release=lambda *_, cid=c["class_id"]: self._show_participants(cid))
            del_btn = GhostButton(text="ВИДАЛИТИ", height=36, size_hint_x=None, width=110)
            del_btn.bind(on_release=lambda *_, cid=c["class_id"], title=c["title"]:
                         self._confirm_delete_class(cid, title))
            actions.add_widget(Label())
            actions.add_widget(del_btn)
            actions.add_widget(btn)
        card.add_widget(actions)
        return card

    def _book(self, class_id: int, card):
        ok = ScheduleRepo.book(class_id, Session.user_id)
        try:
            card.flash(theme.ENERGY_GREEN if ok else theme.DANGER_RED)
        except Exception:
            pass
        Animation(opacity=0.5, d=0.15).start(card)
        from kivy.clock import Clock
        Clock.schedule_once(lambda *_: self.on_enter(), 0.4)

    def _cancel(self, class_id: int, card):
        ScheduleRepo.cancel_booking(class_id, Session.user_id)
        try:
            card.flash(theme.WARN_AMBER)
        except Exception:
            pass
        from kivy.clock import Clock
        Clock.schedule_once(lambda *_: self.on_enter(), 0.4)

    def _show_participants(self, class_id: int):
        from kivy.uix.popup import Popup
        rows = ScheduleRepo.class_participants(class_id)
        body = BoxLayout(orientation="vertical", padding=12, spacing=6)
        hint = Label(
            text="[i]присутній   /   пропустив   /   виключити[/i]",
            markup=True, color=theme.TEXT_MUTED, font_size="10sp",
            size_hint_y=None, height=18,
            halign="left", valign="middle")
        hint.bind(size=lambda *a: setattr(hint, "text_size", hint.size))
        body.add_widget(hint)
        if not rows:
            body.add_widget(Label(text="Поки немає записаних",
                                  color=theme.TEXT_MUTED,
                                  size_hint_y=None, height=32))
        for r in rows:
            line = BoxLayout(orientation="horizontal", spacing=6,
                             size_hint_y=None, height=44)
            l = Label(text=r["full_name"], color=theme.TEXT_PRIMARY,
                      font_size="13sp", halign="left", valign="middle",
                      shorten=True, shorten_from="right")
            l.bind(size=lambda *a, w=l: setattr(w, "text_size", w.size))
            line.add_widget(l)
            line.add_widget(StatusChip(status=r["status"]))
            attend = CheckIcon(size=(36, 36))
            no_show = CrossIcon(size=(36, 36))
            kick = MinusIcon(size=(36, 36))
            attend.bind(on_release=lambda *_, cid=class_id, uid=r["user_id"]:
                        (ScheduleRepo.mark_attendance(cid, uid, True),
                         self._reload_participants(class_id)))
            no_show.bind(on_release=lambda *_, cid=class_id, uid=r["user_id"]:
                         (ScheduleRepo.mark_attendance(cid, uid, False),
                          self._reload_participants(class_id)))
            kick.bind(on_release=lambda *_, cid=class_id, uid=r["user_id"],
                      name=r["full_name"]:
                      self._confirm_kick(cid, uid, name))
            line.add_widget(attend)
            line.add_widget(no_show)
            line.add_widget(kick)
            body.add_widget(line)
        close = GhostButton(text="ЗАКРИТИ", size_hint_y=None, height=42)
        body.add_widget(close)
        popup = Popup(title="Учасники заняття", content=body,
                      size_hint=(0.96, None),
                      height=min(580, 160 + max(1, len(rows)) * 52),
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        close.bind(on_release=lambda *_: popup.dismiss())
        self._participants_popup = popup
        popup.open()

    def _reload_participants(self, class_id: int):
        try:
            self._participants_popup.dismiss()
        except Exception:
            pass
        self._show_participants(class_id)

    def _confirm_delete_class(self, class_id: int, title: str):
        from kivy.uix.popup import Popup
        body = BoxLayout(orientation="vertical", padding=14, spacing=10)
        msg = Label(
            text=f"Видалити заняття «{title}»?\nУсі бронювання будуть скасовані.",
            color=theme.TEXT_PRIMARY, font_size="14sp",
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
                      size_hint=(0.86, None), height=210,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.DANGER_RED,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            ScheduleRepo.delete_class(class_id)
            popup.dismiss()
            self.on_enter()
        confirm.bind(on_release=do)
        popup.open()

    def _confirm_kick(self, class_id: int, client_id: int, name: str):
        from kivy.uix.popup import Popup
        body = BoxLayout(orientation="vertical", padding=14, spacing=10)
        body.add_widget(Label(
            text=f"Виключити «{name}» з цього заняття?",
            color=theme.TEXT_PRIMARY, font_size="14sp",
            halign="center", valign="middle"))
        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=44)
        cancel = GhostButton(text="СКАСУВАТИ")
        confirm = NeonButton(text="ВИКЛЮЧИТИ")
        actions.add_widget(cancel)
        actions.add_widget(confirm)
        body.add_widget(actions)
        popup = Popup(title="Підтвердження", content=body,
                      size_hint=(0.86, None), height=190,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_MAGENTA,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            ScheduleRepo.kick_client(class_id, client_id)
            popup.dismiss()
            self._reload_participants(class_id)
        confirm.bind(on_release=do)
        popup.open()
