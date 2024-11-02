from bot.handlers.base import EventHandler
from bot.models import AVAILABLE_MODELS, BadMessageError, BotState
from telegram import ReplyKeyboardMarkup
from the_spymaster_solvers_api.structs import Difficulty
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class ConfigDifficultyHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        log.info(f"Setting difficulty: '{text}'")
        difficulty = parse_difficulty(text)
        self.update_game_config(difficulty=difficulty)
        keyword = build_models_keyboard(language=self.session.config.language)
        self.send_text("🧠 Pick language model:", reply_markup=keyword)
        return BotState.CONFIG_MODEL


def build_models_keyboard(language: str):
    language_models = [model for model in AVAILABLE_MODELS if model.language == language]
    model_names = [model.model_name for model in language_models]
    keyboard = ReplyKeyboardMarkup([model_names], one_time_keyboard=True)
    return keyboard


def parse_difficulty(text: str) -> Difficulty:
    try:
        return Difficulty(text)
    except ValueError as e:
        raise BadMessageError(f"Unknown difficulty: '*{text}*'") from e
