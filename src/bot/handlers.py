from random import random
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Type

import sentry_sdk
from codenames.game.board import Board
from codenames.game.card import Card
from codenames.game.color import TeamColor
from codenames.game.move import PASS_GUESS, GivenGuess
from codenames.game.player import PlayerRole
from codenames.game.state import GameState
from requests import HTTPError
from telegram import Message, ReplyKeyboardMarkup, Update
from telegram import User as TelegramUser
from telegram.error import BadRequest as TelegramBadRequest
from telegram.ext import CallbackContext
from the_spymaster_api import TheSpymasterClient
from the_spymaster_api.structs import (
    ErrorResponse,
    GetGameStateRequest,
    GuessRequest,
    GuessResponse,
    ModelIdentifier,
    NextMoveRequest,
    StartGameRequest,
)
from the_spymaster_solvers_client.structs import Difficulty, Solver
from the_spymaster_util.logger import get_logger
from the_spymaster_util.measure_time import MeasureTime

from bot.models import (
    AVAILABLE_MODELS,
    BLUE_EMOJI,
    COMMAND_TO_INDEX,
    RED_EMOJI,
    WIN_REASON_TO_EMOJI,
    BadMessageError,
    BotState,
    GameConfig,
    Session,
)

if TYPE_CHECKING:
    from bot.the_spymaster_bot import TheSpymasterBot

log = get_logger(__name__)

SUPPORTED_LANGUAGES = ["hebrew", "english"]


class NoneValueError(Exception):
    pass


class EventHandler:  # pylint: disable=too-many-public-methods
    def __init__(
        self,
        bot: "TheSpymasterBot",
        update: Update,
        context: CallbackContext,
        chat_id: Optional[int],
        session: Optional[Session],
    ):
        self.bot = bot
        self.update = update
        self.context = context
        self.chat_id = chat_id
        self.session = session

    @property
    def api_client(self) -> TheSpymasterClient:
        return self.bot.api_client

    @property
    def user(self) -> Optional[TelegramUser]:
        return self.update.effective_user

    @property
    def user_id(self) -> Optional[int]:
        return self.user.id if self.user else None

    @property
    def username(self) -> Optional[str]:
        if not self.user:
            return None
        return self.user.username

    @property
    def user_full_name(self) -> Optional[str]:
        if not self.user:
            return None
        return self.user.full_name

    @property
    def game_id(self) -> Optional[str]:
        if not self.session:
            return None
        return self.session.game_id

    @property
    def config(self) -> Optional[GameConfig]:
        if not self.session:
            return None
        return self.session.config

    @classmethod
    def generate_callback(cls, bot: "TheSpymasterBot") -> Callable[[Update, CallbackContext], Any]:
        def callback(update: Update, context: CallbackContext) -> Any:
            chat_id = update.effective_chat.id if update.effective_chat else None
            session_data = context.chat_data
            session = Session(**session_data) if session_data else None
            instance = cls(bot=bot, update=update, context=context, chat_id=chat_id, session=session)
            try:
                game_id = session.game_id if session else None
                log.update_context(telegram_user_id=instance.user_id, game_id=game_id)
            except Exception as e:  # pylint: disable=invalid-name
                log.warning(f"Failed to update context: {e}")
            try:
                log.debug(f"Dispatching to event handler: {cls.__name__}")
                return instance.handle()
            except Exception as e:  # pylint: disable=invalid-name
                instance.handle_error(e)
            finally:
                log.reset_context()
            return None

        return callback

    def set_session(self, session: Optional[Session]) -> Optional[Session]:
        if not self.chat_id:
            raise NoneValueError("chat_id is not set, cannot set session.")
        chat_data = session.dict() if session else None
        self.session = session
        self.bot.dispatcher.chat_data[self.chat_id] = chat_data
        return session

    def update_session(self, **kwargs) -> Session:
        if self.session is None:
            raise NoneValueError("session is not set, cannot update session.")
        new_session = self.session.copy(update=kwargs)
        self.set_session(new_session)
        return new_session

    def update_game_config(self, **kwargs) -> Session:
        old_config = self.config
        if not old_config:
            raise NoneValueError("session is not set, cannot update game config.")
        new_config = old_config.copy(update=kwargs)
        return self.update_session(config=new_config)

    def handle(self):
        raise NotImplementedError()

    def trigger(self, other: Type["EventHandler"]) -> Any:
        return other(
            bot=self.bot, update=self.update, context=self.context, chat_id=self.chat_id, session=self.session
        ).handle()

    def send_text(self, text: str, put_log: bool = False, **kwargs) -> Message:
        if put_log:
            log.info(text)
        return self.context.bot.send_message(chat_id=self.chat_id, text=text, **kwargs)

    def send_markdown(self, text: str, **kwargs) -> Message:
        return self.send_text(text=text, parse_mode="Markdown", **kwargs)

    def fast_forward(self, state: GameState):
        if not state:
            raise NoneValueError("state is not set, cannot fast forward.")
        while not state.is_game_over and not _is_blue_guesser_turn(state=state):
            state = self._next_move(state=state)
        self.send_board(state=state)
        if state.is_game_over:
            self.send_game_summary(state=state)
            log.update_context(game_id=None)
            self.update_session(game_id=None)
            self.trigger(HelpMessageHandler)
            return None
        return BotState.PLAYING

    def remove_keyboard(self, last_keyboard_message_id: Optional[int]):
        if last_keyboard_message_id is None:
            return
        log.debug("Removing keyboard")
        try:
            self.context.bot.edit_message_reply_markup(chat_id=self.chat_id, message_id=last_keyboard_message_id)
        except TelegramBadRequest:
            pass
        self.update_session(last_keyboard_message_id=None)

    def send_game_summary(self, state: GameState):
        self._send_hinters_intents(state=state)
        self._send_winner_text(state=state)

    def _send_winner_text(self, state: GameState):
        winner = state.winner
        player_won = winner.team_color == TeamColor.BLUE
        winning_emoji = "🎉" if player_won else "😭"
        reason_emoji = WIN_REASON_TO_EMOJI[winner.reason]
        status = "won" if player_won else "lose"
        text = f"You {status}! {winning_emoji}\n{winner.team_color} team won: {winner.reason.value} {reason_emoji}"
        self.send_text(text, put_log=True)

    def _send_hinters_intents(self, state: GameState):
        relevant_hints = [hint for hint in state.raw_hints if hint.for_words]
        if not relevant_hints:
            return
        intent_strings = [f"'*{hint.word}*' for {hint.for_words}" for hint in relevant_hints]
        intent_string = "\n".join(intent_strings)
        text = f"Hinters intents were:\n{intent_string}\n"
        self.send_markdown(text)

    def _next_move(self, state: GameState) -> GameState:
        if not state or not self.config:
            raise NoneValueError("state is not set, cannot run next move.")
        team_color = state.current_team_color.value.title()
        if state.current_player_role == PlayerRole.HINTER:
            self.send_score(state=state)
            self.send_text(f"{team_color} hinter is thinking... 🤔")
        if _should_skip_turn(current_player_role=state.current_player_role, config=self.config):
            self.send_text(f"{team_color} guesser has skipped the turn.")
            request = GuessRequest(game_id=self.game_id, card_index=PASS_GUESS)
            response = self.api_client.guess(request=request)
            return response.game_state
        solver = self.config.solver
        request = NextMoveRequest(game_id=self.game_id, solver=solver)
        response = self.api_client.next_move(request=request)
        if response.given_hint:
            given_hint = response.given_hint
            text = f"{team_color} hinter says '*{given_hint.word}*' with *{given_hint.card_amount}* card(s)."
            self.send_markdown(text, put_log=True)
        if response.given_guess:
            text = f"{team_color} guesser: " + get_given_guess_result_message_text(given_guess=response.given_guess)
            self.send_markdown(text)
        return response.game_state

    def send_score(self, state: GameState):
        score = state.score
        text = f"{BLUE_EMOJI}  *{score.blue.unrevealed}*  remaining card(s)  *{score.red.unrevealed}*  {RED_EMOJI}"
        self.send_markdown(text)

    def send_board(self, state: GameState, message: Optional[str] = None):
        board_to_send = state.board if state.is_game_over else state.board.censured
        table = board_to_send.as_table
        keyboard = build_board_keyboard(table, is_game_over=state.is_game_over)
        if message is None:
            message = "Game over!" if state.is_game_over else "Pick your guess!"
        if state.left_guesses == 1:
            message += " (bonus round)"
        text = self.send_markdown(message, reply_markup=keyboard)
        self.update_session(last_keyboard_message_id=text.message_id)

    def _get_game_state(self, game_id: str) -> GameState:
        request = GetGameStateRequest(game_id=game_id)
        return self.api_client.get_game_state(request=request).game_state
        # self.set_state(new_state=response.game_state)

    def handle_error(self, error: Exception):
        log.debug(f"Handling error: {error}")
        try:
            _enrich_sentry_context(user_name=self.user_full_name)
        except Exception as e:  # pylint: disable=invalid-name
            log.warning(f"Failed to enrich sentry context: {e}")
        try:
            if self._handle_http_error(error):
                return
            if self._handle_bad_message(error):
                return
        except Exception as handling_error:
            sentry_sdk.capture_exception(handling_error)
            log.exception("Failed to handle error")
        sentry_sdk.capture_exception(error)
        log.exception(error)
        try:
            self.send_text(f"💔 Something went wrong: {error}")
        except:  # noqa  # pylint: disable=bare-except
            pass
        # Try refreshing the state
        # try:
        #     self._refresh_game_state()
        # except:  # noqa
        #     log.exception("Failed to refresh game state")

    def _handle_http_error(self, e: Exception) -> bool:  # pylint: disable=invalid-name
        if not isinstance(e, HTTPError):
            return False
        response = e.response
        if not 400 <= response.status_code < 500:
            return False
        data = response.json()
        error_response = ErrorResponse(**data)
        text = error_response.message
        if error_response.details:
            text += f": {error_response.details}"
        self.send_text(text, put_log=True)
        return True

    def _handle_bad_message(self, e: Exception) -> bool:  # pylint: disable=invalid-name
        if not isinstance(e, BadMessageError):
            return False
        self.send_markdown(f"🧐 {e}", put_log=True)
        return True


def _should_skip_turn(current_player_role: PlayerRole, config: GameConfig) -> bool:
    if current_player_role != PlayerRole.GUESSER:
        return False
    pass_probability = config.difficulty.pass_probability
    dice = random()
    return dice < pass_probability


class StartEventHandler(EventHandler):
    def handle(self):
        log.update_context(username=self.username, full_name=self.user_full_name)
        log.info(f"Got start event from {self.user_full_name}")
        game_config = self.config or GameConfig()
        request = StartGameRequest(language=game_config.language)
        response = self.api_client.start_game(request)
        log.update_context(game_id=response.game_id)
        log.debug("Game starting", extra={"game_id": response.game_id, "game_config": game_config.dict()})
        session = Session(game_id=response.game_id, config=game_config)
        self.set_session(session=session)
        short_id = response.game_id[-4:]
        self.send_markdown(f"Game *{short_id}* is starting! 🥳", put_log=True)
        return self.fast_forward(state=response.game_state)


class ProcessMessageHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        log.info(f"Processing message: '{text}'")
        if not self.session:
            return self.trigger(HelpMessageHandler)
        self.remove_keyboard(last_keyboard_message_id=self.session.last_keyboard_message_id)
        if not self.session.is_game_active:
            return self.trigger(HelpMessageHandler)
        state = self._get_game_state(game_id=self.game_id)
        if state and not _is_blue_guesser_turn(state):
            return self.fast_forward(state)
        try:
            command = COMMAND_TO_INDEX.get(text, text)
            card_index = _get_card_index(board=state.board, text=command)
        except:  # noqa  # pylint: disable=bare-except
            self.send_board(
                state=state,
                message=f"Card '*{text}*' not found. Please reply with card index (1-25) or a word on the board.",
            )
            return None
        response = self._guess(card_index)
        given_guess = response.given_guess
        if given_guess is None:
            pass  # This means we passed the turn
        else:
            text = get_given_guess_result_message_text(given_guess)
            self.send_markdown(text)
        return self.fast_forward(response.game_state)

    def _guess(self, card_index: int) -> GuessResponse:
        request = GuessRequest(game_id=self.game_id, card_index=card_index)
        return self.api_client.guess(request)


def _is_blue_guesser_turn(state: GameState):
    return state.current_team_color == TeamColor.BLUE and state.current_player_role == PlayerRole.GUESSER


def _get_card_index(board: Board, text: str) -> int:
    try:
        index = int(text)
        if index > 0:
            index -= 1
        return index
    except ValueError:
        pass
    return board.find_card_index(text)


class NextMoveHandler(EventHandler):
    def handle(self):
        state = self._get_game_state(game_id=self.game_id)
        new_state = self._next_move(state=state)
        return self.fast_forward(state=new_state)


class CustomHandler(EventHandler):
    def handle(self):
        game_config = GameConfig(difficulty=Difficulty.HARD)
        session = Session(config=game_config)
        self.set_session(session=session)
        keyboard = build_language_keyboard()
        self.send_text("🌍 Pick language:", reply_markup=keyboard)
        return BotState.CONFIG_LANGUAGE


def build_language_keyboard():
    languages = _title_list(SUPPORTED_LANGUAGES)
    return ReplyKeyboardMarkup([languages], one_time_keyboard=True)


class ConfigLanguageHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        log.info(f"Setting language: '{text}'")
        language = parse_language(text)
        self.update_game_config(language=language)
        keyboard = build_solver_keyboard()
        self.send_text("🧮 Pick solver:", reply_markup=keyboard)
        return BotState.CONFIG_SOLVER


def build_solver_keyboard():
    solvers = ["Naive", "GPT"]
    return ReplyKeyboardMarkup([solvers], one_time_keyboard=True)


class ConfigDifficultyHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        log.info(f"Setting difficulty: '{text}'")
        difficulty = parse_difficulty(text)
        self.update_game_config(difficulty=difficulty)
        keyword = build_models_keyboard(language=self.session.config.language)
        self.send_text("🧠 Pick language model:", reply_markup=keyword)
        return BotState.CONFIG_MODEL


def build_models_keyboard(language: str):
    language_models = [model for model in AVAILABLE_MODELS if model.language == language]
    model_names = [model.model_name for model in language_models]
    keyboard = ReplyKeyboardMarkup([model_names], one_time_keyboard=True)
    return keyboard


def parse_difficulty(text: str) -> Difficulty:
    try:
        return Difficulty(text)
    except ValueError as e:  # pylint: disable=invalid-name
        raise BadMessageError(f"Unknown difficulty: '*{text}*'") from e


class ConfigModelHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.lower()
        log.info(f"Setting model: '{text}'")
        model_identifier = parse_model_identifier(language=self.session.config.language, model_name=text)
        self.update_game_config(model_identifier=model_identifier)
        return self.trigger(StartEventHandler)


def parse_model_identifier(language: str, model_name: str) -> ModelIdentifier:
    for model in AVAILABLE_MODELS:
        if model.language == language and model.model_name == model_name:
            return model
    raise BadMessageError(f"Unknown model '*{model_name}*' for language '*{language}*'")


class GetSessionsHandler(EventHandler):
    def handle(self):
        log.info(f"Getting sessions for user {self.user.full_name}")
        self.send_text("Not implemented yet")
        # sessions_dict = {}
        # for session_id, session in self.bot.sessions.items():
        #     sessions_dict[session_id.chat_id] = session.clean_dict()
        # pretty_json = json.dumps(sessions_dict, indent=2, ensure_ascii=False)
        # self.send_text(pretty_json)


class LoadModelsHandler(EventHandler):
    def handle(self):
        self.send_text("Sending load models request...")
        with MeasureTime() as mt:  # pylint: disable=invalid-name
            response = self.bot.send_load_models_request()
        self.send_markdown(f"Loaded `{response.success_count}` models in `{mt.delta}` seconds.")


class ConfigSolverHandler(EventHandler):
    def handle(self):
        text = self.update.message.text.upper()
        try:
            solver = Solver[text]
        except Exception as e:
            raise BadMessageError(f"Unknown solver: '*{text}*'") from e
        log.info(f"Setting solver: '{solver}'")
        self.update_game_config(solver=solver)
        if solver == Solver.GPT:
            return self.trigger(StartEventHandler)
        keyboard = build_difficulty_keyboard()
        self.send_text("🥵 Pick difficulty:", reply_markup=keyboard)
        return BotState.CONFIG_DIFFICULTY


def build_difficulty_keyboard():
    difficulties = _title_list([Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD])
    keyboard = ReplyKeyboardMarkup([difficulties], one_time_keyboard=True)
    return keyboard


def parse_language(text: str) -> str:
    if text not in SUPPORTED_LANGUAGES:
        raise BadMessageError(f"Unknown language: '*{text}*'")
    return text


class ContinueHandler(EventHandler):
    def handle(self):
        self.send_text("This is not implemented yet 😢")


class ContinueGetIdHandler(EventHandler):
    def handle(self):
        pass


class FallbackHandler(EventHandler):
    def handle(self):
        pass


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


class HelpMessageHandler(EventHandler):
    def handle(self):
        log.info("Sending help message")
        text = """Welcome! I'm *The Spymaster* 🕵🏼‍♂️
/start - start a new game.
/custom - start a new game with custom configurations.
/continue - continue an old game.
/help - show this message.

How to play:
You are the blue guesser. The bot will play all other roles. \
When the blue hinter sends a hint, you can reply with a card index (1-25), \
or just click the word on the keyboard. \
Use '-pass' and '-quit' to pass the turn and quit the game.
"""
        self.send_markdown(text)


class ErrorHandler(EventHandler):
    def handle(self):
        log.warning("Using telegram bot handling mechanism, check why error was not handled in callback.")
        self.handle_error(self.context.error)


def _enrich_sentry_context(**kwargs):
    for k, v in log.context.items():  # pylint: disable=invalid-name
        sentry_sdk.set_tag(k, v)
    for k, v in kwargs.items():  # pylint: disable=invalid-name
        sentry_sdk.set_tag(k, v)


def get_given_guess_result_message_text(given_guess: GivenGuess) -> str:
    card = given_guess.guessed_card
    result = "Correct! ✅" if given_guess.correct else "Wrong! ❌"
    return f"Card '*{card.word}*' is {card.color.emoji}, {result}"


def build_board_keyboard(table, is_game_over: bool) -> ReplyKeyboardMarkup:
    reply_keyboard = []
    for row in table.rows:
        row_keyboard = []
        for card in row:
            card: Card  # type: ignore
            if is_game_over:
                content = f"{card.color.emoji} {card.word}"
            else:
                content = card.color.emoji if card.revealed else card.word
            row_keyboard.append(content)
        reply_keyboard.append(row_keyboard)
    reply_keyboard.append(list(COMMAND_TO_INDEX.keys()))
    return ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def _title_list(strings: List[str]) -> List[str]:
    return [s.title() for s in strings]
