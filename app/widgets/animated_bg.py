import math
import random
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.properties import ListProperty

from .. import theme

class AnimatedBackground(FloatLayout):
    _particles: list[dict] = ListProperty([])

    def __init__(self, density: int = 24, **kwargs):
        super().__init__(**kwargs)
        self._density = density
        with self.canvas.before:

            self._grad_instructions = []
            stops = 16
            for i in range(stops):
                t = i / (stops - 1)
                r = theme.BG_DEEP[0] + (theme.BG_MID[0] - theme.BG_DEEP[0]) * t
                g = theme.BG_DEEP[1] + (theme.BG_MID[1] - theme.BG_DEEP[1]) * t
                b = theme.BG_DEEP[2] + (theme.BG_MID[2] - theme.BG_DEEP[2]) * t
                c = Color(r, g, b, 1)
                rect = Rectangle(pos=(0, 0), size=(1, 1))
                self._grad_instructions.append((c, rect, t))

            self._particle_instructions = []

        self.bind(size=self._relayout, pos=self._relayout)
        self._spawn_particles()
        Clock.schedule_interval(self._tick, 1 / 30)

    def _spawn_particles(self):
        self._particles = []
        for _ in range(self._density):
            self._particles.append({
                "x": random.random(),
                "y": random.random(),
                "vx": (random.random() - 0.5) * 0.0006,
                "vy": (random.random() - 0.5) * 0.0006,
                "r": random.randint(2, 6),
                "phase": random.random() * math.tau,
                "speed": 0.6 + random.random() * 1.2,
                "hue": random.choice(["cyan", "magenta"]),
            })

    def _relayout(self, *_):
        w, h = self.size
        x, y = self.pos
        stops = len(self._grad_instructions)
        for i, (col, rect, t) in enumerate(self._grad_instructions):
            band_h = h / stops
            rect.pos = (x, y + h - (i + 1) * band_h)
            rect.size = (w, band_h + 1)

    def _tick(self, dt):

        self.canvas.before.remove_group("particles")
        with self.canvas.before:
            self.canvas.before.add
            for p in self._particles:
                p["x"] += p["vx"] * dt * 30
                p["y"] += p["vy"] * dt * 30
                p["phase"] += dt * p["speed"]
                if p["x"] < -0.05: p["x"] = 1.05
                if p["x"] >  1.05: p["x"] = -0.05
                if p["y"] < -0.05: p["y"] = 1.05
                if p["y"] >  1.05: p["y"] = -0.05
                pulse = 0.45 + 0.25 * math.sin(p["phase"])
                col = theme.NEON_CYAN if p["hue"] == "cyan" else theme.NEON_MAGENTA
                Color(col[0], col[1], col[2], 0.18 * pulse, group="particles")
                d = p["r"] * (2.0 + 0.8 * math.sin(p["phase"]))
                Ellipse(
                    pos=(self.x + p["x"] * self.width - d / 2,
                         self.y + p["y"] * self.height - d / 2),
                    size=(d, d), group="particles")
