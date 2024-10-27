import base64

import requests
from codenames.game.color import CardColor
from telegram import PhotoSize
from the_spymaster_util.logger import get_logger

from bot.handlers.base import EventHandler
from bot.models import BadMessageError, BotState

log = get_logger(__name__)


class ParseHandler(EventHandler):
    def handle(self):
        self.send_text("🗺️ Please send me a picture of the map:")
        return BotState.PARSE_MAP


class ParseMapHandler(EventHandler):
    def handle(self):
        photos = self.update.message.photo
        if not photos:
            raise BadMessageError("No photo found in message")
        log.info(f"Got {len(photos)} photos, downloading the largest one")
        photo_meta = _get_largest_photo(photos)
        photo_ptr = photo_meta.get_file()
        photo_bytes = photo_ptr.download_as_bytearray()
        photo_base64 = base64.b64encode(photo_bytes).decode("utf-8")
        log.info("Downloaded and encoded photo")
        response = requests.get(
            url="http://localhost:5000/parse-color-map", json={"map_image_b64": photo_base64}, timeout=15
        )
        response.raise_for_status()
        response_json = response.json()
        map_colors = response_json.get("map_colors")
        card_colors = [CardColor(color) for color in map_colors]
        self._send_as_emoji_table(card_colors)
        self.send_text("🧩 Please send me a picture of the board:")
        return BotState.PARSE_MAP

    def _send_as_emoji_table(self, card_colors: list[CardColor]):
        result = "🔍 Parsed: \n"
        for i in range(0, len(card_colors), 5):
            row = card_colors[i : i + 5]
            row_emojis = " ".join(card.emoji for card in row)
            result += f"{row_emojis}\n"
        self.send_text(result)


def _get_largest_photo(photos: list[PhotoSize]) -> PhotoSize:
    return max(photos, key=lambda photo: photo.file_size)


class ParseBoardHandler(EventHandler):
    def handle(self):
        photo = self.update.message.photo
        if not photo:
            raise BadMessageError("No photo found in message")

        self.send_text("OK: I got the board. Let's play!")
        return BotState.ENTRY
