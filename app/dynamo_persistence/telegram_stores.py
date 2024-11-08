from typing import Any, DefaultDict

from dynamo_persistence.persistent_store import DynamoPersistentStore
from telegram.ext.utils.types import CD, UD, ConversationDict

ChatDataDict = DefaultDict[int, CD]
UserDataDict = DefaultDict[int, UD]


class DynamoStoredConversation(DynamoPersistentStore, ConversationDict):  # type: ignore
    def __init__(self, conversation_name: str):
        super().__init__()
        self.conversation_name = conversation_name

    def __getitem__(self, item):
        value = super().__getitem__(key=item)
        if value is None:
            return 0
        return value

    def get_item_id(self, key: Any) -> str:
        parts_concat = ":".join([str(k) for k in key])
        conv_name = f"{self.conversation_name}:{parts_concat}"
        return super().get_item_id(key=conv_name)

    def get_item_type(self) -> str:
        return "conversation"


class DynamoStoredChatData(DynamoPersistentStore, ChatDataDict):  # type: ignore
    def get_item_type(self) -> str:
        return "chat"


class DynamoStoredUserData(DynamoPersistentStore, UserDataDict):  # type: ignore
    def get_item_type(self) -> str:
        return "user"


class DynamoStoredBotData(DynamoPersistentStore, dict):  # type: ignore
    def get_item_type(self) -> str:
        return "bot"
