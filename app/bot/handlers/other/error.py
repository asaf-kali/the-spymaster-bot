from bot.handlers.other.event_handler import EventHandler
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class ErrorHandler(EventHandler):
    def handle(self):
        log.warning("Using telegram bot handling mechanism, check why error was not handled in callback.")
        self.on_error(self.context.error)
