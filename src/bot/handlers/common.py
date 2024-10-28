from typing import List

import sentry_sdk
from codenames.game.color import TeamColor
from codenames.game.move import GivenGuess
from codenames.game.player import PlayerRole
from codenames.game.state import GameState
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)

SUPPORTED_LANGUAGES = ["hebrew", "english"]


def is_blue_guesser_turn(state: GameState):
    return state.current_team_color == TeamColor.BLUE and state.current_player_role == PlayerRole.GUESSER


def get_given_guess_result_message_text(given_guess: GivenGuess) -> str:
    card = given_guess.guessed_card
    result = "Correct! ✅" if given_guess.correct else "Wrong! ❌"
    return f"Card '*{card.word}*' is {card.color.emoji}, {result}"


def title_list(strings: List[str]) -> List[str]:
    return [s.title() for s in strings]


def enrich_sentry_context(**kwargs):
    for k, v in log.context.items():
        sentry_sdk.set_tag(k, v)
    for k, v in kwargs.items():
        sentry_sdk.set_tag(k, v)
