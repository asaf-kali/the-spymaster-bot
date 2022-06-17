import logging
from typing import List

from cachetools.func import ttl_cache
from the_spymaster_util import LazyConfig

log = logging.getLogger(__name__)


class Config(LazyConfig):
    def load(self, override_files: List[str] = None):
        super().load(override_files)
        parameters = [f"{self.service_prefix}-telegram-token", f"{self.service_prefix}-auth-token"]
        self.load_ssm_parameters(parameters)
        log.info("Config loaded")

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
        return self.get(f"{self.service_prefix}-telegram-token")

    @property
    def base_backend_url(self) -> str:
        return self.get("BASE_BACKEND_URL")

    @property
    def bot_log_level(self) -> str:
        return self.get("BOT_LOG_LEVEL")


@ttl_cache(maxsize=1, ttl=600)
def get_config() -> Config:
    return Config()
