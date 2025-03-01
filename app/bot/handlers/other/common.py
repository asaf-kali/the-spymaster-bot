import sentry_sdk
from codenames.generic.move import GivenGuess
from codenames.generic.player import PlayerRole
from codenames.mini.state import MiniGameState
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)

SUPPORTED_LANGUAGES = ["hebrew", "english"]


def is_operative_turn(state: MiniGameState):
    return state.current_player_role == PlayerRole.OPERATIVE


def get_given_guess_result_message_text(given_guess: GivenGuess) -> str:
    card = given_guess.guessed_card
    result = "Correct! ✅" if given_guess.correct else "Wrong! ❌"
    assert card.color
    return f"Card '*{card.word}*' is {card.color.emoji}, {result}"


def title_list(strings: list[str]) -> list[str]:
    return [s.title() for s in strings]


def enrich_sentry_context(**kwargs):
    for k, v in log.context.items():
        sentry_sdk.set_tag(k, v)
    for k, v in kwargs.items():
        sentry_sdk.set_tag(k, v)
