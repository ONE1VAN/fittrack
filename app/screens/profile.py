import io
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton
from ..auth import Session
from ..database.repos import UserRepo, SubscriptionRepo
from ._layout import screen_shell

class ProfileScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="profile", **kw)

    def on_enter(self):
        self.clear_widgets()
        if not Session.is_authenticated():
            self.manager.go("login", direction="right")
            return
        user = UserRepo.by_id(Session.user_id)

        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=14,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        card = GlassCard(size_hint_y=None, height=160, padding=18, spacing=6)
        card.add_widget(Label(text=f"[b]{user['full_name']}[/b]", markup=True,
                              color=theme.TEXT_PRIMARY, font_size="22sp",
                              size_hint_y=None, height=30,
                              halign="left", valign="middle"))
        card.add_widget(Label(text=f"Роль: [b]{user['role_name']}[/b]", markup=True,
                              color=theme.NEON_CYAN, font_size="13sp",
                              size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        card.add_widget(Label(text=f"Email: {user['email']}",
                              color=theme.TEXT_SECONDARY, font_size="13sp",
                              size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        if user["phone"]:
            card.add_widget(Label(text=f"Телефон: {user['phone']}",
                                  color=theme.TEXT_SECONDARY, font_size="13sp",
                                  size_hint_y=None, height=18,
                                  halign="left", valign="middle"))
        for w in card.children:
            if isinstance(w, Label):
                w.bind(size=lambda *a, _w=w: setattr(_w, "text_size", _w.size))
        content.add_widget(card)

        if Session.role == "client" and user["card_id_skud"]:
            qr_card = GlassCard(size_hint_y=None, height=280, padding=16, spacing=8)
            qr_card.add_widget(Label(text="[b]КАРТКА ДОСТУПУ СКУД[/b]", markup=True,
                                     color=theme.NEON_MAGENTA, font_size="13sp",
                                     size_hint_y=None, height=20,
                                     halign="center", valign="middle"))
            img = self._make_qr(user["card_id_skud"])
            if img is not None:
                qr_card.add_widget(img)
            qr_card.add_widget(Label(text=f"ID: {user['card_id_skud']}",
                                     color=theme.TEXT_PRIMARY, font_size="14sp",
                                     size_hint_y=None, height=20,
                                     halign="center", valign="middle"))
            qr_card.add_widget(Label(text="Прикладіть до турнікета",
                                     color=theme.TEXT_MUTED, font_size="11sp",
                                     size_hint_y=None, height=14,
                                     halign="center", valign="middle"))
            content.add_widget(qr_card)

        if Session.role == "client":
            sub = SubscriptionRepo.active_for_client(Session.user_id)
            if sub:
                ac = GlassCard(size_hint_y=None, height=80, padding=14, spacing=4)
                ac.add_widget(Label(text=f"[b]{sub['type_name']}[/b]", markup=True,
                                    color=theme.TEXT_PRIMARY, font_size="15sp",
                                    size_hint_y=None, height=22,
                                    halign="left", valign="middle"))
                ac.add_widget(Label(text=f"Дійсний до {sub['end_date']}  •  {sub['status']}",
                                    color=theme.TEXT_SECONDARY, font_size="12sp",
                                    size_hint_y=None, height=18,
                                    halign="left", valign="middle"))
                for w in ac.children:
                    if isinstance(w, Label):
                        w.bind(size=lambda *a, _w=w: setattr(_w, "text_size", _w.size))
                content.add_widget(ac)

        logout = GhostButton(text="ВИЙТИ", size_hint_y=None, height=48)
        logout.bind(on_release=self._logout)
        content.add_widget(logout)

        scroll.add_widget(content)
        shell = screen_shell(scroll, title="Профіль", active_nav="profile")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _make_qr(self, payload: str):
        from kivy.uix.anchorlayout import AnchorLayout
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(payload)
            qr.make(fit=True)
            pil = qr.make_image(fill_color="#00F0FF", back_color=(0, 0, 0, 0)).convert("RGBA")
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            buf.seek(0)
            core = CoreImage(buf, ext="png")
            img = Image(texture=core.texture, size_hint=(None, None),
                        size=(180, 180))
            wrap = AnchorLayout(anchor_x="center", anchor_y="center",
                                size_hint_y=None, height=190)
            wrap.add_widget(img)
            return wrap
        except Exception:
            return Label(text="[size=72sp]◼[/size]", markup=True,
                         color=theme.NEON_CYAN, size_hint_y=None, height=180,
                         halign="center", valign="middle")

    def _logout(self, *_):
        Session.logout()
        self.manager.fade_to("login")
