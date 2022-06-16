import os
from logging.config import dictConfig

from the_spymaster_util.logging import get_dict_config

from bot.config import Config, get_config
from bot.the_spymaster_bot import TheSpymasterBot


def main():
    config = get_config()
    configure_logging(config=config)
    bot = TheSpymasterBot(telegram_token=config.telegram_token, base_backend=config.base_backend_url)
    bot.poll()


def configure_logging(config: Config):
    loggers = {
        "bot": {
            "handlers": ["console_out", "console_err", "bot_file"],
            "level": config.bot_log_level,
            "propagate": False,
        },
        "telegram": {"level": "INFO"},
        "botocore": {"level": "WARNING"},
    }
    handlers = {
        "bot_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(".", "bot.log"),
            "formatter": "json",
            "level": "DEBUG",
            "when": "midnight",
            "backupCount": 28,
        }
    }
    log_config = get_dict_config(
        std_formatter=config.std_formatter,
        root_log_level=config.root_log_level,
        indent_json=config.indent_json,
        extra_handlers=handlers,
        extra_loggers=loggers,
    )
    dictConfig(log_config)


if __name__ == "__main__":
    main()
