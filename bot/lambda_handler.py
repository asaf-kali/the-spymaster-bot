import json

from the_spymaster_util import get_logger

from bot.config import get_config
from bot.main import configure_logging
from bot.the_spymaster_bot import TheSpymasterBot

configure_logging()
log = get_logger(__name__)

log.info("Bootstrap starting...")
config = get_config()
configure_logging(config=config)
bot = TheSpymasterBot(telegram_token=config.telegram_token, base_backend=config.base_backend_url)
log.info("Bootstrap complete.")


def handle(event: dict, context=None):
    log.info("Received event", extra={"event": event})
    update_data = json.loads(event["body"])
    bot.process_update(update_data)


def main():
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
    main()
