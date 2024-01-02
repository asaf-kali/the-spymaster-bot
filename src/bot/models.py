from enum import IntEnum, auto
from typing import Optional

from codenames.game.color import CardColor, TeamColor
from codenames.game.move import PASS_GUESS, QUIT_GAME
from codenames.game.winner import WinningReason
from pydantic import BaseModel
from the_spymaster_api.structs import ModelIdentifier
from the_spymaster_solvers_client.structs import Difficulty, Solver

BLUE_EMOJI = CardColor.BLUE.emoji
RED_EMOJI = CardColor.RED.emoji
WIN_REASON_TO_EMOJI = {
    WinningReason.TARGET_SCORE_REACHED: "🤓",
    WinningReason.OPPONENT_HIT_BLACK: "😵",
    WinningReason.OPPONENT_QUIT: "🥴",
}
COMMAND_TO_INDEX = {"-pass": PASS_GUESS, "-quit": QUIT_GAME}
AVAILABLE_MODELS = [
    ModelIdentifier(language="english", model_name="wiki-50", is_stemmed=False),
    # ModelIdentifier(language="english", model_name="google-300", is_stemmed=False),
    # ModelIdentifier(language="hebrew", model_name="twitter", is_stemmed=False),
    # ModelIdentifier(language="hebrew", model_name="ft-200", is_stemmed=False),
    # ModelIdentifier(language="hebrew", model_name="skv-cbow-30", is_stemmed=True),
    # ModelIdentifier(language="hebrew", model_name="skv-cbow-150", is_stemmed=True),
    ModelIdentifier(language="hebrew", model_name="skv-ft-150", is_stemmed=True),
    # ModelIdentifier(language="hebrew", model_name="ft-30", is_stemmed=False),
    # ModelIdentifier(language="hebrew", model_name="cbow-30", is_stemmed=False),
]


class BadMessageError(Exception):
    pass


class BotState(IntEnum):
    ENTRY = auto()
    CONFIG_LANGUAGE = auto()
    CONFIG_SOLVER = auto()
    CONFIG_DIFFICULTY = auto()
    CONFIG_MODEL = auto()
    CONTINUE_GET_ID = auto()
    PLAYING = auto()


class GameConfig(BaseModel):  # Move to backend api?
    language: str = "english"
    difficulty: Difficulty = Difficulty.EASY
    solver: Solver = Solver.NAIVE
    model_identifier: Optional[ModelIdentifier] = None
    first_team: Optional[TeamColor] = TeamColor.BLUE

    class Config:
        frozen = True


class Session(BaseModel):
    game_id: Optional[str]
    config: Optional[GameConfig]
    last_keyboard_message_id: Optional[int]

    class Config:
        frozen = True

    @property
    def is_game_active(self) -> bool:
        return self.game_id is not None
