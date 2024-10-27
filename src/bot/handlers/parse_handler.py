import base64

import requests
from codenames.game.color import CardColor
from telegram import PhotoSize
from the_spymaster_util.logger import get_logger

from bot.config import get_config
from bot.handlers.base import EventHandler
from bot.models import BadMessageError, BotState

log = get_logger(__name__)


class ParseHandler(EventHandler):
    def handle(self):
        self.send_text("🗺️ Please send me a picture of the map:")
        return BotState.PARSE_MAP


class ParseMapHandler(EventHandler):
    def handle(self):
        photo_base64 = _get_base64_photo(photos=self.update.message.photo)
        card_colors = _parse_map_colors(photo_base64)
        self._send_as_emoji_table(card_colors)
        self.send_text("🧩 Please send me a picture of the board:")
        return BotState.PARSE_BOARD

    def _send_as_emoji_table(self, card_colors: list[CardColor]):
        result = "I got: \n\n"
        for i in range(0, len(card_colors), 5):
            row = card_colors[i : i + 5]
            row_emojis = " ".join(card.emoji for card in row)
            result += f"{row_emojis}\n"
        result += "\nYou will have a chance to fix any mistakes later."
        self.send_text(result)


class ParseBoardHandler(EventHandler):
    def handle(self):
        photo_base64 = _get_base64_photo(photos=self.update.message.photo)
        self.send_text("Working on it. This might take a minute ⏳️")
        words = _parse_board_words(photo_base64)
        self._send_as_table(words)
        return BotState.PARSE_BOARD

    def _send_as_table(self, words: list[str]):
        result = "OK! I got: \n\n"
        for i in range(0, len(words), 5):
            row = words[i : i + 5]
            row_str = " | ".join(_word_cell(word) for word in row)
            result += f"{row_str}\n"
        result += "\nHow does it look?"
        self.send_markdown(result)


def _word_cell(word: str) -> str:
    return f"*{word:<5}*"


def _parse_map_colors(photo_base64: str) -> list[CardColor]:
    env_config = get_config()
    url = f"{env_config.base_parser_url}/parse-color-map"
    payload = {"map_image_b64": photo_base64}
    response = requests.get(url=url, json=payload, timeout=15)
    response.raise_for_status()
    response_json = response.json()
    map_colors = response_json.get("map_colors")
    card_colors = [CardColor(color) for color in map_colors]
    return card_colors


def _parse_board_words(photo_base64: str) -> list[str]:
    env_config = get_config()
    url = f"{env_config.base_parser_url}/parse-board"
    payload = {"board_image_b64": photo_base64, "language": "heb"}
    response = requests.get(url=url, json=payload, timeout=80)
    response.raise_for_status()
    response_json = response.json()
    words = response_json.get("words")
    return words


def _get_base64_photo(photos: list[PhotoSize]) -> str:
    if not photos:
        raise BadMessageError("No photo found in message")
    log.info(f"Got {len(photos)} photos, downloading the largest one")
    photo_meta = _pick_largest_photo(photos)
    photo_ptr = photo_meta.get_file()
    photo_bytes = photo_ptr.download_as_bytearray()
    photo_base64 = base64.b64encode(photo_bytes).decode("utf-8")
    log.info("Downloaded and encoded photo")
    return photo_base64


def _pick_largest_photo(photos: list[PhotoSize]) -> PhotoSize:
    return max(photos, key=lambda photo: photo.file_size)
