import time
from typing import Any, Dict, Optional

from pynamodb.attributes import JSONAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.expressions.condition import Condition
from pynamodb.models import Model
from pynamodb.settings import OperationSettings

from bot.config import get_config
from bot.models import Session

config = get_config()


class PersistenceItem(Model):
    class Meta:
        table_name = config.persistence_db_table_name
        allow_extra = True

    item_id = UnicodeAttribute(hash_key=True)
    item_type = UnicodeAttribute(null=True)
    updated_ts = NumberAttribute(range_key=True)
    item_data = JSONAttribute()

    def save(
        self, condition: Optional[Condition] = None, settings: OperationSettings = OperationSettings.default
    ) -> Dict[str, Any]:
        self.updated_ts = int(time.time())
        return super().save(condition=condition, settings=settings)


def main():
    session = Session(game_id=1, last_keyboard_message=2)
    session_item = PersistenceItem(
        item_id=f"session::test::{session.game_id}",
        item_type="session",
        updated_ts=time.time(),
        item_data=session.dict(),
    )
    session_item.save()


if __name__ == "__main__":
    main()
