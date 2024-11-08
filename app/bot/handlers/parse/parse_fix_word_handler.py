from bot.handlers.other.event_handler import EventHandler
from bot.models import BotState

# Fixing


class ParseFixWordHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower().strip()
        parsing_state = self.parsing_state
        parsing_state.words[parsing_state.fix_index] = text
        self.update_session(parsing_state=parsing_state)
        self.send_parsing_state()
        return BotState.PARSE_FIXES
