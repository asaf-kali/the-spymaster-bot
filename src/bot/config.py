import logging
from logging.config import dictConfig
from typing import List, Optional

from the_spymaster_util.config import LazyConfig
from the_spymaster_util.logger import get_dict_config, get_logger

log = logging.getLogger(__name__)


class Config(LazyConfig):
    def load(self, extra_files: Optional[List[str]] = None):
        super().load(extra_files)
        parameters = [f"{self.service_prefix}-telegram-token", f"{self.service_prefix}-sentry-dsn"]
        if self.should_load_ssm_parameters:
            self.load_ssm_parameters(parameters)
        log.info("Config loaded")

    @property
    def project_name(self) -> str:
        return "the-spymaster-bot"

    @property
    def service_prefix(self):
        return f"{self.project_name}-{self.env_name}"

    @property
    def env_verbose_name(self) -> str:
        return self.get("ENV_VERBOSE_NAME")

    @property
    def sentry_dsn(self) -> str:
        return self.get(f"{self.service_prefix}-sentry-dsn") or self.get("SENTRY_DSN")

    @property
    def telegram_token(self) -> str:
        return self.get(f"{self.service_prefix}-telegram-token") or self.get("TELEGRAM_TOKEN")

    @property
    def persistence_db_table_name(self) -> str:
        return self.get("persistence_db_table_name") or f"{self.service_prefix}-persistence-table"

    @property
    def base_backend_url(self) -> str:
        return self.get("BASE_BACKEND_URL")

    @property
    def bot_log_level(self) -> str:
        return self.get("BOT_LOG_LEVEL")

    @property
    def should_load_ssm_parameters(self) -> bool:
        return self.get("SHOULD_LOAD_SSM_PARAMETERS")


def configure_logging(config: Optional[Config] = None):
    loggers = {
        "bot": {
            "handlers": ["console_out", "console_err"],
            "level": config.bot_log_level if config else "DEBUG",
            "propagate": False,
        },
        "telegram": {"level": "INFO"},
        "botocore": {"level": "WARNING"},
        "urllib3": {"level": "WARNING"},
        "pynamodb": {"level": "WARNING"},
    }
    kwargs = (
        {
            "std_formatter": config.std_formatter,
            "root_log_level": config.root_log_level,
            "indent_json": config.indent_json,
        }
        if config
        else {}
    )
    log_config = get_dict_config(
        **kwargs,
        extra_loggers=loggers,
    )
    dictConfig(log_config)
    get_logger(__name__).debug("Logging configured.")


def configure_sentry(config: Config):
    import sentry_sdk
    from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(  # type: ignore
        dsn=config.sentry_dsn,
        integrations=[LoggingIntegration(event_level=None), AwsLambdaIntegration()],
        environment=config.env_verbose_name,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.2,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )


_config = Config()


def get_config() -> Config:
    return _config
