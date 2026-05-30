from datetime import datetime
from pathlib import Path
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.video import Video
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.clock import Clock

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton, DangerButton
from ..auth import Session
from ..database.repos import VideoRepo, CommentRepo
from ._layout import screen_shell

ROOT = Path(__file__).resolve().parents[2]


def _fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds or 0))
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


class _PlayerBox(FloatLayout):
    def __init__(self, video_path: Path, thumb_path: Path | None, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self._bg = RoundedRectangle(radius=[theme.RADIUS_CARD])
        self.bind(
            pos=lambda *_: setattr(self._bg, "pos", self.pos),
            size=lambda *_: setattr(self._bg, "size", self.size),
        )

        self.video = None
        if video_path is not None and video_path.exists():
            try:


                self.video = Video(
                    source=str(video_path),
                    state="play",
                    eos="loop",
                    fit_mode="contain",
                    size_hint=(1, 1),
                    pos_hint={"x": 0, "y": 0},
                )
                self.add_widget(self.video)
            except Exception:
                self.video = None

        if self.video is None and thumb_path is not None and thumb_path.exists():
            self.add_widget(Image(
                source=str(thumb_path), fit_mode="fill",
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
            ))

        self._overlay = _OverlayButton(on_tap=self.toggle)
        self.add_widget(self._overlay)
        Clock.schedule_once(lambda *_: self._update_overlay(), 0.2)

    def toggle(self, *_):
        if self.video is None:
            return
        try:
            if self.video.state == "play":
                self.video.state = "pause"
            else:
                self.video.state = "play"
        except Exception:
            pass
        self._update_overlay()

    def _update_overlay(self, *_):
        playing = bool(self.video and self.video.state == "play")
        self._overlay.set_playing(playing)

    def stop(self):
        if self.video is not None:
            try:
                self.video.state = "stop"


                self.video.unload()
            except Exception:
                pass
            self.video = None


class _OverlayButton(ButtonBehavior, Label):
    def __init__(self, on_tap, **kw):
        kw.setdefault("text", "[size=64sp]▶[/size]")
        kw.setdefault("markup", True)
        kw.setdefault("color", (1, 1, 1, 0.88))
        kw.setdefault("size_hint", (1, 1))
        kw.setdefault("pos_hint", {"x": 0, "y": 0})
        super().__init__(**kw)
        self._on_tap = on_tap

    def set_playing(self, playing: bool):
        self.text = "" if playing else "[size=64sp]▶[/size]"

    def on_release(self):
        self._on_tap()


class _ProgressBar(Widget):
    def __init__(self, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 6)
        super().__init__(**kw)
        self._progress = 0.0
        with self.canvas:
            self._track_c = Color(*theme.NEON_CYAN[:3], 0.18)
            self._track = RoundedRectangle(radius=[3])
            self._fill_c = Color(*theme.NEON_CYAN[:3], 1.0)
            self._fill = RoundedRectangle(radius=[3])
        self.bind(size=self._sync, pos=self._sync)

    def set_progress(self, value: float):
        self._progress = max(0.0, min(1.0, float(value)))
        self._sync()

    def _sync(self, *_):
        self._track.pos = self.pos
        self._track.size = self.size
        self._fill.pos = self.pos
        self._fill.size = (self.width * self._progress, self.height)


    def on_touch_down(self, touch):
        return self.collide_point(*touch.pos)


class _SeekRow(BoxLayout):
    def __init__(self, video, **kw):
        kw.setdefault("orientation", "horizontal")
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", 26)
        kw.setdefault("spacing", 10)
        kw.setdefault("padding", [6, 0, 6, 0])
        super().__init__(**kw)
        self._video = video
        self._muted_tail = False
        self._initial_volume = 1.0
        if video is not None:
            try:
                self._initial_volume = float(video.volume)
            except Exception:
                pass

        self._bar = _ProgressBar(size_hint=(1, None), height=6)

        from kivy.uix.anchorlayout import AnchorLayout
        bar_holder = AnchorLayout(anchor_x="center", anchor_y="center")
        bar_holder.add_widget(self._bar)
        self.add_widget(bar_holder)

        self._time_lbl = Label(text="0:00 / 0:00", color=theme.TEXT_SECONDARY,
                               font_size="11sp", size_hint_x=None, width=88,
                               halign="right", valign="middle")
        self._time_lbl.bind(size=lambda *a: setattr(self._time_lbl, "text_size",
                                                    self._time_lbl.size))
        self.add_widget(self._time_lbl)

        if video is not None:
            try:
                video.bind(position=self._on_video_position,
                           duration=self._on_video_duration,
                           eos=self._on_video_eos)
            except Exception:
                pass

    def _refresh(self):
        v = self._video
        if v is None:
            return
        dur = float(v.duration or 0)
        pos = float(v.position or 0)
        if dur > 0:
            self._bar.set_progress(pos / dur)


            if pos >= dur - 0.5 and not self._muted_tail:
                self._muted_tail = True
                try:
                    v.volume = 0
                except Exception:
                    pass


            if self._muted_tail and pos < dur * 0.5:
                self._muted_tail = False
                try:
                    v.volume = self._initial_volume
                except Exception:
                    pass
        self._time_lbl.text = f"{_fmt_time(pos)} / {_fmt_time(dur)}"

    def _on_video_position(self, *_):
        self._refresh()

    def _on_video_duration(self, *_):
        self._refresh()

    def _on_video_eos(self, _inst, value):


        if not value:
            return
        v = self._video
        if v is None:
            return
        if self._muted_tail:
            self._muted_tail = False
            try:
                v.volume = self._initial_volume
            except Exception:
                pass

    def stop(self):
        if self._video is not None:
            for prop, cb in (("position", self._on_video_position),
                             ("duration", self._on_video_duration),
                             ("eos", self._on_video_eos)):
                try:
                    self._video.unbind(**{prop: cb})
                except Exception:
                    pass
        self._video = None


class VideoDetailScreen(Screen):
    video_id = NumericProperty(0)

    def __init__(self, **kw):
        super().__init__(name="video_detail", **kw)
        self._player = None
        self._seek = None
        self._comments_box = None
        self._likes_lbl = None
        self._like_holder = None
        self._built_for = None

    def on_enter(self):
        if not self.video_id:
            self.manager.go("video_feed", direction="right")
            return
        v = VideoRepo.by_id(self.video_id)
        if not v:
            self.manager.go("video_feed", direction="right")
            return
        if self._built_for == self.video_id and self._player is not None:

            self._refresh_dynamic(v)
            return
        self._stop_player()
        self.clear_widgets()
        self._built_for = self.video_id
        self._build(v)

    def _build(self, v):
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=12,
                            padding=[14, 12, 14, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))


        fp = v["file_path"] or ""
        local = (ROOT / fp) if fp else None
        thumb_str = v["thumbnail_path"] or ""
        thumb_path = ROOT / thumb_str if thumb_str else None
        player_box = _PlayerBox(local, thumb_path,
                                size_hint_y=None, height=220)
        self._player = player_box
        content.add_widget(player_box)

        if player_box.video is not None:
            self._seek = _SeekRow(player_box.video)
            content.add_widget(self._seek)


        meta_card = GlassCard(size_hint_y=None, padding=14, spacing=6)
        title_lbl = Label(text=v["title"], color=theme.TEXT_PRIMARY,
                          font_size="18sp", bold=True,
                          size_hint_y=None,
                          halign="left", valign="top")
        title_lbl.bind(
            width=lambda *a: setattr(title_lbl, "text_size",
                                     (title_lbl.width, None)),
            texture_size=lambda *a: setattr(title_lbl, "height",
                                            title_lbl.texture_size[1] + 4))
        meta_card.add_widget(title_lbl)

        likes_lbl = Label(text=f"{v['category']}  •  {v['trainer']}  •  ♥ {v['likes']}",
                          color=theme.TEXT_SECONDARY, font_size="12sp",
                          size_hint_y=None, height=18,
                          halign="left", valign="middle")
        likes_lbl.bind(size=lambda *a: setattr(likes_lbl, "text_size", likes_lbl.size))
        self._likes_lbl = likes_lbl
        self._likes_template = f"{v['category']}  •  {v['trainer']}  •  ♥ {{likes}}"
        meta_card.add_widget(likes_lbl)

        actions = BoxLayout(orientation="horizontal", spacing=10,
                            size_hint_y=None, height=44)
        back = GhostButton(text="НАЗАД", height=42)
        back.bind(on_release=lambda *_: self._go_back())
        self._like_holder = BoxLayout(orientation="horizontal")
        self._rebuild_like_button(v["video_id"])
        actions.add_widget(back)
        actions.add_widget(self._like_holder)
        meta_card.add_widget(actions)
        meta_card.bind(minimum_height=meta_card.setter("height"))
        meta_card.height = 0
        content.add_widget(meta_card)

        content.add_widget(Label(text="[b]ОБГОВОРЕННЯ[/b]", markup=True,
                                 color=theme.NEON_CYAN, font_size="13sp",
                                 size_hint_y=None, height=22,
                                 halign="left", valign="middle"))

        composer = GlassCard(size_hint_y=None, height=110, padding=12, spacing=6)
        ti = TextInput(hint_text="Напишіть коментар...", multiline=True,
                       size_hint_y=None, height=54,
                       background_color=[1, 1, 1, 0.06],
                       foreground_color=theme.TEXT_PRIMARY,
                       cursor_color=theme.NEON_CYAN)
        composer.add_widget(ti)
        send = NeonButton(text="ВІДПРАВИТИ", size_hint_y=None, height=38)
        send.bind(on_release=lambda *_: self._post(ti, None))
        composer.add_widget(send)
        content.add_widget(composer)


        self._comments_box = BoxLayout(orientation="vertical", spacing=10,
                                       size_hint_y=None)
        self._comments_box.bind(minimum_height=self._comments_box.setter("height"))
        content.add_widget(self._comments_box)
        self._fill_comments(v["video_id"])

        scroll.add_widget(content)
        shell = screen_shell(scroll, title="Відео-тренування",
                             back="video_feed", active_nav="video")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    def _refresh_dynamic(self, v):
        if self._likes_lbl is not None:
            self._likes_lbl.text = self._likes_template.format(likes=v["likes"])
        self._rebuild_like_button(v["video_id"])
        self._fill_comments(v["video_id"])

    def _rebuild_like_button(self, video_id: int):
        if getattr(self, "_like_holder", None) is None:
            return
        self._like_holder.clear_widgets()
        is_liked = VideoRepo.liked_by(video_id, Session.user_id)
        if is_liked:
            btn = DangerButton(text="♥  ВПОДОБАНО", height=42)
        else:
            btn = NeonButton(text="♡  ВПОДОБАТИ", height=42)
        btn.bind(on_release=lambda *_, vid=video_id: self._toggle_like(vid))
        self._like_holder.add_widget(btn)

    def _fill_comments(self, video_id: int):
        if self._comments_box is None:
            return
        self._comments_box.clear_widgets()
        comments = CommentRepo.for_video(video_id)
        if not comments:
            empty = GlassCard(size_hint_y=None, height=64)
            empty.add_widget(Label(text="Поки немає коментарів — будьте першим!",
                                   color=theme.TEXT_MUTED, font_size="13sp"))
            self._comments_box.add_widget(empty)
            return
        for c in comments:
            self._comments_box.add_widget(self._comment(c))

    def on_leave(self):
        self._stop_player()
        self._built_for = None
        self._comments_box = None
        self._likes_lbl = None
        self._like_holder = None

    def _stop_player(self):
        if self._seek is not None:
            self._seek.stop()
            self._seek = None
        if self._player is not None:
            self._player.stop()
            self._player = None

    def _go_back(self):
        self._stop_player()
        self.manager.go("video_feed", direction="right")

    def _toggle_like(self, video_id):
        VideoRepo.toggle_like(video_id, Session.user_id)
        v = VideoRepo.by_id(video_id)
        if v:
            self._refresh_dynamic(v)

    def _post(self, ti, parent_id):
        text = ti.text.strip()
        if not text:
            return
        CommentRepo.add(self.video_id, Session.user_id, text, parent_id)
        ti.text = ""
        self._fill_comments(self.video_id)

    def _comment(self, c):
        card = GlassCard(size_hint_y=None, padding=10, spacing=4)
        role_color = (theme.NEON_MAGENTA if c["role_name"] == "trainer"
                      else theme.NEON_CYAN if c["role_name"] == "admin"
                      else theme.TEXT_SECONDARY)
        head = BoxLayout(orientation="horizontal", spacing=8,
                         size_hint_y=None, height=20)
        name = Label(text=f"[b]{c['full_name']}[/b]", markup=True,
                     color=role_color, font_size="13sp",
                     halign="left", valign="middle")
        name.bind(size=lambda *a: setattr(name, "text_size", name.size))
        when = Label(text=self._ago(c["created_at"]),
                     color=theme.TEXT_MUTED, font_size="11sp",
                     halign="right", valign="middle")
        when.bind(size=lambda *a: setattr(when, "text_size", when.size))
        head.add_widget(name)
        head.add_widget(when)
        card.add_widget(head)

        body = Label(text=c["text"], color=theme.TEXT_PRIMARY,
                     font_size="13sp", halign="left", valign="top",
                     size_hint_y=None)
        body.bind(width=lambda *a: setattr(body, "text_size", (body.width, None)),
                  texture_size=lambda *a: setattr(body, "height", body.texture_size[1] + 4))
        card.add_widget(body)

        reply_btn = GhostButton(text="ВІДПОВІСТИ",
                                size_hint=(None, None),
                                width=120, height=28, font_size="10sp")
        reply_btn.bind(on_release=lambda *_, cid=c["comment_id"]: self._reply_dialog(cid))
        card.add_widget(reply_btn)

        for r in c.get("replies", []):
            indent = BoxLayout(orientation="horizontal", size_hint_y=None,
                               spacing=8, height=80)
            indent.add_widget(Label(text="", size_hint_x=None, width=16))
            indent.add_widget(self._reply(r))
            card.add_widget(indent)

        card.bind(minimum_height=card.setter("height"))
        card.height = 0
        return card

    def _reply(self, r):
        c = GlassCard(size_hint_y=None, padding=8, spacing=2,
                      fill_color=[1, 1, 1, 0.03],
                      border_color=[*theme.NEON_CYAN[:3], 0.3])
        role_color = (theme.NEON_MAGENTA if r["role_name"] == "trainer"
                      else theme.TEXT_SECONDARY)
        n = Label(text=f"[b]{r['full_name']}[/b]", markup=True,
                  color=role_color, font_size="12sp",
                  size_hint_y=None, height=16,
                  halign="left", valign="middle")
        n.bind(size=lambda *a: setattr(n, "text_size", n.size))
        c.add_widget(n)
        b = Label(text=r["text"], color=theme.TEXT_PRIMARY,
                  font_size="12sp", halign="left", valign="top",
                  size_hint_y=None)
        b.bind(width=lambda *a: setattr(b, "text_size", (b.width, None)),
               texture_size=lambda *a: setattr(b, "height", b.texture_size[1] + 4))
        c.add_widget(b)
        c.bind(minimum_height=c.setter("height"))
        c.height = 0
        return c

    def _reply_dialog(self, parent_comment_id):
        body = BoxLayout(orientation="vertical", padding=12, spacing=8)
        ti = TextInput(hint_text="Ваша відповідь...", multiline=True,
                       background_color=[1, 1, 1, 0.06],
                       foreground_color=theme.TEXT_PRIMARY,
                       cursor_color=theme.NEON_CYAN,
                       size_hint_y=None, height=120)
        body.add_widget(ti)
        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=42)
        send = NeonButton(text="ВІДПРАВИТИ")
        cancel = GhostButton(text="СКАСУВАТИ")
        actions.add_widget(cancel)
        actions.add_widget(send)
        body.add_widget(actions)
        popup = Popup(title="Відповідь на коментар", content=body,
                      size_hint=(0.92, None), height=260,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do(*_):
            if not ti.text.strip():
                return
            CommentRepo.add(self.video_id, Session.user_id,
                            ti.text.strip(), parent_comment_id)
            popup.dismiss()
            self._fill_comments(self.video_id)
        send.bind(on_release=do)
        popup.open()

    @staticmethod
    def _ago(iso):
        try:
            dt = datetime.fromisoformat(iso)
            delta = datetime.now() - dt
            if delta.days >= 1:
                return f"{delta.days} дн тому"
            h = delta.seconds // 3600
            if h >= 1:
                return f"{h} год тому"
            m = delta.seconds // 60
            if m >= 1:
                return f"{m} хв тому"
            return "щойно"
        except Exception:
            return ""
