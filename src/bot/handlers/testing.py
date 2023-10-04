from the_spymaster_util.logger import get_logger

from bot.handlers.base import EventHandler
from bot.models import BotState

log = get_logger(__name__)


class TestingHandler(EventHandler):
    def handle(self):
        text = remove_command(self.update.message.text)
        log.info(f"Testing handler with text: '{text}'")
        if "error" in text:
            raise ValueError(f"This is an error: {text}")
        self.send_text("Hello")
        return BotState.CONFIG_SOLVER


def remove_command(text: str) -> str:
    """
    Given a text like "/example 123 xyz", returns "123 xyz"
    """
    return text.split(maxsplit=1)[1]
