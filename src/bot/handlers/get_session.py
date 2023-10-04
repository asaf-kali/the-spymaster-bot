from the_spymaster_util.logger import get_logger

from bot.handlers.base import EventHandler

log = get_logger(__name__)


class GetSessionsHandler(EventHandler):
    def handle(self):
        log.info(f"Getting sessions for user {self.user.full_name}")
        self.send_text("Not implemented yet")
        # sessions_dict = {}
        # for session_id, session in self.bot.sessions.items():
        #     sessions_dict[session_id.chat_id] = session.clean_dict()
        # pretty_json = json.dumps(sessions_dict, indent=2, ensure_ascii=False)
        # self.send_text(pretty_json)
