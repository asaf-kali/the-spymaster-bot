from bot.handlers.gameplay.start import StartEventHandler
from bot.handlers.other.event_handler import EventHandler
from bot.models import AVAILABLE_MODELS, BadMessageError
from the_spymaster_solvers_api.structs import APIModelIdentifier
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class ConfigModelHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        log.info(f"Setting model: '{text}'")
        model_identifier = parse_model_identifier(language=self.session.config.language, model_name=text)
        self.update_game_config(model_identifier=model_identifier)
        return self.trigger(StartEventHandler)


def parse_model_identifier(language: str, model_name: str) -> APIModelIdentifier:
    for model in AVAILABLE_MODELS:
        if model.language == language and model.model_name == model_name:
            return model
    raise BadMessageError(f"Unknown model '*{model_name}*' for language '*{language}*'")
