from bot.handlers.base import EventHandler
from bot.models import GameConfig, Session
from the_spymaster_api.structs import StartGameRequest
from the_spymaster_util.logger import get_logger

log = get_logger(__name__)


class StartEventHandler(EventHandler):
    def handle(self):
        log.update_context(username=self.username, full_name=self.user_full_name)
        log.info(f"Got start event from {self.user_full_name}")
        game_config = self.config or GameConfig()
        request = StartGameRequest(language=game_config.language, first_team=game_config.first_team)
        response = self.api_client.start_game(request)
        log.update_context(game_id=response.game_id)
        log.debug("Game starting", extra={"game_id": response.game_id, "game_config": game_config.dict()})
        session = Session(game_id=response.game_id, config=game_config)
        self.set_session(session=session)
        short_id = response.game_id[-4:]
        self.send_markdown(f"Game *{short_id}* is starting! 🥳", put_log=True)
        return self.fast_forward(state=response.game_state)
