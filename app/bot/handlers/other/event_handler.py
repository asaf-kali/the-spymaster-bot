from random import random
from typing import TYPE_CHECKING, Any, Callable, Optional, Type

import sentry_sdk
from beautifultable import BeautifulTable
from bot.handlers.other.common import (
    enrich_sentry_context,
    get_given_guess_result_message_text,
    is_blue_guesser_turn,
)
from bot.models import (
    BLUE_EMOJI,
    COMMAND_TO_INDEX,
    RED_EMOJI,
    WIN_REASON_TO_EMOJI,
    BadMessageError,
    BotState,
    GameConfig,
    ParsingState,
    Session,
)
from codenames.game.card import Card
from codenames.game.color import TeamColor
from codenames.game.move import PASS_GUESS, Hint
from codenames.game.player import PlayerRole
from codenames.game.state import GameState
from requests import HTTPError
from telegram import Message, ReplyKeyboardMarkup, Update
from telegram import User as TelegramUser
from telegram.error import BadRequest as TelegramBadRequest
from telegram.error import Unauthorized
from telegram.ext import CallbackContext
from the_spymaster_api import TheSpymasterClient
from the_spymaster_api.structs import (
    APIGameRuleError,
    ErrorResponse,
    GetGameStateRequest,
    GuessRequest,
    NextMoveRequest,
)
from the_spymaster_util.logger import get_logger

if TYPE_CHECKING:
    from bot.the_spymaster_bot import TheSpymasterBot

log = get_logger(__name__)


class NoneValueError(Exception):
    pass


class EventHandler:
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

    @property
    def parsing_state(self) -> Optional[ParsingState]:
        if not self.session:
            return None
        return self.session.parsing_state

    @classmethod
    def generate_callback(cls, bot: "TheSpymasterBot") -> Callable[[Update, CallbackContext], Any]:
        def callback(update: Update, context: CallbackContext) -> Any:
            chat_id = update.effective_chat.id if update.effective_chat else None
            session_data = context.chat_data
            session = Session(**session_data) if session_data else None
            instance = cls(bot=bot, update=update, context=context, chat_id=chat_id, session=session)
            handler_name = cls.__name__
            try:
                game_id = session.game_id if session else None
                log.update_context(telegram_user_id=instance.user_id, game_id=game_id, handler=handler_name)
            except Exception as e:
                log.warning(f"Failed to update context: {e}")
            try:
                log.debug(f"Dispatching to event handler: {handler_name}")
                return instance.handle()
            except Exception as e:
                instance.on_error(e)
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

    def update_parsing_state(self, **kwargs) -> Session:
        old_parsing_state = self.parsing_state
        if not old_parsing_state:
            raise NoneValueError("parsing state is not set, cannot update parsing state.")
        new_parsing_state = old_parsing_state.copy(update=kwargs)
        return self.update_session(parsing_state=new_parsing_state)

    def handle(self):
        raise NotImplementedError

    def trigger(self, other: Type["EventHandler"]) -> Any:
        return other(
            bot=self.bot,
            update=self.update,
            context=self.context,
            chat_id=self.chat_id,
            session=self.session,
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
        while not state.is_game_over and not is_blue_guesser_turn(state=state):
            state = self._next_move(state=state)
        self.send_board(state=state)
        if state.is_game_over:
            self.send_game_summary(state=state)
            log.update_context(game_id=None)
            self.update_session(game_id=None)
            from bot.handlers.other.help import HelpMessageHandler

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
        intent_strings = [_hint_intent_string(hint) for hint in relevant_hints]
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

    def on_error(self, error: Exception):
        log.debug(f"Handling error: {error}")
        self._enrich_context()
        if self._handle_familiar_errors(error):
            return
        sentry_sdk.capture_exception(error)
        log.exception("Unhandled error")
        self._notify_user_on_error()

    def _handle_familiar_errors(self, error: Exception) -> bool:
        try:
            if self._handle_http_error(error):
                return True
            if self._handle_bad_message(error):
                return True
            if self._handle_bad_move(error):
                return True
            if self._handle_bot_blocked(error):
                return True
        except Exception as handling_error:
            sentry_sdk.capture_exception(handling_error)
            log.exception("Error handling failed")
        return False

    def _notify_user_on_error(self):
        try:
            self.send_text("💔 Something went wrong, please try again")
        except Exception as e:
            log.warning(f"Failed to notify user on error: {e}")

    def _enrich_context(self):
        try:
            enrich_sentry_context(user_name=self.user_full_name)
        except Exception as e:
            log.warning(f"Failed to enrich sentry context: {e}")

    def _handle_bot_blocked(self, e: Exception) -> bool:
        if not isinstance(e, Unauthorized):
            return False
        log.info("Bot was blocked by the user")
        return True

    def _handle_http_error(self, e: Exception) -> bool:
        if not isinstance(e, HTTPError):
            return False
        response = e.response
        if not response:
            return False
        if not 400 <= response.status_code < 500:
            return False
        data = response.json()
        error_response = ErrorResponse(**data)
        text = error_response.message
        if error_response.details:
            text += f": {error_response.details}"
        self.send_text(text, put_log=True)
        return True

    def _handle_bad_message(self, e: Exception) -> bool:
        if not isinstance(e, BadMessageError):
            return False
        self.send_markdown(f"🧐 {e}", put_log=True)
        return True

    def _handle_bad_move(self, e: Exception) -> bool:
        if not isinstance(e, APIGameRuleError):
            return False
        self.send_text(f"🤬 {e.message}", put_log=True)
        return True


def _should_skip_turn(current_player_role: PlayerRole, config: GameConfig) -> bool:
    if current_player_role != PlayerRole.GUESSER:
        return False
    pass_probability = config.difficulty.pass_probability
    dice = random()
    return dice < pass_probability


def build_board_keyboard(table: BeautifulTable, is_game_over: bool) -> ReplyKeyboardMarkup:
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


def _hint_intent_string(hint: Hint) -> str:
    return f"'*{hint.word}*' for {hint.for_words}"
