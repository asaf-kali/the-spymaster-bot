from typing import Any, Callable, Optional, Type

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    DictPersistence,
    Dispatcher,
    Filters,
    MessageHandler,
    Updater,
)
from the_spymaster_api import TheSpymasterClient
from the_spymaster_solvers_api.structs import LoadModelsRequest, LoadModelsResponse
from the_spymaster_util.logger import get_logger

from bot.handlers import (
    ConfigDifficultyHandler,
    ConfigLanguageHandler,
    ConfigModelHandler,
    ConfigSolverHandler,
    ContinueGetIdHandler,
    ContinueHandler,
    CustomHandler,
    ErrorHandler,
    EventHandler,
    FallbackHandler,
    GetSessionsHandler,
    HelpMessageHandler,
    LoadModelsHandler,
    NextMoveHandler,
    ProcessMessageHandler,
    StartEventHandler,
    TestingHandler,
)
from bot.models import AVAILABLE_MODELS, BotState
from persistence.dynamo_db_persistence import DynamoDbPersistence

log = get_logger(__name__)


class TheSpymasterBot:
    def __init__(self, telegram_token: str, base_url: Optional[str] = None, dynamo_persistence: bool = False):
        self.api_client = TheSpymasterClient(base_url=base_url)
        persistence = DynamoDbPersistence() if dynamo_persistence else DictPersistence()
        self.updater = Updater(token=telegram_token, persistence=persistence)
        self._construct_updater()

    @property
    def dispatcher(self) -> Dispatcher:
        return self.updater.dispatcher  # type: ignore

    def generate_callback(self, handler_type: Type[EventHandler]) -> Callable[[Update, CallbackContext], Any]:
        return handler_type.generate_callback(bot=self)

    def process_update(self, update: dict):
        action = update.get("action")
        if action == "warmup":
            return self.handle_warmup()
        parsed_update = self.parse_update(update)
        return self.dispatcher.process_update(parsed_update)

    def handle_warmup(self) -> dict:
        log.update_context(action="warmup")
        log.info("Warming up...")
        response = self.send_load_models_request()
        return response.dict()

    def send_load_models_request(self) -> LoadModelsResponse:
        request = LoadModelsRequest(model_identifiers=AVAILABLE_MODELS, load_default_models=False)
        response = self.api_client.load_models(request)
        return response

    def parse_update(self, update: dict) -> Optional[Update]:
        return Update.de_json(update, bot=self.updater.bot)  # type: ignore

    def _construct_updater(self):  # pylint: disable=too-many-locals
        log.info("Setting up bot...")
        start_handler = CommandHandler("start", self.generate_callback(StartEventHandler))
        custom_handler = CommandHandler("custom", self.generate_callback(CustomHandler))
        config_language_handler = MessageHandler(Filters.text, self.generate_callback(ConfigLanguageHandler))
        config_solver_handler = MessageHandler(Filters.text, self.generate_callback(ConfigSolverHandler))
        config_difficulty_handler = MessageHandler(Filters.text, self.generate_callback(ConfigDifficultyHandler))
        config_model_handler = MessageHandler(Filters.text, self.generate_callback(ConfigModelHandler))
        continue_game_handler = CommandHandler("continue", self.generate_callback(ContinueHandler))
        continue_get_id_handler = MessageHandler(Filters.text, self.generate_callback(ContinueGetIdHandler))
        fallback_handler = CommandHandler("quit", self.generate_callback(FallbackHandler))
        help_message_handler = CommandHandler("help", self.generate_callback(HelpMessageHandler))
        get_sessions_handler = CommandHandler("sessions", self.generate_callback(GetSessionsHandler))
        load_models_handler = CommandHandler("load_models", self.generate_callback(LoadModelsHandler))
        testing_handler = CommandHandler("test", self.generate_callback(TestingHandler))
        process_message_handler = MessageHandler(
            Filters.text & ~Filters.command, self.generate_callback(ProcessMessageHandler)
        )
        next_move_handler = CommandHandler("next_move", self.generate_callback(NextMoveHandler))
        error_handler = self.generate_callback(ErrorHandler)

        conv_handler = ConversationHandler(
            name="main",
            entry_points=[
                help_message_handler,
                start_handler,
                custom_handler,
                next_move_handler,
                load_models_handler,
                testing_handler,
                get_sessions_handler,
                continue_game_handler,
            ],
            states={
                BotState.CONFIG_LANGUAGE: [config_language_handler],
                BotState.CONFIG_SOLVER: [config_solver_handler, fallback_handler],
                BotState.CONFIG_DIFFICULTY: [config_difficulty_handler, fallback_handler],
                BotState.CONFIG_MODEL: [config_model_handler, fallback_handler],
                BotState.CONTINUE_GET_ID: [continue_get_id_handler],
                BotState.PLAYING: [process_message_handler],
            },
            fallbacks=[fallback_handler],
            allow_reentry=True,
            persistent=True,
        )

        self.dispatcher.add_handler(conv_handler)
        self.dispatcher.add_handler(process_message_handler)
        self.dispatcher.add_error_handler(error_handler)  # type: ignore

    def poll(self) -> None:
        self.updater.start_polling()
        self.updater.idle()
