from bot.handlers.other.event_handler import EventHandler
from bot.models import BotState

# Fixing


class ParseFixesHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower().strip()
        if text == "/done":
            return
        self.send_text("🧩 Please send me a picture of the fixed board:")
        return BotState.PARSE_BOARD
