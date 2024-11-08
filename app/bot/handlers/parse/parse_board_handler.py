import requests
from bot.config import get_config
from bot.handlers.other.event_handler import EventHandler, build_board_keyboard
from bot.handlers.parse.photos import _get_base64_photo
from bot.models import BotState
from codenames.game.board import Board
from codenames.game.card import Card

# Board -> Fixing


class ParseBoardHandler(EventHandler):
    def handle(self):
        photo_base64 = _get_base64_photo(photos=self.update.message.photo)
        self.send_text("Working on it. This might take a minute ⏳️")
        parsing_state = self.session.parsing_state
        parsed_words = _parse_board_words(photo_base64=photo_base64, language=parsing_state.language)
        words = [word if word else str(i) for i, word in enumerate(parsed_words)]
        cards = [Card(word=word, color=color) for word, color in zip(words, parsing_state.card_colors)]
        parsed_board = Board(language=parsing_state.language, cards=cards)
        keyboard = build_board_keyboard(table=parsed_board.as_table, is_game_over=True)
        message = "🎉 Done! Here's the board.\nClick on any card to fix it. When you are done, send me /done."
        text = self.send_markdown(text=message, reply_markup=keyboard)
        self.update_session(last_keyboard_message_id=text.message_id, parsing_state=None)
        return BotState.PARSE_FIXES


def _parse_board_words(photo_base64: str, language: str) -> list[str]:
    env_config = get_config()
    url = f"{env_config.base_parser_url}/parse-board"
    payload = {"board_image_b64": photo_base64, "language": language}
    response = requests.get(url=url, json=payload, timeout=80)
    response.raise_for_status()
    response_json = response.json()
    words = response_json.get("words")
    return words
