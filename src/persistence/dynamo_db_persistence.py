import logging
from typing import Any, Dict, Optional

from pynamodb.exceptions import DoesNotExist
from telegram.ext import BasePersistence
from telegram.ext.utils.types import BD, CD, UD, CDCData, ConversationDict

from persistence.persistence_item import (
    ChatDataDict,
    ConversationKey,
    PersistenceItem,
    UserDataDict,
    get_bot_id,
    get_chat_id,
    get_conversation_id,
    get_user_id,
)

log = logging.getLogger(__name__)


class DynamoPersistencyStore:
    def __init__(self):
        # This cache might be a bad idea, in case 2 requests come in the same time.
        self.cache = {}

    def get_item_id(self, key: Any) -> str:
        raise NotImplementedError()

    def get_item_type(self) -> str:
        raise NotImplementedError()

    def get(self, key: Any) -> Any:
        item_id = self.get_item_id(key=key)
        if item_id in self.cache:
            return self.cache[item_id]
        try:
            persistence_item = PersistenceItem.get(hash_key=item_id)
            data = persistence_item.item_data
            self.cache[item_id] = data
            return data
        except DoesNotExist:
            log.info(f"Item {item_id} does not exist")
            return None

    def set(self, key: Any, data: Any):
        item_id = self.get_item_id(key=key)
        existing_data = self.cache.get(item_id)
        if data == existing_data:
            log.info(f"Data {data} is the same as in cache, not storing")
            return
        item_type = self.get_item_type()
        item = PersistenceItem(item_id=item_id, item_type=item_type, item_data=data)
        item.save()
        self.cache[item_id] = data

    def __getitem__(self, item: ConversationKey):
        return self.get(key=item)

    def __setitem__(self, key: Any, value: Any):
        return self.set(key=key, data=value)


class DynamoStoredConversations(DynamoPersistencyStore, ConversationDict):  # type: ignore
    def __init__(self, conversation_name: str):
        super().__init__()
        self.conversation_name = conversation_name

    def get_item_id(self, key: Any) -> str:
        return get_conversation_id(conversation_name=self.conversation_name, key=key)

    def get_item_type(self) -> str:
        return "conversation"


class DynamoStoredChatData(DynamoPersistencyStore, ChatDataDict):  # type: ignore
    def __copy__(self):
        return self.copy()

    def copy(self):
        new = self.__class__()
        new.cache = self.cache
        return new

    def get_item_id(self, key: Any) -> str:
        return get_chat_id(key=key)

    def get_item_type(self) -> str:
        return "chat"


class DynamoStoredUserData(DynamoPersistencyStore, UserDataDict):  # type: ignore
    def get_item_id(self, key: Any) -> str:
        return get_user_id(key=key)

    def get_item_type(self) -> str:
        return "user"


class DynamoStoredBotData(DynamoPersistencyStore, dict):  # type: ignore
    def get_item_id(self, key: Any) -> str:
        return get_bot_id(key=key)

    def get_item_type(self) -> str:
        return "bot"


class DynamoDbPersistence(BasePersistence):
    def __init__(
        self,
        store_user_data: bool = False,
        store_chat_data: bool = True,
        store_bot_data: bool = False,
        store_callback_data: bool = False,
    ):
        super().__init__(
            store_user_data=store_user_data,
            store_chat_data=store_chat_data,
            store_bot_data=store_bot_data,
            store_callback_data=store_callback_data,
        )
        self.conversation_store_dict: Dict[str, DynamoStoredConversations] = {}
        if store_user_data:
            self.user_data_store = DynamoStoredUserData()
        if store_chat_data:
            self.chat_data_store = DynamoStoredChatData()
        if store_bot_data:
            self.bot_data_store = DynamoStoredBotData()

    def get_conversations(self, name: str) -> DynamoStoredConversations:
        if name not in self.conversation_store_dict:
            self.conversation_store_dict[name] = DynamoStoredConversations(conversation_name=name)
        return self.conversation_store_dict[name]

    def get_user_data(self) -> UserDataDict:
        raise NotImplementedError()

    def get_chat_data(self) -> DynamoStoredChatData:
        return self.chat_data_store

    def get_bot_data(self) -> BD:
        raise NotImplementedError()

    def get_callback_data(self) -> Optional[CDCData]:
        raise NotImplementedError()

    def update_conversation(self, name: str, key: ConversationKey, new_state: Optional[object]) -> None:
        conversation_store = self.get_conversations(name=name)
        conversation_store.set(key=key, data=new_state)

    def update_user_data(self, user_id: int, data: UD) -> None:
        raise NotImplementedError()

    def update_chat_data(self, chat_id: int, data: CD) -> None:
        self.chat_data_store.set(key=chat_id, data=data)

    def update_bot_data(self, data: BD) -> None:
        raise NotImplementedError()

    def update_callback_data(self, data: CDCData) -> None:
        raise NotImplementedError()
