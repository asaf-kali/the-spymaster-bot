from telegram import ReplyKeyboardMarkup
from the_spymaster_solvers_client.structs import Difficulty, Solver
from the_spymaster_util.logger import get_logger

from bot.handlers.base import EventHandler
from bot.handlers.common import title_list
from bot.handlers.start import StartEventHandler
from bot.models import BadMessageError, BotState

log = get_logger(__name__)


class ConfigSolverHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.upper()
        try:
            solver = Solver[text]
        except Exception as e:
            raise BadMessageError(f"Unknown solver: '*{text}*'") from e
        log.info(f"Setting solver: '{solver}'")
        self.update_game_config(solver=solver)
        if solver == Solver.GPT:
            return self.trigger(StartEventHandler)
        keyboard = build_difficulty_keyboard()
        self.send_text("🥵 Pick difficulty:", reply_markup=keyboard)
        return BotState.CONFIG_DIFFICULTY


def build_difficulty_keyboard():
    difficulties = title_list([Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD])
    keyboard = ReplyKeyboardMarkup([difficulties], one_time_keyboard=True)
    return keyboard
