from bot.handlers.other.event_handler import EventHandler
from bot.handlers.parse.parse_done_handler import ParseDoneHandler
from bot.models import BotState

# Fixing


class ParseFixesHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower().strip()
        if text == "/done":
            return self.trigger(ParseDoneHandler)
        _, word = text.split()
        words = self.parsing_state.words
        word_index = words.index(word)
        self.update_parsing_state(fix_index=word_index)
        # Fix word
        self.send_text("OK, send me the correct word:")
        return BotState.PARSE_FIX
