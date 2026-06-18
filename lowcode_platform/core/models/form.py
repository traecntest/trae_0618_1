from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import BaseModel
from utils import generate_id


class ValidationRule(BaseModel):
    type: str = "required"
    message: str = ""
    params: Dict[str, Any] = Field(default_factory=dict)


class FieldSchema(BaseModel):
    field_type: str = "text"
    label: str = ""
    name: str = ""
    required: bool = False
    placeholder: str = ""
    default_value: Any = None
    props: Dict[str, Any] = Field(default_factory=dict)
    validation: List[ValidationRule] = Field(default_factory=list)
    options: List[Dict[str, Any]] = Field(default_factory=list)
    width: int = 12
    position: Dict[str, int] = Field(default_factory=dict)

    @classmethod
    def create(cls, field_type: str, label: str = "", **kwargs) -> "FieldSchema":
        name = kwargs.pop("name", None) or f"field_{generate_id()[:8]}"
        return cls(
            field_type=field_type,
            label=label or field_type,
            name=name,
            **kwargs
        )


class LayoutConfig(BaseModel):
    type: str = "grid"
    columns: int = 12
    gap: int = 16
    label_width: int = 120
    label_position: str = "left"


class FormSchema(BaseModel):
    name: str = "新建表单"
    description: str = ""
    fields: List[FieldSchema] = Field(default_factory=list)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    data_source: Optional[str] = None
    events: Dict[str, str] = Field(default_factory=dict)
    style: Dict[str, Any] = Field(default_factory=dict)

    def add_field(self, field_type: str, **kwargs) -> FieldSchema:
        field = FieldSchema.create(field_type, **kwargs)
        self.fields.append(field)
        return field

    def remove_field(self, field_id: str) -> None:
        self.fields = [f for f in self.fields if f.id != field_id]

    def get_field(self, field_id: str) -> Optional[FieldSchema]:
        for field in self.fields:
            if field.id == field_id:
                return field
        return None

    def move_field(self, field_id: str, new_index: int) -> None:
        for i, field in enumerate(self.fields):
            if field.id == field_id:
                self.fields.pop(i)
                self.fields.insert(new_index, field)
                break


class FormInstance(BaseModel):
    form_id: str
    form_data: Dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"
    workflow_instance_id: Optional[str] = None
    created_by: Optional[str] = None

    def validate(self) -> tuple[bool, List[str]]:
        errors = []
        from core.engine import FormEngine
        engine = FormEngine()
        return engine.validate_form_data(self.form_data, FormSchema)
