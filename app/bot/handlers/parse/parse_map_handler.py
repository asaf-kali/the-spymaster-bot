import requests
from bot.config import get_config
from bot.handlers.other.event_handler import EventHandler
from bot.handlers.parse.photos import _get_base64_photo
from bot.models import BotState
from codenames.game.color import CardColor

# Map -> Board


class ParseMapHandler(EventHandler):
    def handle(self):
        photo_base64 = _get_base64_photo(photos=self.update.message.photo)
        card_colors = _parse_map_colors(photo_base64)
        table = self._as_emoji_table(card_colors)
        self.update_parsing_state(card_colors=card_colors)
        # Board parsing
        message = f"""I got:
{table}
You will have a chance to fix any mistakes later.

🧩 Please send me a picture of the board:
"""
        self.send_text(message)
        return BotState.PARSE_BOARD

    def _as_emoji_table(self, card_colors: list[CardColor]) -> str:
        result = ""
        for i in range(0, len(card_colors), 5):
            row = card_colors[i : i + 5]
            row_emojis = " ".join(card.emoji for card in row)
            result += f"{row_emojis}\n"
        return result


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
