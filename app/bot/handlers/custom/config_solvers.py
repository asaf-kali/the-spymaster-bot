from bot.handlers.gameplay.start import StartEventHandler
from bot.handlers.other.common import title_list
from bot.handlers.other.event_handler import EventHandler
from bot.models import BadMessageError, BotState
from telegram import ReplyKeyboardMarkup
from the_spymaster_solvers_api.structs import Difficulty, Solver
from the_spymaster_util.logger import get_logger

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
