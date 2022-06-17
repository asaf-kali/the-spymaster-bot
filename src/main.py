import logging
from logging.config import dictConfig

from the_spymaster_util.logging import get_dict_config

from bot.config import Config, get_config
from bot.the_spymaster_bot import TheSpymasterBot


def main():
    config = get_config()
    configure_logging(config=config)
    bot = TheSpymasterBot(telegram_token=config.telegram_token, base_backend=config.base_backend_url)
    bot.poll()


def configure_logging(config: Config = None):
    loggers = {
        "bot": {
            "handlers": ["console_out", "console_err"],
            "level": config.bot_log_level if config else "DEBUG",
            "propagate": False,
        },
        "telegram": {"level": "INFO"},
        "botocore": {"level": "WARNING"},
        "urllib3": {"level": "WARNING"},
    }
    kwargs = (
        dict(
            std_formatter=config.std_formatter,
            root_log_level=config.root_log_level,
            indent_json=config.indent_json,
        )
        if config
        else {}
    )
    log_config = get_dict_config(
        **kwargs,
        extra_loggers=loggers,
    )
    dictConfig(log_config)
    log = logging.getLogger(__name__)
    log.debug("Logging configured.")


if __name__ == "__main__":
    main()
