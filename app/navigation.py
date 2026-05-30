from kivy.uix.screenmanager import ScreenManager, SlideTransition, FadeTransition

from .auth import Session

class AppNav(ScreenManager):
    def __init__(self, **kw):
        kw.setdefault("transition", SlideTransition(direction="left", duration=0.32))
        super().__init__(**kw)

    def go(self, name: str, direction: str = "left"):
        self.transition = SlideTransition(direction=direction, duration=0.32)
        self.current = name

    def fade_to(self, name: str):
        self.transition = FadeTransition(duration=0.4)
        self.current = name

    def go_home(self):
        role = Session.role
        if role == "client":
            self.fade_to("home_client")
        elif role == "trainer":
            self.fade_to("home_trainer")
        else:
            self.fade_to("home_admin")
