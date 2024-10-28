import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING, Dict, List

import requests
from the_spymaster_solvers_api.structs import LoadModelsRequest, LoadModelsResponse

from bot.config import get_config
from bot.handlers.base import EventHandler
from bot.models import AVAILABLE_MODELS

if TYPE_CHECKING:
    from bot.the_spymaster_bot import TheSpymasterBot

log = logging.getLogger(__name__)


@dataclass
class WarmupTaskResult:
    name: str
    message: str
    duration: float


WarmupResult = Dict[str, str]


class WarmupHandler(EventHandler):
    def handle(self):
        receive_ts = time.time()
        sent_ts = self.update.message.date.timestamp()
        receive_delta = round(receive_ts - sent_ts, 3)
        self.send_markdown(f"Receive warmup command took `{receive_delta}` seconds")
        results = handle_warmup(self.bot)
        self._send_results(results)

    def _send_results(self, results: List[WarmupTaskResult]):
        message = "Warmup complete. Results:\n"
        for result in results:
            message += f"\n🐇 *{result.name}*: {result.message} in `{result.duration}` sec"
        self.send_markdown(message)


def handle_warmup(bot: "TheSpymasterBot") -> List[WarmupTaskResult]:
    worker = ThreadPoolExecutor(max_workers=5)
    tasks = [
        worker.submit(load_solvers_models, bot),
        worker.submit(load_parser_languages, bot),
    ]
    worker.shutdown()
    task_results = [task.result() for task in tasks]
    return task_results


def warmup_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs) -> WarmupTaskResult:
        start_ts = time.time()
        try:
            message = func(*args, **kwargs)
        except Exception as e:
            log.exception(f"Error in warmup task {func.__name__}")
            message = f"Failed with error: `{str(e)}`"
        end_ts = time.time()
        delta = round(end_ts - start_ts, 3)
        return WarmupTaskResult(name=func.__name__, message=message, duration=delta)

    return wrapper


@warmup_task
def load_solvers_models(bot: "TheSpymasterBot") -> str:
    response = _send_load_models_request(bot)
    return f"Loaded `{response.success_count}` models"


@warmup_task
def load_parser_languages(bot: "TheSpymasterBot") -> str:
    languages = _send_load_languages_request()
    return f"Loaded `{len(languages)}` languages"


def _send_load_languages_request() -> List[str]:
    env_config = get_config()
    url = f"{env_config.base_parser_url}/load-languages"
    payload = {"languages": ["heb", "eng"]}
    response = requests.put(url=url, json=payload, timeout=30)
    response.raise_for_status()
    response_json = response.json()
    languages = response_json.get("loaded")
    return languages


def _send_load_models_request(bot: "TheSpymasterBot") -> LoadModelsResponse:
    request = LoadModelsRequest(model_identifiers=AVAILABLE_MODELS, load_default_models=False)
    response = bot.api_client.load_models(request)
    return response
