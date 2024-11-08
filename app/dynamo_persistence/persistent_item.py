import time
from typing import Any, Dict, Optional

from bot.config import get_config
from pynamodb.attributes import JSONAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.expressions.condition import Condition
from pynamodb.models import Model
from pynamodb.settings import OperationSettings

config = get_config()


class PersistentItem(Model):
    class Meta:
        table_name = config.persistence_db_table_name

    item_id = UnicodeAttribute(hash_key=True)
    item_type = UnicodeAttribute(null=True)
    item_data = JSONAttribute(null=True)
    updated_at = NumberAttribute()

    def save(
        self,
        condition: Optional[Condition] = None,
        settings: OperationSettings = OperationSettings.default,
        **kwargs,
    ) -> Dict[str, Any]:
        self.updated_at = float(time.time())
        return super().save(condition=condition, settings=settings, **kwargs)
