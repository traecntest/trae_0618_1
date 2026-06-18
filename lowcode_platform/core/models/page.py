from typing import Any, Dict, List, Optional, ClassVar
from pydantic import Field
from .base import BaseModel


class DataBinding(BaseModel):
    source: str = ""
    field: str = ""
    transform: Optional[str] = None
    filter_condition: Optional[str] = None


class ComponentEvent(BaseModel):
    event_name: str = ""
    action: str = ""
    params: Dict[str, Any] = Field(default_factory=dict)


class LayoutConfig(BaseModel):
    type: str = "flex"
    direction: str = "column"
    gap: int = 16
    padding: int = 16
    justify: str = "flex-start"
    align: str = "stretch"
    wrap: bool = False


class ResponsiveConfig(BaseModel):
    xs: LayoutConfig = Field(default_factory=LayoutConfig)
    sm: Optional[LayoutConfig] = None
    md: Optional[LayoutConfig] = None
    lg: Optional[LayoutConfig] = None
    xl: Optional[LayoutConfig] = None

    BREAKPOINTS: ClassVar[Dict[str, int]] = {
        "xs": 0,
        "sm": 576,
        "md": 768,
        "lg": 992,
        "xl": 1200
    }

    def get_layout_for_width(self, width: int) -> LayoutConfig:
        for bp in reversed(self.BREAKPOINTS):
            if width >= self.BREAKPOINTS[bp]:
                layout = getattr(self, bp, None)
                if layout:
                    return layout
        return self.xs


class Component(BaseModel):
    component_type: str = "container"
    name: str = ""
    props: Dict[str, Any] = Field(default_factory=dict)
    style: Dict[str, Any] = Field(default_factory=dict)
    children: List["Component"] = Field(default_factory=list)
    bindings: Optional[DataBinding] = None
    events: List[ComponentEvent] = Field(default_factory=list)
    layout: Optional[LayoutConfig] = None
    permissions: List[str] = Field(default_factory=list)

    @classmethod
    def create(cls, component_type: str, name: str = "", **kwargs) -> "Component":
        return cls(component_type=component_type, name=name or component_type, **kwargs)

    def add_child(self, child: "Component") -> None:
        self.children.append(child)

    def remove_child(self, child_id: str) -> None:
        self.children = [c for c in self.children if c.id != child_id]

    def find_component(self, component_id: str) -> Optional["Component"]:
        if self.id == component_id:
            return self
        for child in self.children:
            found = child.find_component(component_id)
            if found:
                return found
        return None

    def get_all_components(self) -> List["Component"]:
        result = [self]
        for child in self.children:
            result.extend(child.get_all_components())
        return result


class PageSchema(BaseModel):
    name: str = "新建页面"
    route: str = "/"
    title: str = ""
    description: str = ""
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    root_component: Component = Field(default_factory=lambda: Component.create("container", "root"))
    responsive: ResponsiveConfig = Field(default_factory=ResponsiveConfig)
    style: Dict[str, Any] = Field(default_factory=dict)
    scripts: List[str] = Field(default_factory=list)
    stylesheets: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)

    def add_component(self, component_type: str, parent_id: Optional[str] = None, **kwargs) -> Component:
        component = Component.create(component_type, **kwargs)
        if parent_id:
            parent = self.find_component(parent_id)
            if parent:
                parent.add_child(component)
        else:
            self.root_component.add_child(component)
        return component

    def remove_component(self, component_id: str) -> None:
        if self.root_component.id == component_id:
            return
        self.root_component.remove_child(component_id)

    def find_component(self, component_id: str) -> Optional[Component]:
        return self.root_component.find_component(component_id)

    def get_all_components(self) -> List[Component]:
        return self.root_component.get_all_components()
