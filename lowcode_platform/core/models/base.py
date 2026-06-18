from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel as PydanticBaseModel, Field
from utils import generate_id, to_json, from_json


class BaseModel(PydanticBaseModel):
    id: str = Field(default_factory=lambda: generate_id())
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True
        populate_by_name = True

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    def to_json(self, indent: int = 2) -> str:
        return to_json(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "BaseModel":
        data = from_json(json_str)
        return cls.from_dict(data)

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
