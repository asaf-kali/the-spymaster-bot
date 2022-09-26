import time
from typing import Any, DefaultDict, Dict, Optional, Tuple

from pynamodb.attributes import JSONAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.expressions.condition import Condition
from pynamodb.models import Model
from pynamodb.settings import OperationSettings
from telegram.ext.utils.types import CD, UD

from bot.config import get_config

config = get_config()

ChatDataDict = DefaultDict[int, CD]
UserDataDict = DefaultDict[int, UD]
ConversationKey = Tuple[int, ...]


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


def get_conversation_id(conversation_name: str, key: ConversationKey) -> str:
    key_str = ":".join([str(k) for k in key])
    return f"conversation::{conversation_name}:{key_str}"


def get_chat_id(key: int) -> str:
    return f"chat::{key}"


def get_user_id(key: int) -> str:
    return f"user::{key}"


def get_bot_id(key: int) -> str:
    return f"bot::{key}"
