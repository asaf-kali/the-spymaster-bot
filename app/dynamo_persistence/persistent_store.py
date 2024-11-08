import logging
from typing import Any, Optional, Tuple

from dynamo_persistence.persistent_item import PersistentItem
from pynamodb.exceptions import DoesNotExist as PynamoDoesNotExist
from the_spymaster_util.measure_time import MeasureTime

log = logging.getLogger(__name__)

ConversationKey = Tuple[int, ...]

SEC_TO_MS = 1000


class DoesNotExist(Exception):
    def __init__(self, item_id: str):
        self.item_id = item_id


class DynamoPersistentStore:
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
                persistence_item = PersistentItem.get(hash_key=item_id)
            except PynamoDoesNotExist as e:
                raise DoesNotExist(item_id=item_id) from e
        data = persistence_item.item_data
        log.debug("Read complete", extra={"item_id": item_id, "duration_ms": mt.delta * SEC_TO_MS, "data": data})
        return data

    def _write(self, key: Any, data: Any):
        item_id = self.get_item_id(key=key)
        item_type = self.get_item_type()
        item = PersistentItem(item_id=item_id, item_type=item_type, item_data=data)
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
        return f"{self.get_item_type()}::{key}"

    def get_item_type(self) -> str:
        raise NotImplementedError
