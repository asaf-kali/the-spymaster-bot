import time
from typing import Any, DefaultDict, Dict, Optional, Tuple

from pynamodb.attributes import JSONAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.expressions.condition import Condition
from pynamodb.models import Model
from pynamodb.settings import OperationSettings
from telegram.ext.utils.types import CD, UD

from bot.config import get_config
from bot.models import Session

config = get_config()


class PersistenceItem(Model):
    class Meta:
        table_name = config.persistence_db_table_name

    item_id = UnicodeAttribute(hash_key=True)
    item_type = UnicodeAttribute(null=True)
    item_data = JSONAttribute(null=True)
    updated_ts = NumberAttribute()

    def save(
        self, condition: Optional[Condition] = None, settings: OperationSettings = OperationSettings.default
    ) -> Dict[str, Any]:
        self.updated_ts = int(time.time())
        return super().save(condition=condition, settings=settings)


ConversationKey = Tuple[int, ...]


def get_conversation_id(conversation_name: str, key: ConversationKey) -> str:
    return f"conversation::{conversation_name}:{key}"


def get_chat_id(key: int) -> str:
    return f"chat::{key}"


def get_user_id(key: int) -> str:
    return f"user::{key}"


def get_bot_id(key: int) -> str:
    return f"bot::{key}"


def main():
    session = Session(game_id=1, last_keyboard_message_id=2)
    session_item = PersistenceItem(
        item_id=get_conversation_id("main", key=(999, 999)),
        item_data=session.dict(),
    )
    session_item.save()


if __name__ == "__main__":
    main()
ChatDataDict = DefaultDict[int, CD]
UserDataDict = DefaultDict[int, UD]
