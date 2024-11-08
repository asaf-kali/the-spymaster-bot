import requests
from bot.config import get_config
from bot.handlers.other.event_handler import EventHandler
from bot.handlers.parse.photos import _get_base64_photo
from bot.models import BotState

# Board -> Fixing


class ParseBoardHandler(EventHandler):
    def handle(self):
        photo_base64 = _get_base64_photo(photos=self.update.message.photo)
        self.send_text("Working on it, this might take a minute... 🔍️")
        parsed_words = _parse_board_words(photo_base64=photo_base64, language=self.parsing_state.language)
        words = [word if word else str(i) for i, word in enumerate(parsed_words)]
        self.update_parsing_state(words=words)
        self.send_parsing_state()
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
