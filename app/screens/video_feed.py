from pathlib import Path
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton
from ..auth import Session
from ..database.repos import VideoRepo
from ._layout import screen_shell

ROOT = Path(__file__).resolve().parents[2]


class _CatChip(ButtonBehavior, Label):
    def __init__(self, text, vcat_id, active, on_choose, **kw):
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (110, 34))
        kw.setdefault("font_size", "11sp")
        kw.setdefault("padding", (12, 6))
        kw.setdefault("color", theme.NEON_CYAN if active else theme.TEXT_SECONDARY)
        kw.setdefault("bold", True)
        super().__init__(text=text, **kw)
        self.vcat_id = vcat_id
        self._on_choose = on_choose
        active_bg = list(theme.NEON_CYAN[:3]) + [0.18]
        active_brd = list(theme.NEON_CYAN)
        with self.canvas.before:
            self._bg_c = Color(*(active_bg if active else (1, 1, 1, 0.04)))
            self._bg = RoundedRectangle(radius=[theme.RADIUS_CHIP])
            self._brd_c = Color(*(active_brd if active else (1, 1, 1, 0.12)))
            self._brd = Line(width=1.2, rounded_rectangle=(0, 0, 0, 0, theme.RADIUS_CHIP))
        self.bind(size=self._sync, pos=self._sync, texture_size=self._tx)

    def _tx(self, *_):
        self.width = max(80, self.texture_size[0] + 24)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._brd.rounded_rectangle = (*self.pos, *self.size, theme.RADIUS_CHIP)

    def on_release(self):
        self._on_choose(self.vcat_id)


class _VideoCard(ButtonBehavior, BoxLayout):
    def __init__(self, on_open, video_id: int, **kw):
        kw.setdefault("orientation", "vertical")
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 270)
        kw.setdefault("padding", 0)
        kw.setdefault("spacing", 0)
        super().__init__(**kw)
        self._on_open = on_open
        self._video_id = video_id
        with self.canvas.before:
            self._bg_c = Color(*theme.GLASS_TINT)
            self._bg = RoundedRectangle(radius=[theme.RADIUS_CARD])
            self._brd_c = Color(*theme.GLASS_BORDER)
            self._brd = Line(width=1.0, rounded_rectangle=(0, 0, 0, 0, theme.RADIUS_CARD))
        self.bind(size=self._sync, pos=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._brd.rounded_rectangle = (*self.pos, *self.size, theme.RADIUS_CARD)

    def on_release(self):

        self._on_open(self._video_id)


class _DeleteButton(ButtonBehavior, Label):
    def __init__(self, on_tap, **kw):
        kw.setdefault("text", "✕")
        kw.setdefault("color", (1, 1, 1, 0.95))
        kw.setdefault("font_size", "16sp")
        kw.setdefault("bold", True)
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (34, 34))
        super().__init__(**kw)
        self._on_tap = on_tap
        with self.canvas.before:
            Color(0, 0, 0, 0.55)
            self._bg = RoundedRectangle(radius=[17])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def on_release(self):
        self._on_tap()


class VideoFeedScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="video_feed", **kw)
        self._active_cat = None
        self._query = ""

    def on_enter(self):
        self.clear_widgets()


        search_row = BoxLayout(orientation="horizontal", spacing=8,
                               padding=[14, 10, 14, 4],
                               size_hint_y=None, height=54)
        search_in = TextInput(
            hint_text="Пошук відео за назвою...",
            text=self._query,
            multiline=False,
            size_hint_y=None, height=40,
            background_color=[1, 1, 1, 0.06],
            foreground_color=theme.TEXT_PRIMARY,
            cursor_color=theme.NEON_CYAN,
            padding=[12, 10, 12, 10],
        )
        search_in.bind(text=lambda _w, val: setattr(self, "_query", val))
        search_in.bind(on_text_validate=lambda *_: self.on_enter())
        search_row.add_widget(search_in)


        chips_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False,
                                  size_hint_y=None, height=46, bar_width=0)
        chips_box = BoxLayout(orientation="horizontal", spacing=8,
                              padding=[14, 6, 14, 6], size_hint_x=None)
        chips_box.bind(minimum_width=chips_box.setter("width"))
        chips_box.add_widget(_CatChip("ВСІ", None,
                                      active=(self._active_cat is None),
                                      on_choose=self._set_cat))
        for c in VideoRepo.categories():
            chips_box.add_widget(_CatChip(c["name"].upper(), c["vcat_id"],
                                          active=(self._active_cat == c["vcat_id"]),
                                          on_choose=self._set_cat))
        chips_scroll.add_widget(chips_box)


        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=14,
                            padding=[14, 8, 14, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        videos = VideoRepo.feed(self._active_cat)
        q = (self._query or "").strip().lower()
        if q:
            videos = [v for v in videos if q in (v["title"] or "").lower()]

        if not videos:
            content.add_widget(self._empty(bool(q)))
        else:
            for v in videos:
                content.add_widget(self._video_card(v))

        scroll.add_widget(content)

        body = BoxLayout(orientation="vertical")
        body.add_widget(search_row)
        body.add_widget(chips_scroll)
        body.add_widget(scroll)

        title = "Відео-тренування" if Session.role != "trainer" else "Стрічка відео"
        shell = screen_shell(body, title=title, active_nav="video")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _set_cat(self, vcat_id):
        self._active_cat = vcat_id
        self.on_enter()

    @staticmethod
    def _empty(filtered: bool = False):
        c = GlassCard(size_hint_y=None, height=120)
        msg = ("Нічого не знайдено за вашим запитом"
               if filtered else "Поки немає відео в цій категорії")
        c.add_widget(Label(text=msg,
                           color=theme.TEXT_SECONDARY,
                           font_size=theme.SIZE_BODY))
        return c

    def _video_card(self, v):
        card = _VideoCard(on_open=self._open, video_id=v["video_id"])


        thumb_box = RelativeLayout(size_hint_y=None, height=170)
        thumb_str = v["thumbnail_path"] or ""
        thumb_path = ROOT / thumb_str if thumb_str else None

        if thumb_path is not None and thumb_path.exists():
            img = Image(source=str(thumb_path), fit_mode="fill",
                        size_hint=(1, 1))
            thumb_box.add_widget(img)
        else:

            with thumb_box.canvas.before:
                Color(*theme.NEON_CYAN[:3], 0.10)
                thumb_box._bg = RoundedRectangle(
                    radius=[theme.RADIUS_CARD, theme.RADIUS_CARD, 0, 0])
            thumb_box.bind(
                pos=lambda *_: setattr(thumb_box._bg, "pos", thumb_box.pos),
                size=lambda *_: setattr(thumb_box._bg, "size", thumb_box.size),
            )

        play_overlay = Label(text="[size=42sp]▶[/size]", markup=True,
                             color=(1, 1, 1, 0.88),
                             pos_hint={"center_x": 0.5, "center_y": 0.5})
        thumb_box.add_widget(play_overlay)


        if (Session.role == "trainer"
                and v["trainer_id"] == Session.user_id):
            del_btn = _DeleteButton(
                on_tap=lambda vid=v["video_id"], t=v["title"]:
                    self._confirm_delete(vid, t),
                pos_hint={"right": 0.97, "top": 0.95},
            )
            thumb_box.add_widget(del_btn)

        card.add_widget(thumb_box)


        meta = BoxLayout(orientation="vertical", spacing=4,
                         padding=[12, 8, 12, 10],
                         size_hint_y=None, height=100)

        cat = Label(text=f"[b]{v['category'].upper()}[/b]", markup=True,
                    color=theme.NEON_MAGENTA, font_size="10sp",
                    halign="left", valign="middle",
                    size_hint_y=None, height=16)
        cat.bind(size=lambda *a: setattr(cat, "text_size", cat.size))
        meta.add_widget(cat)

        title = Label(text=v["title"], color=theme.TEXT_PRIMARY,
                      font_size="15sp", bold=True,
                      halign="left", valign="middle",
                      size_hint_y=None, height=22,
                      shorten=True, shorten_from="right")
        title.bind(size=lambda *a: setattr(title, "text_size", title.size))
        meta.add_widget(title)

        bottom = BoxLayout(orientation="horizontal", spacing=8,
                           size_hint_y=None, height=22)
        tr = Label(text=f"● {v['trainer']}", color=theme.TEXT_SECONDARY,
                   font_size="11sp", halign="left", valign="middle",
                   shorten=True, shorten_from="right")
        tr.bind(size=lambda *a: setattr(tr, "text_size", tr.size))
        likes = Label(text=f"♥ {v['likes']}", color=theme.NEON_MAGENTA,
                      font_size="12sp", size_hint_x=None, width=44,
                      halign="right", valign="middle")
        likes.bind(size=lambda *a: setattr(likes, "text_size", likes.size))
        comments = Label(text=f"✎ {v['comments_count']}",
                         color=theme.NEON_CYAN, font_size="12sp",
                         size_hint_x=None, width=44,
                         halign="right", valign="middle")
        comments.bind(size=lambda *a: setattr(comments, "text_size", comments.size))
        bottom.add_widget(tr)
        bottom.add_widget(likes)
        bottom.add_widget(comments)
        meta.add_widget(bottom)

        card.add_widget(meta)
        return card

    def _open(self, video_id):
        target = self.manager.get_screen("video_detail")
        target.video_id = video_id
        self.manager.go("video_detail")

    def _confirm_delete(self, video_id: int, title: str):
        body = BoxLayout(orientation="vertical", padding=14, spacing=10)
        body.add_widget(Label(
            text=f"Видалити відео «{title}»?\nЦе незворотньо.",
            color=theme.TEXT_PRIMARY, font_size="14sp",
            halign="center", valign="middle"))
        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=46)
        cancel = GhostButton(text="СКАСУВАТИ")
        confirm = NeonButton(text="ВИДАЛИТИ")
        actions.add_widget(cancel)
        actions.add_widget(confirm)
        body.add_widget(actions)
        popup = Popup(title="Підтвердження", content=body,
                      size_hint=(0.86, None), height=200,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_MAGENTA,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            VideoRepo.delete(video_id)
            popup.dismiss()
            self.on_enter()
        confirm.bind(on_release=do)
        popup.open()
