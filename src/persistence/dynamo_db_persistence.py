import logging
from typing import Any, DefaultDict, Dict, Optional, Tuple

from pynamodb.exceptions import DoesNotExist
from telegram.ext import BasePersistence
from telegram.ext.utils.types import BD, CD, UD, CDCData, ConversationDict

from persistence.persistence_item import PersistenceItem

log = logging.getLogger(__name__)

ConversationKey = Tuple[int, ...]
ChatDataDict = DefaultDict[int, CD]
UserDataDict = DefaultDict[int, UD]


def get_conversation_id(conversation_name: str, key: ConversationKey) -> str:
    return f"conversation::{conversation_name}:{key}"


def get_chat_id(key: int) -> str:
    return f"chat::{key}"


def get_user_id(key: int) -> str:
    return f"user::{key}"


def get_bot_id(key: int) -> str:
    return f"bot::{key}"


class DynamoPersistencyStore:
    def get_item_id(self, key: Any) -> str:
        raise NotImplementedError()

    def __getitem__(self, item: ConversationKey):
        item_id = self.get_item_id(key=item)
        try:
            persistence_item = PersistenceItem.get(hash_key=item_id)
            return persistence_item.item_data
        except DoesNotExist:
            log.info(f"Item {item_id} does not exist")
            return None

    def store(self, key: Any, data: Any):
        item_id = self.get_item_id(key=key)
        item = PersistenceItem(item_id=item_id, item_data=data)
        item.save()


class DynamoStoredConversations(DynamoPersistencyStore, ConversationDict):  # type: ignore
    def __init__(self, conversation_name: str):
        self.conversation_name = conversation_name

    def get_item_id(self, key: Any) -> str:
        return get_conversation_id(conversation_name=self.conversation_name, key=key)


class DynamoStoredChatData(DynamoPersistencyStore, ChatDataDict):  # type: ignore
    def get_item_id(self, key: Any) -> str:
        return get_chat_id(key=key)


class DynamoStoredUserData(DynamoPersistencyStore, UserDataDict):  # type: ignore
    def get_item_id(self, key: Any) -> str:
        return get_user_id(key=key)


class DynamoStoredBotData(DynamoPersistencyStore, dict):  # type: ignore
    def get_item_id(self, key: Any) -> str:
        return get_bot_id(key=key)


class DynamoDbPersistence(BasePersistence):
    def __init__(
        self,
        store_user_data: bool = True,
        store_chat_data: bool = True,
        store_bot_data: bool = True,
        store_callback_data: bool = False,
    ):
        super().__init__(
            store_user_data=store_user_data,
            store_chat_data=store_chat_data,
            store_bot_data=store_bot_data,
            store_callback_data=store_callback_data,
        )
        self.user_data_store = DynamoStoredUserData()
        self.chat_data_store = DynamoStoredChatData()
        self.bot_data_store = DynamoStoredBotData()
        self.conversation_store_dict: Dict[str, DynamoStoredConversations] = {}

    def get_user_data(self) -> DynamoStoredUserData:
        return self.user_data_store

    def get_chat_data(self) -> DynamoStoredChatData:
        return self.chat_data_store

    def get_bot_data(self) -> DynamoStoredBotData:
        return self.bot_data_store

    def get_callback_data(self) -> Optional[CDCData]:
        log.warning("get_callback_data")
        return None

    def get_conversations(self, name: str) -> DynamoStoredConversations:
        if name not in self.conversation_store_dict:
            self.conversation_store_dict[name] = DynamoStoredConversations(conversation_name=name)
        return self.conversation_store_dict[name]

    def update_conversation(self, name: str, key: ConversationKey, new_state: Optional[object]) -> None:
        log.debug("Update conversation", extra={"name": name, "key": key, "new_state": new_state})
        conversation_store = self.get_conversations(name=name)
        conversation_store.store(key=key, data=new_state)

    def update_user_data(self, user_id: int, data: UD) -> None:
        self.user_data_store.store(key=user_id, data=data)

    def update_chat_data(self, chat_id: int, data: CD) -> None:
        self.chat_data_store.store(key=chat_id, data=data)

    def update_bot_data(self, data: BD) -> None:
        self.bot_data_store.store(key="main", data=data)

    def update_callback_data(self, data: CDCData) -> None:
        log.warning("update_callback_data")
