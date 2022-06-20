import os
import sys

os.chdir("src")
sys.path.insert(0, "./")
from bot.config import get_config
from main import configure_logging

config = get_config()
config.load()
configure_logging(config=config)
