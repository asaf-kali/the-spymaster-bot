from typing import List

from the_spymaster_util import LazyConfig


class Config(LazyConfig):
    def load(self, override_files: List[str] = None):
        super().load(override_files)
        secret_name = f"the-spymaster-{self.env_name}-secrets"
        try:
            self.load_kms_secrets(secret_name)
        except Exception:  # noqa
            pass

    @property
    def env_verbose_name(self) -> str:
        return self.get("ENV_VERBOSE_NAME")

    @property
    def sentry_dsn(self) -> str:
        return self.get("SENTRY_DSN")

    @property
    def telegram_token(self) -> str:
        return self.get("TELEGRAM_TOKEN")

    @property
    def base_backend_url(self) -> str:
        return self.get("BASE_BACKEND_URL")


def get_config() -> Config:
    return Config()


# handlers:
#         "bot_file": {
#             "class": "logging.handlers.TimedRotatingFileHandler",
#             "filename": os.path.join(LOGGING_DIR, "bot.log"),
#             "formatter": "json",
#             "level": "DEBUG",
#             "when": "midnight",
#             "backupCount": 28,
#         },
# "telegram_bot": {
#     "handlers": ["console_out", "console_err", "bot_file"],
#     "level": config.bot_log_level,
#     "propagate": False,
# },
# loggers:
#         "telegram": {"level": "INFO"},
