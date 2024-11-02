from bot.handlers.base import EventHandler


class ContinueHandler(EventHandler):
    def handle(self):
        self.send_text("This is not implemented yet 😢")
