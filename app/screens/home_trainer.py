from datetime import datetime, timedelta
from pathlib import Path
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation

from .. import theme
from ..widgets import GlassCard, NeonButton, GhostButton, StatusChip
from ..auth import Session
from ..database.repos import ScheduleRepo, VideoRepo, CommentRepo
from ._layout import screen_shell

class HomeTrainerScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="home_trainer", **kw)

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(do_scroll_x=False, bar_width=0)
        content = BoxLayout(orientation="vertical", spacing=14,
                            padding=[16, 14, 16, 20], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        classes = ScheduleRepo.trainer_schedule(Session.user_id)
        upcoming = sum(1 for c in classes
                       if datetime.fromisoformat(c["start_time"]) > datetime.now())
        videos = VideoRepo.feed()
        my_videos = [v for v in videos if v["trainer_id"] == Session.user_id]

        stats = BoxLayout(orientation="horizontal", spacing=10,
                          size_hint_y=None, height=110)
        stats.add_widget(self._stat(str(upcoming), "Майбутніх занять", theme.NEON_CYAN))
        stats.add_widget(self._stat(str(len(my_videos)), "Моїх відео", theme.NEON_MAGENTA))
        stats.add_widget(self._stat(str(sum(c["booked_count"] for c in classes)),
                                    "Бронювань", theme.ENERGY_GREEN))
        content.add_widget(stats)

        a1 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=54)
        b1 = NeonButton(text="ЗАВАНТАЖИТИ ВІДЕО", height=48)
        b1.bind(on_release=self._upload_dialog)
        b2 = GhostButton(text="РОЗКЛАД", height=48)
        b2.bind(on_release=lambda *_: self.manager.go("schedule"))
        a1.add_widget(b1)
        a1.add_widget(b2)
        content.add_widget(a1)

        a2 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=54)
        b3 = NeonButton(text="НОВЕ ЗАНЯТТЯ", height=48)
        b3.bind(on_release=self._new_class_dialog)
        b4 = GhostButton(text="ВІДЕО", height=48)
        b4.bind(on_release=lambda *_: self.manager.go("video_feed"))
        a2.add_widget(b3)
        a2.add_widget(b4)
        content.add_widget(a2)

        sec = GlassCard(size_hint_y=None, padding=14, spacing=8)
        sec.add_widget(Label(text="[b]МОЇ ЗАНЯТТЯ[/b]", markup=True,
                             color=theme.NEON_CYAN, font_size="13sp",
                             size_hint_y=None, height=20,
                             halign="left", valign="middle"))
        if not classes:
            sec.add_widget(Label(text="Немає запланованих занять",
                                 color=theme.TEXT_MUTED, size_hint_y=None, height=24,
                                 font_size="13sp"))
            sec.height = 80
        else:
            for c in classes[:6]:
                sec.add_widget(self._class_row(c))
            sec.height = 60 + min(len(classes), 6) * 60
        content.add_widget(sec)

        scroll.add_widget(content)
        shell = screen_shell(scroll, title=f"Тренер {Session.full_name.split()[-1]}",
                             active_nav="home")
        self.add_widget(shell)
        content.opacity = 0
        Animation(opacity=1, d=theme.DUR_NORMAL).start(content)

    @staticmethod
    def _stat(big, label, color):


        c = GlassCard(padding=10, spacing=2, orientation="vertical")
        num = Label(text=f"[b]{big}[/b]", markup=True, color=color,
                    font_size="30sp", halign="left", valign="bottom",
                    size_hint_y=None, height=46)
        num.bind(size=lambda *a: setattr(num, "text_size", num.size))
        l = Label(text=label, color=theme.TEXT_SECONDARY, font_size="10sp",
                  halign="left", valign="top",
                  size_hint_y=None, height=32)
        l.bind(size=lambda *a: setattr(l, "text_size", l.size))
        c.add_widget(num)
        c.add_widget(l)
        return c

    @staticmethod
    def _class_row(c):
        row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=56,
                        padding=[8, 0, 8, 0])
        dt = datetime.fromisoformat(c["start_time"])
        when = Label(text=f"[b]{dt.strftime('%d.%m')}\n{dt.strftime('%H:%M')}[/b]",
                     markup=True, color=theme.NEON_CYAN, font_size="13sp",
                     size_hint_x=None, width=56, halign="center", valign="middle")
        when.bind(size=lambda *a: setattr(when, "text_size", when.size))
        info = BoxLayout(orientation="vertical")
        t = Label(text=c["title"], color=theme.TEXT_PRIMARY, font_size="14sp",
                  halign="left", valign="middle")
        t.bind(size=lambda *a: setattr(t, "text_size", t.size))
        meta = Label(text=f"{c['category']} • {c['room']} • {c['booked_count']}/{c['capacity']}",
                     color=theme.TEXT_SECONDARY, font_size="11sp",
                     halign="left", valign="middle")
        meta.bind(size=lambda *a: setattr(meta, "text_size", meta.size))
        info.add_widget(t)
        info.add_widget(meta)
        row.add_widget(when)
        row.add_widget(info)
        return row

    def _upload_dialog(self, *_):
        body = BoxLayout(orientation="vertical", padding=12, spacing=8)

        title_in = TextInput(hint_text="Назва відео", multiline=False,
                             size_hint_y=None, height=44,
                             background_color=[1, 1, 1, 0.06],
                             foreground_color=theme.TEXT_PRIMARY,
                             cursor_color=theme.NEON_CYAN)
        desc_in = TextInput(
            hint_text="Опис (буде першим коментарем під відео)",
            multiline=True, size_hint_y=None, height=110,
            background_color=[1, 1, 1, 0.06],
            foreground_color=theme.TEXT_PRIMARY,
            cursor_color=theme.NEON_CYAN)

        cat_row_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False,
                                    size_hint_y=None, height=42, bar_width=0)
        cat_row = BoxLayout(orientation="horizontal", spacing=6, size_hint_x=None)
        cat_row.bind(minimum_width=cat_row.setter("width"))
        cats = VideoRepo.categories()
        chosen = {"vcat_id": cats[0]["vcat_id"] if cats else None}
        chips = []

        def select_cat(vcat_id):
            chosen["vcat_id"] = vcat_id
            for ch in chips:
                ch.set_active(ch.vcat_id == vcat_id)

        for c in cats:
            chip = _Chip(c["name"], c["vcat_id"], active=(c["vcat_id"] == chosen["vcat_id"]),
                         on_choose=select_cat)
            chips.append(chip)
            cat_row.add_widget(chip)
        cat_row_scroll.add_widget(cat_row)

        file_row = BoxLayout(orientation="horizontal", spacing=6,
                             size_hint_y=None, height=44)
        path_lbl = TextInput(hint_text="Оберіть файл відео (MP4)...",
                             multiline=False, readonly=True,
                             background_color=[1, 1, 1, 0.06],
                             foreground_color=theme.TEXT_PRIMARY)
        browse = GhostButton(text="ОБРАТИ", size_hint_x=None, width=130, height=44)
        file_row.add_widget(path_lbl)
        file_row.add_widget(browse)
        browse.bind(on_release=lambda *_: self._open_file_picker(path_lbl))

        err = Label(text="", color=theme.DANGER_RED, font_size="12sp",
                    size_hint_y=None, height=18)

        body.add_widget(Label(text="[b]Завантажити відео-тренування[/b]", markup=True,
                              color=theme.NEON_CYAN, font_size="14sp",
                              size_hint_y=None, height=22))
        body.add_widget(Label(text="Назва:", color=theme.TEXT_SECONDARY,
                              font_size="12sp", size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        body.add_widget(title_in)
        body.add_widget(Label(text="Опис (стане першим коментарем):",
                              color=theme.TEXT_SECONDARY,
                              font_size="12sp", size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        body.add_widget(desc_in)
        body.add_widget(Label(text="Категорія:", color=theme.TEXT_SECONDARY,
                              font_size="12sp", size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        body.add_widget(cat_row_scroll)
        body.add_widget(Label(text="Файл відео (MP4):", color=theme.TEXT_SECONDARY,
                              font_size="12sp", size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        body.add_widget(file_row)
        body.add_widget(err)

        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=46)
        save = NeonButton(text="ОПУБЛІКУВАТИ")
        cancel = GhostButton(text="СКАСУВАТИ")
        actions.add_widget(cancel)
        actions.add_widget(save)
        body.add_widget(actions)

        popup = Popup(title="", content=body, size_hint=(0.94, None), height=600,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do_save(*_):


            try:
                if not title_in.text.strip():
                    err.text = "Введіть назву"
                    return
                if chosen["vcat_id"] is None:
                    err.text = "Виберіть категорію"
                    return
                if not path_lbl.text.strip():
                    err.text = "Оберіть файл відео"
                    return

                from pathlib import Path as _P
                src_file = _P(path_lbl.text.strip())
                if not src_file.exists():
                    err.text = "Файл не знайдено"
                    return
                videos_dir = _P(__file__).resolve().parents[2] / "data" / "videos"
                videos_dir.mkdir(parents=True, exist_ok=True)


                dst = videos_dir / src_file.name
                try:
                    if str(src_file.resolve()) != str(dst.resolve()):
                        import shutil
                        shutil.copy2(src_file, dst)
                except Exception as exc:
                    err.text = f"Не вдалося скопіювати: {exc}"
                    return
                file_path = f"data/videos/{src_file.name}"

                description = desc_in.text.strip()
                try:
                    video_id = VideoRepo.upload(
                        trainer_id=Session.user_id,
                        vcat_id=chosen["vcat_id"],
                        title=title_in.text.strip(),
                        description=description,
                        file_path=file_path,
                        thumbnail_path="",
                        duration_sec=0,
                    )
                except Exception as exc:
                    err.text = f"Помилка БД: {exc}"
                    return


                try:
                    from ..database.thumbnails import extract_first_frame
                    thumb_rel = extract_first_frame(dst, video_id)
                    if thumb_rel:
                        VideoRepo.set_thumbnail(video_id, thumb_rel)
                except Exception:
                    pass

                if description:
                    try:
                        CommentRepo.add(video_id, Session.user_id, description, None)
                    except Exception:
                        pass
                popup.dismiss()
                self.manager.go("video_feed")
            except Exception as exc:
                err.text = f"Несподівана помилка: {exc}"
        save.bind(on_release=do_save)
        popup.open()

    def _open_file_picker(self, target_input):
        fc = FileChooserListView(filters=["*.mp4", "*.MP4", "*.mov", "*.MOV", "*.webm"],
                                 path=str(Path.home()))
        wrap = BoxLayout(orientation="vertical", spacing=6, padding=6)
        wrap.add_widget(fc)
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=46, spacing=6)
        ok = NeonButton(text="ВИБРАТИ")
        cancel = GhostButton(text="СКАСУВАТИ")
        row.add_widget(cancel)
        row.add_widget(ok)
        wrap.add_widget(row)
        popup = Popup(title="Вибір відео-файлу", content=wrap,
                      size_hint=(0.95, 0.9),
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        def on_ok(*_):
            if fc.selection:
                target_input.text = fc.selection[0]
            popup.dismiss()
        ok.bind(on_release=on_ok)
        cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _new_class_dialog(self, *_):
        body = BoxLayout(orientation="vertical", padding=12, spacing=8)
        body.add_widget(Label(text="[b]Створити нове заняття[/b]", markup=True,
                              color=theme.NEON_CYAN, font_size="14sp",
                              size_hint_y=None, height=24))
        title_in = TextInput(hint_text="Назва заняття (наприклад: Ранкова йога)",
                             multiline=False, size_hint_y=None, height=44,
                             background_color=[1, 1, 1, 0.06],
                             foreground_color=theme.TEXT_PRIMARY,
                             cursor_color=theme.NEON_CYAN)
        body.add_widget(title_in)

        body.add_widget(Label(text="Категорія:", color=theme.TEXT_SECONDARY,
                              font_size="12sp", size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        cat_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False,
                                size_hint_y=None, height=42, bar_width=0)
        cat_row = BoxLayout(orientation="horizontal", spacing=6, size_hint_x=None)
        cat_row.bind(minimum_width=cat_row.setter("width"))
        cats = ScheduleRepo.categories()
        chosen_cat = {"id": cats[0]["cat_id"] if cats else None}
        cat_chips = []
        def pick_cat(cid):
            chosen_cat["id"] = cid
            for ch in cat_chips:
                ch.set_active(ch.vcat_id == cid)
        for c in cats:
            ch = _Chip(c["name"], c["cat_id"], active=(c["cat_id"] == chosen_cat["id"]),
                       on_choose=pick_cat)
            cat_chips.append(ch)
            cat_row.add_widget(ch)
        cat_scroll.add_widget(cat_row)
        body.add_widget(cat_scroll)

        body.add_widget(Label(text="Зал:", color=theme.TEXT_SECONDARY,
                              font_size="12sp", size_hint_y=None, height=18,
                              halign="left", valign="middle"))
        room_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False,
                                 size_hint_y=None, height=42, bar_width=0)
        room_row = BoxLayout(orientation="horizontal", spacing=6, size_hint_x=None)
        room_row.bind(minimum_width=room_row.setter("width"))
        rooms = ScheduleRepo.rooms()
        chosen_room = {"id": rooms[0]["room_id"] if rooms else None,
                       "cap": rooms[0]["capacity"] if rooms else 20}
        room_chips = []
        def pick_room(rid):
            chosen_room["id"] = rid
            chosen_room["cap"] = next(r["capacity"] for r in rooms if r["room_id"] == rid)
            for ch in room_chips:
                ch.set_active(ch.vcat_id == rid)
        for r in rooms:
            ch = _Chip(r["name"], r["room_id"], active=(r["room_id"] == chosen_room["id"]),
                       on_choose=pick_room)
            room_chips.append(ch)
            room_row.add_widget(ch)
        room_scroll.add_widget(room_row)
        body.add_widget(room_scroll)

        dt_row = BoxLayout(orientation="horizontal", spacing=6,
                           size_hint_y=None, height=44)
        date_in = TextInput(hint_text="Дата YYYY-MM-DD",
                            text=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                            multiline=False, size_hint_x=0.5,
                            background_color=[1, 1, 1, 0.06],
                            foreground_color=theme.TEXT_PRIMARY,
                            cursor_color=theme.NEON_CYAN)
        time_in = TextInput(hint_text="Час HH:MM", text="10:00",
                            multiline=False, size_hint_x=0.3,
                            background_color=[1, 1, 1, 0.06],
                            foreground_color=theme.TEXT_PRIMARY,
                            cursor_color=theme.NEON_CYAN)
        dur_in = TextInput(hint_text="Хв", text="60",
                           multiline=False, size_hint_x=0.2,
                           background_color=[1, 1, 1, 0.06],
                           foreground_color=theme.TEXT_PRIMARY,
                           cursor_color=theme.NEON_CYAN)
        dt_row.add_widget(date_in)
        dt_row.add_widget(time_in)
        dt_row.add_widget(dur_in)
        body.add_widget(dt_row)

        err = Label(text="", color=theme.DANGER_RED, font_size="12sp",
                    size_hint_y=None, height=18)
        body.add_widget(err)

        actions = BoxLayout(orientation="horizontal", spacing=8,
                            size_hint_y=None, height=46)
        save = NeonButton(text="СТВОРИТИ")
        cancel = GhostButton(text="СКАСУВАТИ")
        actions.add_widget(cancel)
        actions.add_widget(save)
        body.add_widget(actions)

        popup = Popup(title="", content=body, size_hint=(0.94, None), height=520,
                      background_color=theme.BG_SURFACE,
                      separator_color=theme.NEON_CYAN,
                      title_color=theme.TEXT_PRIMARY)
        cancel.bind(on_release=lambda *_: popup.dismiss())

        def do_save(*_):
            try:
                start = datetime.strptime(
                    f"{date_in.text.strip()} {time_in.text.strip()}",
                    "%Y-%m-%d %H:%M")
                end = start + timedelta(minutes=int(dur_in.text.strip()))
            except Exception:
                err.text = "Некоректний формат дати/часу/тривалості"
                return
            if not title_in.text.strip():
                err.text = "Введіть назву"
                return
            ScheduleRepo.add_class(
                cat_id=chosen_cat["id"],
                trainer_id=Session.user_id,
                room_id=chosen_room["id"],
                title=title_in.text.strip(),
                start_time=start.isoformat(),
                end_time=end.isoformat(),
                capacity=chosen_room.get("cap", 20),
            )
            popup.dismiss()
            self.on_enter()
        save.bind(on_release=do_save)
        popup.open()

class _Chip(ButtonBehavior, Label):
    def __init__(self, label: str, vcat_id, active: bool, on_choose, **kw):
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (130, 36))
        kw.setdefault("font_size", "12sp")
        kw.setdefault("padding", (12, 6))
        kw.setdefault("bold", True)
        super().__init__(text=label, **kw)
        self.vcat_id = vcat_id
        self._on_choose = on_choose
        from .. import theme as _th
        active_bg = list(_th.NEON_CYAN[:3]) + [0.18]
        with self.canvas.before:
            self._bg_c = Color(*(active_bg if active else (1, 1, 1, 0.04)))
            self._bg = RoundedRectangle(radius=[14])
            self._brd_c = Color(*(list(_th.NEON_CYAN) if active else (1, 1, 1, 0.12)))
            self._brd = Line(width=1.2, rounded_rectangle=(0, 0, 0, 0, 14))
        self.color = _th.NEON_CYAN if active else _th.TEXT_SECONDARY
        self.bind(size=self._sync, pos=self._sync, texture_size=self._tx)

    def _tx(self, *_):
        self.width = max(90, self.texture_size[0] + 28)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._brd.rounded_rectangle = (*self.pos, *self.size, 14)

    def set_active(self, active: bool):
        from .. import theme as _th
        active_bg = list(_th.NEON_CYAN[:3]) + [0.18]
        self._bg_c.rgba = active_bg if active else (1, 1, 1, 0.04)
        self._brd_c.rgba = list(_th.NEON_CYAN) if active else (1, 1, 1, 0.12)
        self.color = _th.NEON_CYAN if active else _th.TEXT_SECONDARY

    def on_release(self):
        self._on_choose(self.vcat_id)
