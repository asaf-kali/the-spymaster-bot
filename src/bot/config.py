import logging
from typing import List

from cachetools.func import ttl_cache
from the_spymaster_util import LazyConfig

log = logging.getLogger(__name__)


class Config(LazyConfig):
    def load(self, extra_files: List[str] = None):
        super().load(extra_files)
        parameters = [f"{self.service_prefix}-telegram-token", f"{self.service_prefix}-sentry-dsn"]
        if self.should_load_ssm_parameters:
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


@ttl_cache(maxsize=1, ttl=600)
def get_config() -> Config:
    return Config()
