from the_spymaster_util.measure_time import MeasureTime

from bot.handlers.base import EventHandler


class LoadModelsHandler(EventHandler):
    def handle(self):
        self.send_text("Sending load models request...")
        with MeasureTime() as mt:  # pylint: disable=invalid-name
            response = self.bot.send_load_models_request()
        self.send_markdown(f"Loaded `{response.success_count}` models in `{mt.delta}` seconds.")
