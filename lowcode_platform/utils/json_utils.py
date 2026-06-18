import json
import orjson
from datetime import datetime, date
from typing import Any, Dict, List, Optional


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def to_json(data: Any, indent: int = 2, use_orjson: bool = True) -> str:
    if use_orjson:
        try:
            options = orjson.OPT_INDENT_2 if indent > 0 else 0
            options |= orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC
            return orjson.dumps(data, option=options).decode("utf-8")
        except (TypeError, ValueError):
            pass
    return json.dumps(data, cls=DateTimeEncoder, indent=indent, ensure_ascii=False)


def from_json(json_str: str, use_orjson: bool = True) -> Any:
    if use_orjson:
        try:
            return orjson.loads(json_str)
        except (TypeError, ValueError):
            pass
    return json.loads(json_str)


def save_json(file_path: str, data: Any) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(to_json(data))


def load_json(file_path: str) -> Any:
    with open(file_path, "r", encoding="utf-8") as f:
        return from_json(f.read())


def deep_copy(data: Any) -> Any:
    return from_json(to_json(data, indent=0))
