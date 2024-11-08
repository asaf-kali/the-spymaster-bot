from bot.handlers.other.event_handler import EventHandler
from bot.models import BotState, ParsingState
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)

# Entrypoint -> Language

LANGUAGES_CODES = {
    "hebrew": "heb",
    "hnglish": "eng",
    "hussian": "rus",
}


class ParseHandler(EventHandler):
    def handle(self):
        keyboard = _build_language_options_keyboard()
        parsing_state = ParsingState()
        self.update_session(parsing_state=parsing_state)
        # Language selection
        self.send_markdown("🔤 Pick cards language:", reply_markup=keyboard)
        return BotState.PARSE_LANGUAGE


def _build_language_options_keyboard() -> list[str]:
    keyboard = [language.title() for language in LANGUAGES_CODES.keys()]
    return keyboard
