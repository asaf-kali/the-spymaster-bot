from typing import Any, Callable, Dict, Optional, Type

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)
from the_spymaster_api import TheSpymasterClient
from the_spymaster_util import get_logger

from bot.config import get_config
from bot.handlers import (
    ConfigDifficultyHandler,
    ConfigLanguageHandler,
    ConfigModelHandler,
    ConfigSolverHandler,
    ContinueGetIdHandler,
    ContinueHandler,
    CustomHandler,
    EventHandler,
    FallbackHandler,
    GetSessionsHandler,
    HelpMessageHandler,
    LoadModelsHandler,
    ProcessMessageHandler,
    StartEventHandler,
    TestingHandler,
)
from bot.models import BotState, Session, SessionId

log = get_logger(__name__)


class TheSpymasterBot:
    def __init__(self, base_backend: str = None):
        self.sessions: Dict[SessionId, Session] = {}
        self.client = TheSpymasterClient(base_backend=base_backend)

    def set_session(self, session_id: SessionId, session: Optional[Session]):
        if not session:
            self.sessions.pop(session_id, None)
            log.update_context(game_id=None)
        else:
            log.update_context(game_id=session.game_id)
        self.sessions[session_id] = session  # type: ignore

    def get_session(self, session_id: SessionId) -> Optional[Session]:
        return self.sessions.get(session_id)

    def generate_callback(self, handler_type: Type[EventHandler]) -> Callable[[Update, CallbackContext], Any]:
        return handler_type.generate_callback(bot=self)

    def listen(self) -> None:
        log.info("Starting bot...")
        config = get_config()
        updater = Updater(config.telegram_token)
        dispatcher = updater.dispatcher

        start_handler = CommandHandler("start", self.generate_callback(StartEventHandler), run_async=True)
        custom_handler = CommandHandler("custom", self.generate_callback(CustomHandler), run_async=True)
        config_language_handler = MessageHandler(
            Filters.text, self.generate_callback(ConfigLanguageHandler), run_async=True
        )
        config_difficulty_handler = MessageHandler(
            Filters.text, self.generate_callback(ConfigDifficultyHandler), run_async=True
        )
        config_model_handler = MessageHandler(Filters.text, self.generate_callback(ConfigModelHandler), run_async=True)
        config_solver_handler = MessageHandler(
            Filters.text, self.generate_callback(ConfigSolverHandler), run_async=True
        )
        continue_game_handler = CommandHandler("continue", self.generate_callback(ContinueHandler), run_async=True)
        continue_get_id_handler = MessageHandler(
            Filters.text, self.generate_callback(ContinueGetIdHandler), run_async=True
        )
        fallback_handler = CommandHandler("quit", self.generate_callback(FallbackHandler), run_async=True)
        help_message_handler = CommandHandler("help", self.generate_callback(HelpMessageHandler), run_async=True)
        get_sessions_handler = CommandHandler("sessions", self.generate_callback(GetSessionsHandler), run_async=True)
        load_models_handler = CommandHandler("load_models", self.generate_callback(LoadModelsHandler), run_async=True)
        testing_handler = CommandHandler("test", self.generate_callback(TestingHandler), run_async=True)
        process_message_handler = MessageHandler(
            Filters.text & ~Filters.command, self.generate_callback(ProcessMessageHandler), run_async=True
        )

        conv_handler = ConversationHandler(
            entry_points=[
                start_handler,
                custom_handler,
                continue_game_handler,
                help_message_handler,
                get_sessions_handler,
                load_models_handler,
                testing_handler,
            ],
            states={
                BotState.ConfigLanguage: [config_language_handler],
                BotState.ConfigDifficulty: [config_difficulty_handler, fallback_handler],
                BotState.ConfigModel: [config_model_handler, fallback_handler],
                BotState.ConfigSolver: [config_solver_handler, fallback_handler],
                BotState.ContinueGetId: [continue_get_id_handler],
                BotState.Playing: [process_message_handler],
            },
            fallbacks=[fallback_handler],
            allow_reentry=True,
        )

        dispatcher.add_handler(conv_handler)
        dispatcher.add_handler(process_message_handler)

        updater.start_polling()
        updater.idle()
