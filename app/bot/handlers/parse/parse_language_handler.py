from bot.handlers.other.event_handler import EventHandler
from bot.handlers.parse.parse_handler import LANGUAGES_CODES, log
from bot.models import BotState

# Language -> Map


class ParseLanguageHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        language_code = _get_language_code(text)
        log.info(f"Setting language: '{language_code}'")
        self.update_parsing_state(language=language_code)
        # Map parsing
        self.send_text("🗺️ Please send me a picture of the map:")
        return BotState.PARSE_MAP


def _get_language_code(text: str) -> str:
    text = text.lower().strip()
    if text in LANGUAGES_CODES:
        return LANGUAGES_CODES[text]
    log.info(f"Unknown language: '{text}'")
    language_code = text[:3]
    return language_code
