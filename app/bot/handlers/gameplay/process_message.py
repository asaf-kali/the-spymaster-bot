from bot.handlers.other.common import (
    get_given_guess_result_message_text,
    is_blue_guesser_turn,
)
from bot.handlers.other.event_handler import EventHandler
from bot.handlers.other.help import HelpMessageHandler
from bot.models import COMMAND_TO_INDEX
from codenames.game.board import Board
from the_spymaster_api.structs import GuessRequest, GuessResponse
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


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
        if state and not is_blue_guesser_turn(state):
            return self.fast_forward(state)
        try:
            command = COMMAND_TO_INDEX.get(text, text)
            card_index = _get_card_index(board=state.board, text=command)
        except:  # noqa
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


def _get_card_index(board: Board, text: str) -> int:
    try:
        index = int(text)
        if index > 0:
            index -= 1
        return index
    except ValueError:
        pass
    return board.find_card_index(text)
