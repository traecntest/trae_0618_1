from typing import Any, Dict, List, Optional
from core.models.page import PageSchema, Component, LayoutConfig
from core.models.form import FormSchema
from utils import safe_eval


class RenderEngine:
    def __init__(self):
        self.component_renderers = {
            "container": self._render_container,
            "button": self._render_button,
            "table": self._render_table,
            "form": self._render_form_component,
            "chart": self._render_chart,
            "card": self._render_card,
            "tabs": self._render_tabs,
            "menu": self._render_menu,
        }

    def render_page(self, page_schema: PageSchema, context: Optional[Dict[str, Any]] = None, width: int = 1200) -> Dict[str, Any]:
        context = context or {}
        layout = page_schema.responsive.get_layout_for_width(width)
        
        return {
            "id": page_schema.id,
            "name": page_schema.name,
            "route": page_schema.route,
            "title": page_schema.title,
            "layout": layout.to_dict(),
            "style": page_schema.style,
            "components": self._render_component(page_schema.root_component, context, width),
            "permissions": page_schema.permissions,
        }

    def _render_component(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        renderer = self.component_renderers.get(
            component.component_type, self._render_default
        )
        
        rendered = renderer(component, context, width)
        rendered["children"] = [
            self._render_component(child, context, width)
            for child in component.children
        ]
        
        return rendered

    def _render_container(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        layout = component.layout or LayoutConfig()
        return {
            "id": component.id,
            "type": "container",
            "name": component.name,
            "props": self._process_props(component.props, context),
            "style": component.style,
            "layout": layout.to_dict(),
            "permissions": component.permissions,
        }

    def _render_button(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        props = self._process_props(component.props, context)
        return {
            "id": component.id,
            "type": "button",
            "name": component.name,
            "label": props.get("text", "按钮"),
            "button_type": props.get("type", "primary"),
            "disabled": props.get("disabled", False),
            "props": props,
            "style": component.style,
            "events": [e.to_dict() for e in component.events],
            "permissions": component.permissions,
        }

    def _render_table(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        props = self._process_props(component.props, context)
        data = self._resolve_binding(component.bindings, context) if component.bindings else []
        
        return {
            "id": component.id,
            "type": "table",
            "name": component.name,
            "columns": props.get("columns", []),
            "data": data,
            "pagination": props.get("pagination", True),
            "props": props,
            "style": component.style,
            "permissions": component.permissions,
        }

    def _render_form_component(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        props = self._process_props(component.props, context)
        form_schema_id = props.get("form_id")
        form_data = self._resolve_binding(component.bindings, context) if component.bindings else {}
        
        return {
            "id": component.id,
            "type": "form",
            "name": component.name,
            "form_id": form_schema_id,
            "form_data": form_data,
            "readonly": props.get("readonly", False),
            "props": props,
            "style": component.style,
            "permissions": component.permissions,
        }

    def _render_chart(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        props = self._process_props(component.props, context)
        data = self._resolve_binding(component.bindings, context) if component.bindings else []
        
        return {
            "id": component.id,
            "type": "chart",
            "name": component.name,
            "chart_type": props.get("chart_type", "line"),
            "data": data,
            "options": props.get("options", {}),
            "props": props,
            "style": component.style,
            "permissions": component.permissions,
        }

    def _render_card(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        props = self._process_props(component.props, context)
        return {
            "id": component.id,
            "type": "card",
            "name": component.name,
            "title": props.get("title", ""),
            "props": props,
            "style": component.style,
            "permissions": component.permissions,
        }

    def _render_tabs(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        props = self._process_props(component.props, context)
        return {
            "id": component.id,
            "type": "tabs",
            "name": component.name,
            "tabs": props.get("tabs", []),
            "active_tab": props.get("active_tab", 0),
            "props": props,
            "style": component.style,
            "permissions": component.permissions,
        }

    def _render_menu(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        props = self._process_props(component.props, context)
        return {
            "id": component.id,
            "type": "menu",
            "name": component.name,
            "items": props.get("items", []),
            "mode": props.get("mode", "vertical"),
            "props": props,
            "style": component.style,
            "permissions": component.permissions,
        }

    def _render_default(self, component: Component, context: Dict[str, Any], width: int) -> Dict[str, Any]:
        return {
            "id": component.id,
            "type": component.component_type,
            "name": component.name,
            "props": self._process_props(component.props, context),
            "style": component.style,
            "permissions": component.permissions,
        }

    def _process_props(self, props: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in props.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                expression = value[2:-2].strip()
                try:
                    result[key] = safe_eval(expression, context)
                except Exception:
                    result[key] = value
            else:
                result[key] = value
        return result

    def _resolve_binding(self, binding, context: Dict[str, Any]) -> Any:
        if not binding:
            return None
        
        source = binding.source
        field = binding.field
        
        data = context.get(source, [])
        
        if binding.filter_condition:
            try:
                data = [
                    item for item in data
                    if safe_eval(binding.filter_condition, {"item": item, **context})
                ]
            except Exception:
                pass
        
        if binding.transform:
            try:
                data = safe_eval(binding.transform, {"data": data, **context})
            except Exception:
                pass
        
        if field and isinstance(data, dict):
            return data.get(field)
        
        return data

    def render_form(self, form_schema: FormSchema, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from core.engine import FormEngine
        form_engine = FormEngine()
        return form_engine.render_form(form_schema, data)
