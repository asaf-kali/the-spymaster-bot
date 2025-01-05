from enum import IntEnum
from typing import List, Optional

from codenames.classic.color import ClassicColor, ClassicTeam
from codenames.classic.winner import WinningReason
from codenames.generic.move import PASS_GUESS, QUIT_GAME
from pydantic import BaseModel
from the_spymaster_solvers_api.structs import APIModelIdentifier, Difficulty, Solver

BLUE_EMOJI = ClassicColor.BLUE.emoji
RED_EMOJI = ClassicColor.RED.emoji
WIN_REASON_TO_EMOJI = {
    WinningReason.TARGET_SCORE_REACHED: "🤓",
    WinningReason.OPPONENT_HIT_ASSASSIN: "😵",
    WinningReason.OPPONENT_QUIT: "🥴",
}
COMMAND_TO_INDEX = {"-pass": PASS_GUESS, "-quit": QUIT_GAME}
AVAILABLE_MODELS = [
    APIModelIdentifier(language="english", model_name="wiki-50", is_stemmed=False),
    # APIModelIdentifier(language="english", model_name="google-300", is_stemmed=False),
    # APIModelIdentifier(language="hebrew", model_name="twitter", is_stemmed=False),
    # APIModelIdentifier(language="hebrew", model_name="ft-200", is_stemmed=False),
    # APIModelIdentifier(language="hebrew", model_name="skv-cbow-30", is_stemmed=True),
    # APIModelIdentifier(language="hebrew", model_name="skv-cbow-150", is_stemmed=True),
    APIModelIdentifier(language="hebrew", model_name="skv-ft-150", is_stemmed=True),
    # APIModelIdentifier(language="hebrew", model_name="ft-30", is_stemmed=False),
    # APIModelIdentifier(language="hebrew", model_name="cbow-30", is_stemmed=False),
]


class BadMessageError(Exception):
    pass


class BotState(IntEnum):
    PLAYING = 30
    # Config
    CONFIG_LANGUAGE = 10
    CONFIG_SOLVER = 11
    CONFIG_DIFFICULTY = 12
    CONFIG_MODEL = 13
    # Parsing
    PARSE_LANGUAGE = 40
    PARSE_MAP = 41
    PARSE_BOARD = 42
    PARSE_FIXES = 43
    PARSE_FIX = 44
    # Other
    CONTINUE_GET_ID = 20


class GameConfig(BaseModel):  # Move to backend api?
    language: str = "english"
    difficulty: Difficulty = Difficulty.EASY
    solver: Solver = Solver.NAIVE
    model_identifier: Optional[APIModelIdentifier] = None
    first_team: Optional[ClassicTeam] = ClassicTeam.BLUE

    class Config:
        frozen = True


class ParsingState(BaseModel):
    language: Optional[str] = None
    card_colors: Optional[List[ClassicColor]] = None
    words: Optional[List[str]] = None
    fix_index: Optional[int] = None


class Session(BaseModel):
    game_id: Optional[str]
    config: Optional[GameConfig]
    parsing_state: Optional[ParsingState]
    last_keyboard_message_id: Optional[int]

    class Config:
        frozen = True

    @property
    def is_game_active(self) -> bool:
        return self.game_id is not None
