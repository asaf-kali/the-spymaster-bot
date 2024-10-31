from the_spymaster_util.logger import get_logger

from bot.handlers.base import EventHandler

log = get_logger(__name__)


class HelpMessageHandler(EventHandler):
    def handle(self):
        log.info("Sending help message")
        text = """Welcome! I'm *The Spymaster* 🕵🏼‍♂️
/start - start a new game.
/custom - start a new game with custom configurations.
/help - show this message.
Under development: 👨🏻‍💻
/parse - get help with your camera.
/continue - continue an old game.

How to play:
You are the blue guesser. The bot will play all other roles. \
When the blue hinter sends a hint, you can reply with a card index (1-25), \
or just click the word on the keyboard. \
Use '-pass' and '-quit' to pass the turn and quit the game.
"""
        self.send_markdown(text)
