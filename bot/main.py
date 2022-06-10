from the_spymaster_util import configure_logging

from bot.config import get_config
from bot.the_spymaster_bot import TheSpymasterBot


def main():
    configure_logging()
    config = get_config()
    bot = TheSpymasterBot(base_backend=config.base_backend_url)
    bot.listen()


if __name__ == "__main__":
    main()
