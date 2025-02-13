from bot.handlers.other.event_handler import EventHandler
from bot.models import BotState
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class TestingHandler(EventHandler):
    def handle(self):
        text = remove_command(self.update.message.text)
        log.info(f"Testing handler with text: '{text}'")
        if "error" in text:
            raise ValueError(f"This is an error: {text}")
        if not text:
            self.send_text("Hello!")
        else:
            self.send_text(f"Hello, {text}!")
        return BotState.CONFIG_SOLVER


def remove_command(text: str) -> str:
    """
    Given a text like "/example 123 xyz", returns "123 xyz".
    """
    split = text.split(maxsplit=1)
    if len(split) == 1:
        return ""
    return split[1]
