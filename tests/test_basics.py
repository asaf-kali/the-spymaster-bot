import logging

from bot.config import get_config

log = logging.getLogger(__name__)


def test_config_loads():
    config = get_config()
    config.load()
    log.info(f"Config loaded, environment: {config.env_verbose_name}")


def test_main_modules_load():
    from lambda_handler import handle  # noqa: F401
    from main import main  # noqa: F401
    from util import create_response  # noqa: F401
