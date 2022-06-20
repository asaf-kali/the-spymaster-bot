import logging

from bot.config import Config, get_config

log = logging.getLogger(__name__)


def test_config_loads():
    config: Config = get_config()
    config.load()
    log.info(f"Config loaded, environment: {config.env_verbose_name}")
