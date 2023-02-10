import json

from bot.config import configure_logging, get_config
from bot.the_spymaster_bot import TheSpymasterBot
from lambda_handler import handle


def main():
    config = get_config()
    config.load(extra_files=["../secrets.toml"])
    configure_logging(config=config)
    bot = TheSpymasterBot(
        telegram_token=config.telegram_token,
        base_url=config.base_backend_url,
        dynamo_persistence=True,
    )
    bot.poll()


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


def example_warmup():
    update = {"action": "warmup"}
    event = {"body": json.dumps(update)}
    handle(event)


if __name__ == "__main__":
    main()
