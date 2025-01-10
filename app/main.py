import json

from bot.config import configure_logging, get_config
from bot.the_spymaster_bot import TheSpymasterBot


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


def example_warmup():
    from lambda_handler import handle

    update = {"action": "warmup"}
    event = {"body": json.dumps(update)}
    handle(event)


if __name__ == "__main__":
    main()
