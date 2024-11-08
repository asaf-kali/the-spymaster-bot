from bot.handlers.other.event_handler import EventHandler
from bot.models import BotState, ParsingState, Session
from telegram import ReplyKeyboardMarkup
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)

# Entrypoint -> Language

LANGUAGES_CODES = {
    "hebrew": "heb",
    "english": "eng",
}


class ParseHandler(EventHandler):
    def handle(self):
        session = Session(parsing_state=ParsingState())
        self.set_session(session=session)
        # Language selection
        keyboard = _build_language_options_keyboard()
        self.send_markdown("🔤 Pick cards language:", reply_markup=keyboard)
        return BotState.PARSE_LANGUAGE


def _build_language_options_keyboard() -> ReplyKeyboardMarkup:
    options = [language.title() for language in LANGUAGES_CODES.keys()]
    keyboard = ReplyKeyboardMarkup([options], one_time_keyboard=True)
    return keyboard
