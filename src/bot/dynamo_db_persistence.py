import logging
from collections import defaultdict
from typing import DefaultDict, Optional, Tuple

from pynamodb.exceptions import DoesNotExist
from telegram.ext import BasePersistence
from telegram.ext.utils.types import BD, CD, UD, CDCData, ConversationDict

from persistence.persistence_item import PersistenceItem

log = logging.getLogger(__name__)

ConversationKey = Tuple[int, ...]


def get_conversation_id(conversation_name: str, key: ConversationKey) -> str:
    return f"conversation::{conversation_name}:{key}"


class DynamoStoredConversations(ConversationDict):
    def __init__(self, conversation_name: str):
        self.conversation_name = conversation_name

    def __getitem__(self, item: ConversationKey):
        conversation_id = get_conversation_id(conversation_name=self.conversation_name, key=item)
        try:
            conversation = PersistenceItem.get(hash_key=conversation_id)
            return conversation
        except DoesNotExist:
            log.info(f"Conversation {conversation_id} does not exist")
            return None


class DynamoDbPersistence(BasePersistence):
    def __init__(
        self,
        store_user_data: bool = False,
        store_chat_data: bool = False,
        store_bot_data: bool = False,
        store_callback_data: bool = False,
    ):
        super().__init__(
            store_user_data=store_user_data,
            store_chat_data=store_chat_data,
            store_bot_data=store_bot_data,
            store_callback_data=store_callback_data,
        )

    def get_user_data(self) -> DefaultDict[int, UD]:
        log.warning("get_user_data")
        return defaultdict()

    def get_chat_data(self) -> DefaultDict[int, CD]:
        log.warning("get_chat_data")
        return defaultdict()

    def get_bot_data(self) -> BD:
        log.warning("get_bot_data")
        return None  # type: ignore

    def get_callback_data(self) -> Optional[CDCData]:
        log.warning("get_callback_data")
        return None

    def get_conversations(self, name: str) -> ConversationDict:
        return DynamoStoredConversations(conversation_name=name)

    def update_conversation(self, name: str, key: ConversationKey, new_state: Optional[object]) -> None:
        log.info("Update conversation", extra={"name": name, "key": key, "new_state": new_state})
        conversation_id = get_conversation_id(conversation_name=name, key=key)
        item_data = {"state": new_state}
        conversation = PersistenceItem(item_id=conversation_id, item_data=item_data)
        conversation.save()

    def update_user_data(self, user_id: int, data: UD) -> None:
        log.warning("update_user_data")

    def update_chat_data(self, chat_id: int, data: CD) -> None:
        log.warning("update_chat_data")

    def update_bot_data(self, data: BD) -> None:
        log.warning("update_bot_data")

    def update_callback_data(self, data: CDCData) -> None:
        log.warning("update_callback_data")
