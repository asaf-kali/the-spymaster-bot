from typing import List

import sentry_sdk
from codenames.classic.color import ClassicTeam
from codenames.classic.state import ClassicGameState
from codenames.generic.move import GivenGuess
from codenames.generic.player import PlayerRole
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)

SUPPORTED_LANGUAGES = ["hebrew", "english"]


def is_blue_operative_turn(state: ClassicGameState):
    return state.current_team == ClassicTeam.BLUE and state.current_player_role == PlayerRole.OPERATIVE


def get_given_guess_result_message_text(given_guess: GivenGuess) -> str:
    card = given_guess.guessed_card
    result = "Correct! ✅" if given_guess.correct else "Wrong! ❌"
    assert card.color
    return f"ClassicCard '*{card.word}*' is {card.color.emoji}, {result}"


def title_list(strings: List[str]) -> List[str]:
    return [s.title() for s in strings]


def enrich_sentry_context(**kwargs):
    for k, v in log.context.items():
        sentry_sdk.set_tag(k, v)
    for k, v in kwargs.items():
        sentry_sdk.set_tag(k, v)
