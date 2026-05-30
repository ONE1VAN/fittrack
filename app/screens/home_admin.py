from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton, StatusChip
from ..auth import Session, hash_password
from ..database.repos import (AnalyticsRepo, PaymentRepo, EquipmentRepo,
                                SubscriptionRepo, SubscriptionRequestRepo,
                                UserRepo)
from ._layout import screen_shell

class HomeAdminScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="home_admin", **kw)

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=14,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        kpi = AnalyticsRepo.kpi_overview()

        row1 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=110)
        row1.add_widget(self._kpi(str(kpi["active_subs"]), "Активні абонементи", theme.NEON_CYAN))
        row1.add_widget(self._kpi(str(kpi["visits_today"]), "Відвідувань сьогодні", theme.ENERGY_GREEN))
        content.add_widget(row1)

        row2 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=110)
        row2.add_widget(self._kpi(f"{kpi['revenue_month']:.0f}₴", "Доход цього місяця", theme.NEON_MAGENTA))
        row2.add_widget(self._kpi(f"{kpi['retention_pct']}%", "Retention rate", theme.WARN_AMBER))
        content.add_widget(row2)

        actions = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=54)
        b1 = NeonButton(text="◆  АБОНЕМЕНТИ")
        b1.bind(on_release=lambda *_: self.manager.go("subscriptions"))
        b2 = GhostButton(text="✦  ОБЛАДНАННЯ")
        b2.bind(on_release=lambda *_: self.manager.go("equipment"))
        actions.add_widget(b1)
        actions.add_widget(b2)
        content.add_widget(actions)

        new_row = BoxLayout(orientation="horizontal", spacing=10,
                            size_hint_y=None, height=54)
        new_btn = NeonButton(text="+  НОВИЙ КЛІЄНТ")
        new_btn.bind(on_release=lambda *_: self._new_client_dialog())
        users_btn = GhostButton(text="●  КОРИСТУВАЧІ")
        users_btn.bind(on_release=lambda *_: self.manager.go("users"))
        new_row.add_widget(new_btn)
        new_row.add_widget(users_btn)
        content.add_widget(new_row)

        pending_req = SubscriptionRequestRepo.count_pending()
        req_row = BoxLayout(orientation="horizontal", spacing=10,
                            size_hint_y=None, height=54)
        req_btn_text = (f"◈  ЗАЯВКИ НА АБОНЕМЕНТИ  ({pending_req})"
                        if pending_req else "◈  ЗАЯВКИ НА АБОНЕМЕНТИ")
        req_btn = NeonButton(text=req_btn_text) if pending_req else GhostButton(text=req_btn_text)
        req_btn.bind(on_release=lambda *_: self.manager.go("sub_requests"))
        req_row.add_widget(req_btn)
        content.add_widget(req_row)

        pays = PaymentRepo.recent(8)
        sec = GlassCard(size_hint_y=None, padding=14, spacing=8)
        sec.add_widget(Label(text="[b]ОСТАННІ ПЛАТЕЖІ[/b]", markup=True,
                             color=theme.NEON_CYAN, font_size="13sp",
                             size_hint_y=None, height=20,
                             halign="left", valign="middle"))
        if not pays:
            sec.add_widget(Label(text="Платежів ще немає",
                                 color=theme.TEXT_MUTED, size_hint_y=None, height=24))
            sec.height = 80
        else:
            for p in pays[:6]:
                sec.add_widget(self._pay_row(p))
            sec.height = 60 + min(len(pays), 6) * 44
        content.add_widget(sec)

        faults = EquipmentRepo.faults()
        if faults:
            fc = GlassCard(size_hint_y=None, padding=14, spacing=8)
            fc.add_widget(Label(text="[b]▲ ПОТРЕБУЮТЬ УВАГИ[/b]", markup=True,
                                color=theme.DANGER_RED, font_size="13sp",
                                size_hint_y=None, height=20,
                                halign="left", valign="middle"))
            for f in faults[:4]:
                row = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=44,
                                padding=[8, 0, 8, 0])
                t = Label(text=f["eq_name"], color=theme.TEXT_PRIMARY, font_size="13sp",
                          halign="left", valign="middle")
                t.bind(size=lambda *a, w=t: setattr(w, "text_size", w.size))
                row.add_widget(t)
                row.add_widget(StatusChip(status="fault"))
                fc.add_widget(row)
            fc.height = 50 + min(len(faults), 4) * 48
            content.add_widget(fc)

        scroll.add_widget(content)
        title = "Адмін-панель" if Session.role == "admin" else f"Панель {Session.role}"
        shell = screen_shell(scroll, title=title, active_nav="home")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _new_client_dialog(self, *_):
        body = BoxLayout(orientation="vertical", padding=12, spacing=8)
        body.add_widget(Label(text="[b]Новий клієнт[/b]", markup=True,
                              color=theme.NEON_CYAN, font_size="15sp",
                              size_hint_y=None, height=22))

        def _field(hint, **kw):
            return TextInput(hint_text=hint, multiline=False,
                             size_hint_y=None, height=42,
                             background_color=[1, 1, 1, 0.06],
                             foreground_color=theme.TEXT_PRIMARY,
                             cursor_color=theme.NEON_CYAN, **kw)

        name_in  = _field("Повне ім'я")
        email_in = _field("Email")
        phone_in = _field("Телефон (необов'язково)")
        pass_in  = _field("Пароль", password=True)
        card_in  = _field("RFID картки", text=UserRepo.next_client_card_id())
        for w in (name_in, email_in, phone_in, pass_in, card_in):
            body.add_widget(w)

        err = Label(text="", color=theme.DANGER_RED, font_size="12sp",
                    size_hint_y=None, height=18)
        body.add_widget(err)

        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=46)
        cancel = GhostButton(text="СКАСУВАТИ")
        save = NeonButton(text="СТВОРИТИ")
        actions.add_widget(cancel)
        actions.add_widget(save)
        body.add_widget(actions)

        popup = Popup(title="", content=body, size_hint=(0.94, None), height=480,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            email = email_in.text.strip()
            name  = name_in.text.strip()
            pw    = pass_in.text.strip()
            if not (name and email and pw):
                err.text = "Заповніть ім'я, email та пароль"
                return
            if "@" not in email:
                err.text = "Некоректний email"
                return
            if UserRepo.by_email(email):
                err.text = "Користувач з таким email вже існує"
                return
            try:
                UserRepo.create(
                    email=email,
                    password_hash=hash_password(pw),
                    role_name="client",
                    full_name=name,
                    phone=phone_in.text.strip() or None,
                    card=card_in.text.strip() or None,
                )
            except Exception as exc:
                err.text = f"Помилка: {exc}"
                return
            popup.dismiss()
            self.on_enter()
        save.bind(on_release=do)
        popup.open()

    @staticmethod
    def _kpi(big: str, label: str, color):
        c = GlassCard(padding=14, spacing=4)
        big_lbl = Label(text=f"[b]{big}[/b]", markup=True, color=color,
                        font_size="26sp", halign="left", valign="middle")
        big_lbl.bind(size=lambda *a: setattr(big_lbl, "text_size", big_lbl.size))
        c.add_widget(big_lbl)
        l = Label(text=label, color=theme.TEXT_SECONDARY, font_size="11sp",
                  halign="left", valign="middle", size_hint_y=None, height=18)
        l.bind(size=lambda *a: setattr(l, "text_size", l.size))
        c.add_widget(l)
        return c

    @staticmethod
    def _pay_row(p):
        row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        when = datetime.fromisoformat(p["paid_at"]).strftime("%d.%m %H:%M")
        l = Label(text=p["full_name"], color=theme.TEXT_PRIMARY, font_size="13sp",
                  halign="left", valign="middle")
        l.bind(size=lambda *a: setattr(l, "text_size", l.size))
        row.add_widget(l)
        d = Label(text=when, color=theme.TEXT_MUTED, font_size="11sp",
                  size_hint_x=None, width=90, halign="right", valign="middle")
        d.bind(size=lambda *a: setattr(d, "text_size", d.size))
        row.add_widget(d)
        a = Label(text=f"[b]{p['amount']:.0f}₴[/b]", markup=True,
                  color=theme.ENERGY_GREEN if p["pay_type"] == "full" else theme.WARN_AMBER,
                  font_size="14sp", size_hint_x=None, width=80,
                  halign="right", valign="middle")
        a.bind(size=lambda *a2: setattr(a, "text_size", a.size))
        row.add_widget(a)
        return row
