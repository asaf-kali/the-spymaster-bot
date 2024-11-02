import json

import sentry_sdk
from bot.config import configure_logging, configure_sentry, get_config
from bot.the_spymaster_bot import TheSpymasterBot
from the_spymaster_util.logger import get_logger
from util import create_response, json_safe

print("Bootstrap starting...")
config = get_config()
configure_logging(config=config)
log = get_logger(__name__)
configure_sentry(config=config)
bot = TheSpymasterBot(
    telegram_token=config.telegram_token,
    base_url=config.base_backend_url,
    dynamo_persistence=True,
)
log.info("Bootstrap complete.")


def handle(event: dict, context=None):
    try:
        log.reset_context()
        log.info("Received event", extra={"event": event})
        body = event.get("body")
        if not body:
            log.info("No body in event, ignoring")
            return create_response(400, data={"message": "No body in event"})
        try:
            update_data = json.loads(body)
        except json.JSONDecodeError as e:
            log.warning("Error decoding JSON")
            return create_response(400, data={"message": "Error decoding JSON", "error": str(e)})
        result = bot.process_update(update_data)
        return create_response(200, data={"result": json_safe(result)})
    except Exception as e:
        log.exception("Error handling event")
        sentry_sdk.capture_exception(e)
        sentry_sdk.flush(timeout=5)
        return create_response(500, data={"message": "Error handling event"})
