from bot.handlers.other.common import SUPPORTED_LANGUAGES, title_list
from bot.handlers.other.event_handler import EventHandler
from bot.models import BotState, GameConfig, Session
from telegram import ReplyKeyboardMarkup
from the_spymaster_solvers_api.structs import Difficulty


class CustomHandler(EventHandler):
    def handle(self):
        game_config = GameConfig(difficulty=Difficulty.HARD)
        session = Session(config=game_config)
        self.set_session(session=session)
        keyboard = build_language_keyboard()
        self.send_text("🌍 Pick language:", reply_markup=keyboard)
        return BotState.CONFIG_LANGUAGE


def build_language_keyboard():
    languages = title_list(SUPPORTED_LANGUAGES)
    return ReplyKeyboardMarkup([languages], one_time_keyboard=True)
