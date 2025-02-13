from typing import Any, Callable, Dict, Optional, Type

from bot.handlers.custom.config_difficulty import ConfigDifficultyHandler
from bot.handlers.custom.config_language import ConfigLanguageHandler
from bot.handlers.custom.config_model import ConfigModelHandler
from bot.handlers.custom.config_solvers import ConfigSolverHandler
from bot.handlers.custom.custom import CustomHandler
from bot.handlers.gameplay.next_move import NextMoveHandler
from bot.handlers.gameplay.process_message import ProcessMessageHandler
from bot.handlers.gameplay.start import StartEventHandler
from bot.handlers.internal.testing import TestingHandler
from bot.handlers.internal.warmup import WarmupHandler, handle_warmup
from bot.handlers.other.error import ErrorHandler
from bot.handlers.other.event_handler import EventHandler
from bot.handlers.other.fallback import FallbackHandler
from bot.handlers.other.help import HelpMessageHandler
from bot.handlers.parse.parse_board_handler import ParseBoardHandler
from bot.handlers.parse.parse_done_handler import ParseDoneHandler
from bot.handlers.parse.parse_fix_word_handler import ParseFixWordHandler
from bot.handlers.parse.parse_fixing_handler import ParseFixesHandler
from bot.handlers.parse.parse_handler import ParseHandler
from bot.handlers.parse.parse_language_handler import ParseLanguageHandler
from bot.handlers.parse.parse_map_handler import ParseMapHandler
from bot.models import BotState
from dynamo_persistence.persistence import DynamoPersistence
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
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class TheSpymasterBot:
    def __init__(self, telegram_token: str, server_host: str, dynamo_persistence: bool = False):
        self.api_client = TheSpymasterClient(server_host=server_host)
        persistence = DynamoPersistence() if dynamo_persistence else DictPersistence()
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

    def handle_warmup(self) -> Dict[str, float]:
        task_results = handle_warmup(self)
        return {task.name: task.duration for task in task_results}

    def parse_update(self, update: dict) -> Optional[Update]:
        return Update.de_json(update, bot=self.updater.bot)  # type: ignore

    def _construct_updater(self):
        log.info("Setting up bot...")
        # Start
        start = CommandHandler("start", self.generate_callback(StartEventHandler))
        custom = CommandHandler("custom", self.generate_callback(CustomHandler))
        # Config
        config_language = MessageHandler(Filters.text, self.generate_callback(ConfigLanguageHandler))
        config_solver = MessageHandler(Filters.text, self.generate_callback(ConfigSolverHandler))
        config_difficulty = MessageHandler(Filters.text, self.generate_callback(ConfigDifficultyHandler))
        config_model = MessageHandler(Filters.text, self.generate_callback(ConfigModelHandler))
        # Game
        process_message = MessageHandler(Filters.text & ~Filters.command, self.generate_callback(ProcessMessageHandler))
        next_move = CommandHandler("next_move", self.generate_callback(NextMoveHandler))
        # Parsing
        parse = CommandHandler("parse", self.generate_callback(ParseHandler))
        parse_language = MessageHandler(Filters.text, self.generate_callback(ParseLanguageHandler))
        parse_map = MessageHandler(Filters.photo, self.generate_callback(ParseMapHandler))
        parse_board = MessageHandler(Filters.photo, self.generate_callback(ParseBoardHandler))
        parse_fixes = MessageHandler(Filters.text, self.generate_callback(ParseFixesHandler))
        parse_fix = MessageHandler(Filters.text, self.generate_callback(ParseFixWordHandler))
        parse_done = CommandHandler("done", self.generate_callback(ParseDoneHandler))
        # Util
        fallback = CommandHandler("quit", self.generate_callback(FallbackHandler))
        help_message = CommandHandler("help", self.generate_callback(HelpMessageHandler))
        error_handler = self.generate_callback(ErrorHandler)
        # Internal
        load_models = CommandHandler("warmup", self.generate_callback(WarmupHandler))
        testing = CommandHandler("test", self.generate_callback(TestingHandler))

        conv_handler = ConversationHandler(
            name="main",
            entry_points=[
                help_message,
                start,
                custom,
                next_move,
                load_models,
                testing,
                parse,
            ],
            states={
                # Custom
                BotState.CONFIG_LANGUAGE: [config_language],
                BotState.CONFIG_SOLVER: [config_solver],
                BotState.CONFIG_DIFFICULTY: [config_difficulty],
                BotState.CONFIG_MODEL: [config_model],
                # Game
                BotState.PLAYING: [process_message],
                # Parse
                BotState.PARSE_LANGUAGE: [parse_language],
                BotState.PARSE_MAP: [parse_map],
                BotState.PARSE_BOARD: [parse_board],
                BotState.PARSE_FIXES: [parse_fixes, parse_done],
                BotState.PARSE_FIX: [parse_fix],
            },
            fallbacks=[fallback],
            allow_reentry=True,
            persistent=True,
        )

        self.dispatcher.add_handler(conv_handler)
        self.dispatcher.add_handler(process_message)
        self.dispatcher.add_error_handler(error_handler)  # type: ignore

    def poll(self) -> None:
        self.updater.start_polling()
        self.updater.idle()
