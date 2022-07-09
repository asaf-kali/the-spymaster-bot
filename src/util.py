import json
from typing import Any


def json_safe(x: Any) -> Any:
    if isinstance(x, (int, float, str, bool)):
        return x
    try:
        return json.dumps(x)
    except:  # noqa
        return str(x)


def create_response(status_code: int, data: dict):
    return {"statusCode": status_code, "body": json.dumps(data)}
