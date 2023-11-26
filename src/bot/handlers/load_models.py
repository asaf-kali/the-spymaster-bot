import time

from bot.handlers.base import EventHandler


class LoadModelsHandler(EventHandler):
    def handle(self):
        receive_ts = time.time()
        sent_ts = self.update.message.date.timestamp()
        receive_delta = round(receive_ts - sent_ts, 3)
        self.send_text(f"Sending load models request (receive took `{receive_delta}` seconds)...")
        load_start_ts = time.time()
        response = self.bot.send_load_models_request()
        load_end_ts = time.time()
        load_delta = round(load_end_ts - load_start_ts, 3)
        self.send_markdown(f"Loaded `{response.success_count}` models in `{load_delta}` seconds.")
