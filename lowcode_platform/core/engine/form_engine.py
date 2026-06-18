import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from core.models.form import FormSchema, FieldSchema, FormInstance, ValidationRule
from utils import generate_id


class FormEngine:
    def __init__(self):
        self.validators = {
            "required": self._validate_required,
            "min_length": self._validate_min_length,
            "max_length": self._validate_max_length,
            "min": self._validate_min,
            "max": self._validate_max,
            "pattern": self._validate_pattern,
            "email": self._validate_email,
            "phone": self._validate_phone,
        }

    def render_form(self, form_schema: FormSchema, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rendered = {
            "id": form_schema.id,
            "name": form_schema.name,
            "fields": [],
            "layout": form_schema.layout.to_dict(),
        }
        
        for field in form_schema.fields:
            field_data = self._render_field(field, data)
            rendered["fields"].append(field_data)
        
        return rendered

    def _render_field(self, field: FieldSchema, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        value = None
        if data and field.name in data:
            value = data[field.name]
        elif field.default_value is not None:
            value = field.default_value
        
        return {
            "id": field.id,
            "type": field.field_type,
            "label": field.label,
            "name": field.name,
            "required": field.required,
            "placeholder": field.placeholder,
            "value": value,
            "props": field.props,
            "options": field.options,
            "width": field.width,
            "validation": [v.to_dict() for v in field.validation],
        }

    def validate_form_data(
        self, form_data: Dict[str, Any], form_schema: FormSchema
    ) -> Tuple[bool, List[str]]:
        errors = []
        
        for field in form_schema.fields:
            value = form_data.get(field.name)
            
            if field.required:
                valid, error = self._validate_required(field, value)
                if not valid:
                    errors.append(error)
                    continue
            
            for rule in field.validation:
                validator = self.validators.get(rule.type)
                if validator:
                    valid, error = validator(field, value, rule.params)
                    if not valid:
                        errors.append(rule.message or error)
        
        return len(errors) == 0, errors

    def _validate_required(self, field: FieldSchema, value: Any, params: Optional[Dict] = None) -> Tuple[bool, str]:
        if value is None or value == "":
            return False, f"{field.label} 是必填项"
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False, f"{field.label} 是必填项"
        return True, ""

    def _validate_min_length(self, field: FieldSchema, value: Any, params: Dict) -> Tuple[bool, str]:
        min_len = params.get("min", 0)
        if value and len(str(value)) < min_len:
            return False, f"{field.label} 最少需要 {min_len} 个字符"
        return True, ""

    def _validate_max_length(self, field: FieldSchema, value: Any, params: Dict) -> Tuple[bool, str]:
        max_len = params.get("max", 1000)
        if value and len(str(value)) > max_len:
            return False, f"{field.label} 最多允许 {max_len} 个字符"
        return True, ""

    def _validate_min(self, field: FieldSchema, value: Any, params: Dict) -> Tuple[bool, str]:
        min_val = params.get("min", 0)
        if value is not None and float(value) < min_val:
            return False, f"{field.label} 不能小于 {min_val}"
        return True, ""

    def _validate_max(self, field: FieldSchema, value: Any, params: Dict) -> Tuple[bool, str]:
        max_val = params.get("max", float("inf"))
        if value is not None and float(value) > max_val:
            return False, f"{field.label} 不能大于 {max_val}"
        return True, ""

    def _validate_pattern(self, field: FieldSchema, value: Any, params: Dict) -> Tuple[bool, str]:
        pattern = params.get("pattern", "")
        if value and pattern:
            if not re.match(pattern, str(value)):
                return False, f"{field.label} 格式不正确"
        return True, ""

    def _validate_email(self, field: FieldSchema, value: Any, params: Optional[Dict] = None) -> Tuple[bool, str]:
        if value:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, str(value)):
                return False, f"{field.label} 邮箱格式不正确"
        return True, ""

    def _validate_phone(self, field: FieldSchema, value: Any, params: Optional[Dict] = None) -> Tuple[bool, str]:
        if value:
            phone_pattern = r"^1[3-9]\d{9}$"
            if not re.match(phone_pattern, str(value)):
                return False, f"{field.label} 手机号格式不正确"
        return True, ""

    def create_form_instance(
        self, form_id: str, form_data: Dict[str, Any], created_by: Optional[str] = None
    ) -> FormInstance:
        return FormInstance(
            id=generate_id("form_inst"),
            form_id=form_id,
            form_data=form_data,
            status="draft",
            created_by=created_by,
        )

    def submit_form(self, form_instance: FormInstance, form_schema: FormSchema) -> Tuple[bool, List[str]]:
        valid, errors = self.validate_form_data(form_instance.form_data, form_schema)
        if not valid:
            return False, errors
        
        form_instance.status = "submitted"
        return True, []

    def get_field_value(self, form_data: Dict[str, Any], field_name: str) -> Any:
        return form_data.get(field_name)

    def set_field_value(self, form_data: Dict[str, Any], field_name: str, value: Any) -> None:
        form_data[field_name] = value

    def merge_data(self, base_data: Dict[str, Any], override_data: Dict[str, Any]) -> Dict[str, Any]:
        result = base_data.copy()
        result.update(override_data)
        return result
