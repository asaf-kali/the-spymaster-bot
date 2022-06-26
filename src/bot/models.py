from enum import IntEnum, auto
from typing import Optional

from codenames.game import PASS_GUESS, QUIT_GAME, CardColor, GameState, WinningReason
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
    ModelIdentifier(language="hebrew", model_name="ft-30", is_stemmed=False),
    ModelIdentifier(language="hebrew", model_name="cbow-30", is_stemmed=False),
]


class BadMessageError(Exception):
    pass


class BotState(IntEnum):
    Entry = auto()
    ConfigLanguage = auto()
    ConfigDifficulty = auto()
    ConfigModel = auto()
    ConfigSolver = auto()
    ContinueGetId = auto()
    Playing = auto()


class SessionId(BaseModel):
    chat_id: int

    def __str__(self) -> str:
        return f"{self.chat_id}"

    def __hash__(self):
        return hash(self.json())


class GameConfig(BaseModel):  # Move to backend api?
    language: str = "english"
    difficulty: Difficulty = Difficulty.EASY
    solver: Solver = Solver.NAIVE
    model_identifier: Optional[ModelIdentifier] = None


class Session(BaseModel):
    game_id: Optional[int]
    state: Optional[GameState]
    last_keyboard_message: Optional[int]
    config: Optional[GameConfig]

    @property
    def is_game_active(self) -> bool:
        return self.state is not None and not self.state.is_game_over

    def clean_dict(self) -> dict:
        result = self.dict(exclude={"last_keyboard_message", "state"})
        result["is_game_active"] = self.is_game_active
        return result
