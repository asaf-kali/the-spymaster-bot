import time

from bot.handlers.base import EventHandler


class LoadModelsHandler(EventHandler):
    def handle(self):
        self.send_text("Sending load models request...")
        start_ts = self.update.message.date.timestamp()
        response = self.bot.send_load_models_request()
        end_ts = time.time()
        delta = round(end_ts - start_ts, 3)
        self.send_markdown(f"Loaded `{response.success_count}` models in `{delta}` seconds.")
