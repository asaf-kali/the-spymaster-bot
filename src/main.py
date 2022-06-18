import logging
from logging.config import dictConfig

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from the_spymaster_util.logging import get_dict_config

from bot.config import Config, get_config
from bot.the_spymaster_bot import TheSpymasterBot


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


def configure_sentry(config: Config):
    sentry_sdk.init(  # type: ignore
        dsn=config.sentry_dsn,
        integrations=[LoggingIntegration(event_level=None), AwsLambdaIntegration()],
        environment=config.env_verbose_name,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )


def main():
    configure_logging()
    config = get_config()
    config.load(extra_files=["../secrets.toml"])
    configure_logging(config=config)
    bot = TheSpymasterBot(telegram_token=config.telegram_token, base_backend=config.base_backend_url)
    bot.poll()


if __name__ == "__main__":
    main()
