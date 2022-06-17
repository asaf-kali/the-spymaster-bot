from typing import List

from the_spymaster_util import LazyConfig


class Config(LazyConfig):
    def load(self, override_files: List[str] = None):
        super().load(override_files)
        parameters = [f"{self.service_prefix}-telegram-token", f"{self.service_prefix}-auth-token"]
        self.load_ssm_parameters(parameters)

    @property
    def service_prefix(self):
        return f"the-spymaster-bot-{self.env_name}"

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

    @property
    def bot_log_level(self) -> str:
        return self.get("BOT_LOG_LEVEL")


def get_config() -> Config:
    return Config()
