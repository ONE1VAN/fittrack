from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton, StatusChip
from ..auth import Session
from ..database.repos import EquipmentRepo
from ._layout import screen_shell

class EquipmentScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="equipment", **kw)

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=12,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        faults = EquipmentRepo.faults()
        if faults:
            content.add_widget(Label(text="[b]▲ ВІДКРИТІ ЗАЯВКИ[/b]", markup=True,
                                     color=theme.DANGER_RED, font_size="13sp",
                                     size_hint_y=None, height=22,
                                     halign="left", valign="middle"))
            for f in faults:
                content.add_widget(self._fault_card(f))

        content.add_widget(Label(text="[b]ІНВЕНТАР[/b]", markup=True,
                                 color=theme.NEON_CYAN, font_size="13sp",
                                 size_hint_y=None, height=22,
                                 halign="left", valign="middle"))
        for e in EquipmentRepo.all():
            content.add_widget(self._eq_row(e))

        scroll.add_widget(content)
        shell = screen_shell(scroll, title="Обладнання", active_nav="home")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _fault_card(self, f):
        c = GlassCard(size_hint_y=None, padding=12, spacing=6,
                      border_color=[*theme.DANGER_RED[:3], 0.4])
        c.bind(minimum_height=c.setter("height"))
        top = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=24)
        t = Label(text=f"[b]{f['eq_name']}[/b]", markup=True,
                  color=theme.TEXT_PRIMARY, font_size="14sp",
                  halign="left", valign="middle",
                  shorten=True, shorten_from="right")
        t.bind(size=lambda *a: setattr(t, "text_size", t.size))
        top.add_widget(t)
        if f["critical"]:
            top.add_widget(StatusChip(status="fault"))
        c.add_widget(top)
        desc = Label(text=f["description"], color=theme.TEXT_SECONDARY, font_size="12sp",
                     halign="left", valign="top", size_hint_y=None)
        desc.bind(
            width=lambda *a: setattr(desc, "text_size", (desc.width, None)),
            texture_size=lambda *a: setattr(desc, "height",
                                             max(desc.texture_size[1], 18)))
        c.add_widget(desc)
        report = Label(text=f"Повідомив: {f['reporter']}  •  {f['reported_at'][:16]}",
                       color=theme.TEXT_MUTED, font_size="10sp",
                       size_hint_y=None, height=16,
                       halign="left", valign="middle")
        report.bind(size=lambda *a: setattr(report, "text_size", report.size))
        c.add_widget(report)

        if Session.role == "admin":
            actions = BoxLayout(orientation="horizontal", spacing=8,
                                size_hint_y=None, height=38, padding=[0, 4, 0, 0])
            actions.add_widget(Label())
            fix = NeonButton(text="ПОЗНАЧИТИ СПРАВНИМ", height=34)
            fix.bind(on_release=lambda *_, mid=f["mr_id"]:
                     (EquipmentRepo.resolve_fault(mid), self.on_enter()))
            actions.add_widget(fix)
            c.add_widget(actions)
        return c

    def _eq_row(self, e):
        c = GlassCard(size_hint_y=None, height=70, padding=12, spacing=6)
        row = BoxLayout(orientation="horizontal", spacing=8)
        info = Label(text=f"[b]{e['name']}[/b]\n[size=11sp][color=#9EA8CE]"
                          f"Кількість: {e['quantity']}[/color][/size]",
                     markup=True, color=theme.TEXT_PRIMARY, font_size="13sp",
                     halign="left", valign="middle",
                     shorten=True, shorten_from="right")
        info.bind(size=lambda *a: setattr(info, "text_size", info.size))
        row.add_widget(info)
        row.add_widget(StatusChip(status=e["status"]))
        if Session.role in ("trainer", "admin"):
            btn = GhostButton(text="▲", size_hint_x=None, width=44, height=36)
            btn.bind(on_release=lambda *_, eid=e["eq_id"], name=e["name"]:
                     self._report_dialog(eid, name))
            row.add_widget(btn)
        c.add_widget(row)
        return c

    def _report_dialog(self, eq_id: int, eq_name: str):
        body = BoxLayout(orientation="vertical", padding=12, spacing=8)
        body.add_widget(Label(text=f"[b]{eq_name}[/b]", markup=True,
                              color=theme.TEXT_PRIMARY, font_size="16sp",
                              size_hint_y=None, height=24))
        ti = TextInput(hint_text="Опис несправності...", multiline=True,
                       size_hint_y=None, height=120,
                       background_color=[1, 1, 1, 0.06],
                       foreground_color=theme.TEXT_PRIMARY,
                       cursor_color=theme.NEON_CYAN)
        body.add_widget(ti)

        chk_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=34, spacing=6)
        chk = CheckBox(size_hint_x=None, width=34,
                       color=theme.DANGER_RED, active=False)
        chk_lbl = Label(text="Критичне (зупиняє експлуатацію)",
                        color=theme.TEXT_PRIMARY, font_size="13sp",
                        halign="left", valign="middle")
        chk_lbl.bind(size=lambda *a: setattr(chk_lbl, "text_size", chk_lbl.size))
        chk_row.add_widget(chk)
        chk_row.add_widget(chk_lbl)
        body.add_widget(chk_row)

        actions = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=44)
        send = NeonButton(text="ВІДПРАВИТИ ЗАЯВКУ")
        cancel = GhostButton(text="СКАСУВАТИ")
        actions.add_widget(cancel)
        actions.add_widget(send)
        body.add_widget(actions)

        popup = Popup(title="Заявка на ремонт", content=body,
                      size_hint=(0.92, None), height=340,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            if not ti.text.strip():
                return
            EquipmentRepo.report_fault(eq_id, Session.user_id,
                                       ti.text.strip(), bool(chk.active))
            popup.dismiss()
            self.on_enter()
        send.bind(on_release=do)
        popup.open()
