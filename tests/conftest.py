import pytest
from bot.config import configure_logging, get_config


@pytest.fixture(scope="session", autouse=True)
def _configure_logging():
    config = get_config()
    config.load()
    configure_logging(config=config)
