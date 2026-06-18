import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from config.settings import JSON_STORAGE_DIR
from utils import to_json, from_json, generate_id
from core.models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonStore:
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or JSON_STORAGE_DIR
        self.storage_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, Dict[str, T]] = {}

    def _get_file_path(self, entity_type: str) -> Path:
        return self.storage_dir / f"{entity_type}.json"

    def _load(self, entity_type: str) -> Dict[str, Any]:
        file_path = self._get_file_path(entity_type)
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return from_json(f.read())
        except Exception:
            return {}

    def _save(self, entity_type: str, data: Dict[str, Any]) -> None:
        file_path = self._get_file_path(entity_type)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(to_json(data))

    def save(self, entity_type: str, entity: T) -> T:
        data = self._load(entity_type)
        entity_dict = entity.to_dict()
        data[entity.id] = entity_dict
        self._save(entity_type, data)
        if entity_type not in self._cache:
            self._cache[entity_type] = {}
        self._cache[entity_type][entity.id] = entity
        return entity

    def get(self, entity_type: str, entity_id: str, model_class: Type[T]) -> Optional[T]:
        if entity_type in self._cache and entity_id in self._cache[entity_type]:
            return self._cache[entity_type][entity_id]
        
        data = self._load(entity_type)
        if entity_id in data:
            entity = model_class.from_dict(data[entity_id])
            if entity_type not in self._cache:
                self._cache[entity_type] = {}
            self._cache[entity_type][entity_id] = entity
            return entity
        return None

    def get_all(self, entity_type: str, model_class: Type[T]) -> List[T]:
        data = self._load(entity_type)
        result = []
        if entity_type not in self._cache:
            self._cache[entity_type] = {}
        for entity_id, entity_dict in data.items():
            if entity_id in self._cache[entity_type]:
                result.append(self._cache[entity_type][entity_id])
            else:
                entity = model_class.from_dict(entity_dict)
                self._cache[entity_type][entity_id] = entity
                result.append(entity)
        return result

    def delete(self, entity_type: str, entity_id: str) -> bool:
        data = self._load(entity_type)
        if entity_id in data:
            del data[entity_id]
            self._save(entity_type, data)
            if entity_type in self._cache and entity_id in self._cache[entity_type]:
                del self._cache[entity_type][entity_id]
            return True
        return False

    def exists(self, entity_type: str, entity_id: str) -> bool:
        data = self._load(entity_type)
        return entity_id in data

    def count(self, entity_type: str) -> int:
        data = self._load(entity_type)
        return len(data)

    def clear_cache(self, entity_type: Optional[str] = None) -> None:
        if entity_type:
            if entity_type in self._cache:
                del self._cache[entity_type]
        else:
            self._cache.clear()

    def find_by_field(self, entity_type: str, field_name: str, value: Any, model_class: Type[T]) -> List[T]:
        all_entities = self.get_all(entity_type, model_class)
        return [e for e in all_entities if getattr(e, field_name, None) == value]
