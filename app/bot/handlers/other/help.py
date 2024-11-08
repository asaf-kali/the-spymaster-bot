from bot.handlers.other.event_handler import EventHandler
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class HelpMessageHandler(EventHandler):
    def handle(self):
        log.info("Sending help message")
        text = """Welcome! I'm *The Spymaster* 🕵🏼‍♂️
/start - start a new game.
/custom - start a new game with custom configurations.
/help - show this message.
In development: 👨🏻‍💻
/parse - get help with your camera.

How to play:
You are the blue guesser. The bot will play all other roles. \
When the blue hinter sends a hint, you can reply with a card index (1-25), \
or just click the word on the keyboard. \
Use '-pass' and '-quit' to pass the turn and quit the game.
"""
        self.send_markdown(text)
