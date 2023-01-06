import logging
from typing import Any, Dict, Optional

from pynamodb.exceptions import DoesNotExist as PynamoDoesNotExist
from telegram.ext import BasePersistence
from telegram.ext.utils.types import BD, CD, UD, CDCData, ConversationDict
from the_spymaster_util.measure_time import MeasureTime

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
SEC_TO_MS = 1000


class DoesNotExist(Exception):
    def __init__(self, item_id: str):
        self.item_id = item_id


class DynamoPersistencyStore:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}

    def __getitem__(self, key: ConversationKey):
        if key in self._cache:
            # This might be problematic with multiple lambdas: a lambda might keep cache from an old run,
            # while in another lambda's cache (and in dynamo) the data is already newer.
            # That's why it's important to call clear_cache() before / after each lambda run.
            return self._cache[key]
        try:
            self._cache[key] = self._read(key=key)
            return self._cache[key]
        except DoesNotExist as e:
            log.info(f"Item {e.item_id} does not exist")
            return None

    def __setitem__(self, key: Any, value: Any):
        self._cache[key] = value

    def __copy__(self):
        return self.copy()

    def copy(self):
        return self.__class__()

    def clear_cache(self):
        self._cache.clear()

    def _read(self, key: Any) -> Optional[Any]:
        item_id = self.get_item_id(key=key)
        log.debug("Reading from Dynamo", extra={"item_id": item_id})
        with MeasureTime() as mt:
            try:
                persistence_item = PersistenceItem.get(hash_key=item_id)
            except PynamoDoesNotExist as e:
                raise DoesNotExist(item_id=item_id) from e
        data = persistence_item.item_data
        log.debug("Read complete", extra={"item_id": item_id, "duration_ms": mt.delta * SEC_TO_MS, "data": data})
        return data

    def _write(self, key: Any, data: Any):
        item_id = self.get_item_id(key=key)
        item_type = self.get_item_type()
        item = PersistenceItem(item_id=item_id, item_type=item_type, item_data=data)
        log.debug("Writing to Dynamo", extra={"item_id": item_id, "item_data": data})
        with MeasureTime() as mt:
            item.save()
        log.debug("Write complete", extra={"item_id": item_id, "duration_ms": mt.delta * SEC_TO_MS})

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key: Any, data: Any, commit: bool = False):
        self[key] = data
        if commit:
            self.commit(key=key)

    def commit(self, key: Any):
        if key not in self._cache:
            raise KeyError(key)
        self._write(key=key, data=self._cache[key])
        del self._cache[key]

    def get_item_id(self, key: Any) -> str:
        raise NotImplementedError()

    def get_item_type(self) -> str:
        raise NotImplementedError()


class DynamoStoredConversations(DynamoPersistencyStore, ConversationDict):  # type: ignore
    def __init__(self, conversation_name: str):
        super().__init__()
        self.conversation_name = conversation_name

    def __getitem__(self, item):
        value = super().__getitem__(key=item)
        if value is None:
            return 0
        return value

    def get_item_id(self, key: Any) -> str:
        return get_conversation_id(conversation_name=self.conversation_name, key=key)

    def get_item_type(self) -> str:
        return "conversation"


class DynamoStoredChatData(DynamoPersistencyStore, ChatDataDict):  # type: ignore
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
        conversation_store.set(key=key, data=new_state, commit=True)

    def update_user_data(self, user_id: int, data: UD) -> None:
        raise NotImplementedError()

    def update_chat_data(self, chat_id: int, data: CD) -> None:
        self.chat_data_store.set(key=chat_id, data=data, commit=True)

    def update_bot_data(self, data: BD) -> None:
        raise NotImplementedError()

    def update_callback_data(self, data: CDCData) -> None:
        raise NotImplementedError()
