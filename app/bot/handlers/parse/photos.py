import base64

from bot.handlers.parse.parse_handler import log
from bot.models import BadMessageError
from telegram import PhotoSize


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
