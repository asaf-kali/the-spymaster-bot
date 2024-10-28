import os
import sys

os.chdir("src")
sys.path.insert(0, "./")
from bot.config import configure_logging, get_config  # noqa: E402

config = get_config()
config.load()
configure_logging(config=config)
