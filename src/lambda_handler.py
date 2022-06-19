import json

import sentry_sdk
from the_spymaster_util import get_logger

from bot.config import get_config
from bot.the_spymaster_bot import TheSpymasterBot
from main import configure_logging, configure_sentry

configure_logging()
log = get_logger(__name__)

log.info("Bootstrap starting...")
config = get_config()
configure_logging(config=config)
configure_sentry(config=config)
bot = TheSpymasterBot(
    telegram_token=config.telegram_token,
    base_backend=config.base_backend_url,
    dynamo_persistence=True,
)
log.info("Bootstrap complete.")


def handle(event: dict, context=None):
    try:
        log.reset_context()
        log.info("Received event", extra={"event": event})
        body = event.get("body")
        if not body:
            log.info("No body in event, ignoring")
            return create_response(400, data={"message": "No body in event"})
        try:
            update_data = json.loads(body)
        except json.JSONDecodeError as e:
            log.warning("Error decoding JSON")
            return create_response(400, data={"message": "Error decoding JSON", "error": str(e)})
        bot.process_update(update_data)
    except Exception as e:
        log.exception("Error handling event")
        sentry_sdk.capture_exception(e)
        sentry_sdk.flush(timeout=5)
        return create_response(500, data={"message": "Error handling event"})


def create_response(status_code: int, data: dict):
    return {"statusCode": status_code, "body": json.dumps(data)}


def example_event():
    telegram_update = {
        "update_id": 617241338,
        "message": {
            "message_id": 2611,
            "from": {"id": 1362351931, "is_bot": False, "first_name": "𝒦𝒶𝓁𝒾", "language_code": "en"},
            "chat": {"id": 1362351931, "first_name": "𝒦𝒶𝓁𝒾", "type": "private"},
            "date": 1655500031,
            "text": "/start",
            "entities": [{"offset": 0, "length": 6, "type": "bot_command"}],
        },
    }
    event = {"body": json.dumps(telegram_update)}
    handle(event)


if __name__ == "__main__":
    example_event()
