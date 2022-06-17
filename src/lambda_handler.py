import json

from the_spymaster_util import get_logger

from bot.config import get_config
from bot.the_spymaster_bot import TheSpymasterBot
from main import configure_logging

configure_logging()
log = get_logger(__name__)

log.info("Bootstrap starting...")
config = get_config()
configure_logging(config=config)
bot = TheSpymasterBot(telegram_token=config.telegram_token, base_backend=config.base_backend_url)
log.info("Bootstrap complete.")


def handle(event: dict, context=None):
    try:
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
    except:  # noqa
        log.exception("Error handling event")
        return create_response(500, data={"message": "Error handling event"})


def create_response(status_code: int, data: dict):
    return {"statusCode": status_code, "body": json.dumps(data)}


def example_event():
    telegram_update = {
        "update_id": 617241324,
        "message": {
            "message_id": 2577,
            "from": {
                "id": 1362351931,
                "is_bot": False,
                "first_name": "\\ud835\\udca6\\ud835\\udcb6\\ud835\\udcc1\\ud835\\udcbe",
                "language_code": "en",
            },
            "chat": {
                "id": 1362351931,
                "first_name": "\\ud835\\udca6\\ud835\\udcb6\\ud835\\udcc1\\ud835\\udcbe",
                "type": "private",
            },
            "date": 1655397228,
            "text": "asdf",
        },
    }
    event = {"body": json.dumps(telegram_update)}
    handle(event)


if __name__ == "__main__":
    example_event()
