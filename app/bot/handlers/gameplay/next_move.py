from bot.handlers.other.event_handler import EventHandler


class NextMoveHandler(EventHandler):
    def handle(self):
        state = self._get_game_state(game_id=self.game_id)
        new_state = self._next_move(state=state)
        return self.fast_forward(state=new_state)
