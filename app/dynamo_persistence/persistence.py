import logging
from typing import Dict, Optional

from dynamo_persistence.persistent_store import ConversationKey
from dynamo_persistence.telegram_stores import (
    DynamoStoredBotData,
    DynamoStoredChatData,
    DynamoStoredConversation,
    DynamoStoredUserData,
    UserDataDict,
)
from telegram.ext import BasePersistence
from telegram.ext.utils.types import BD, CD, UD, CDCData

log = logging.getLogger(__name__)


class DynamoPersistence(BasePersistence):
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
        self.conversation_store_dict: Dict[str, DynamoStoredConversation] = {}
        if store_user_data:
            self.user_data_store = DynamoStoredUserData()
        if store_chat_data:
            self.chat_data_store = DynamoStoredChatData()
        if store_bot_data:
            self.bot_data_store = DynamoStoredBotData()

    def get_conversations(self, name: str) -> DynamoStoredConversation:
        if name not in self.conversation_store_dict:
            self.conversation_store_dict[name] = DynamoStoredConversation(conversation_name=name)
        return self.conversation_store_dict[name]

    def get_user_data(self) -> UserDataDict:
        raise NotImplementedError

    def get_chat_data(self) -> DynamoStoredChatData:
        return self.chat_data_store

    def get_bot_data(self) -> BD:  # type: ignore
        raise NotImplementedError

    def get_callback_data(self) -> Optional[CDCData]:
        raise NotImplementedError

    def update_conversation(self, name: str, key: ConversationKey, new_state: Optional[object]) -> None:
        conversation_store = self.get_conversations(name=name)
        conversation_store.set(key=key, data=new_state, commit=True)

    def update_user_data(self, user_id: int, data: UD) -> None:
        raise NotImplementedError

    def update_chat_data(self, chat_id: int, data: CD) -> None:
        self.chat_data_store.set(key=chat_id, data=data, commit=True)

    def update_bot_data(self, data: BD) -> None:
        raise NotImplementedError

    def update_callback_data(self, data: CDCData) -> None:
        raise NotImplementedError
