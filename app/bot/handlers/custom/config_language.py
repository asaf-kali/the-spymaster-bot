from bot.handlers.other.common import SUPPORTED_LANGUAGES
from bot.handlers.other.event_handler import EventHandler
from bot.models import BadMessageError, BotState
from telegram import ReplyKeyboardMarkup
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class ConfigLanguageHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        log.info(f"Setting language: '{text}'")
        language = parse_language(text)
        self.update_game_config(language=language)
        keyboard = build_solver_keyboard()
        self.send_text("🧮 Pick solver:", reply_markup=keyboard)
        return BotState.CONFIG_SOLVER


def build_solver_keyboard():
    solvers = ["Naive", "GPT"]
    return ReplyKeyboardMarkup([solvers], one_time_keyboard=True)


def parse_language(text: str) -> str:
    if text not in SUPPORTED_LANGUAGES:
        raise BadMessageError(f"Unknown language: '*{text}*'")
    return text
