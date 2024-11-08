from bot.handlers.other.event_handler import EventHandler
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)

# Fixes -> Done


class ParseDoneHandler(EventHandler):
    def handle(self):
        self.send_text("OK, I'm done! 🎉")
