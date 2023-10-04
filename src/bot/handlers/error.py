from the_spymaster_util.logger import get_logger

from bot.handlers.base import EventHandler

log = get_logger(__name__)


class ErrorHandler(EventHandler):
    def handle(self):
        log.warning("Using telegram bot handling mechanism, check why error was not handled in callback.")
        self.handle_error(self.context.error)
