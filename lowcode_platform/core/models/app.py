from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import BaseModel
from .form import FormSchema
from .workflow import WorkflowSchema
from .data_model import DataModel
from .page import PageSchema


class AppStatus(str):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DeploymentConfig(BaseModel):
    type: str = "local"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./app.db"
    docker: bool = False
    docker_image: str = ""
    env_vars: Dict[str, str] = Field(default_factory=dict)


class AppConfig(BaseModel):
    name: str = "新建应用"
    description: str = ""
    icon: str = "📱"
    color: str = "#1890ff"
    version: str = "1.0.0"
    default_route: str = "/"
    enable_auth: bool = True
    enable_workflow: bool = True
    enable_api: bool = True
    api_prefix: str = "/api/v1"
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)


class AppSchema(BaseModel):
    config: AppConfig = Field(default_factory=AppConfig)
    forms: Dict[str, FormSchema] = Field(default_factory=dict)
    workflows: Dict[str, WorkflowSchema] = Field(default_factory=dict)
    data_models: Dict[str, DataModel] = Field(default_factory=dict)
    pages: Dict[str, PageSchema] = Field(default_factory=dict)
    roles: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[Dict[str, Any]] = Field(default_factory=list)
    menus: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "draft"
    published_version: Optional[str] = None

    def add_form(self, form: FormSchema) -> None:
        self.forms[form.id] = form

    def remove_form(self, form_id: str) -> None:
        if form_id in self.forms:
            del self.forms[form_id]

    def get_form(self, form_id: str) -> Optional[FormSchema]:
        return self.forms.get(form_id)

    def add_workflow(self, workflow: WorkflowSchema) -> None:
        self.workflows[workflow.id] = workflow

    def remove_workflow(self, workflow_id: str) -> None:
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowSchema]:
        return self.workflows.get(workflow_id)

    def add_data_model(self, data_model: DataModel) -> None:
        self.data_models[data_model.id] = data_model

    def remove_data_model(self, model_id: str) -> None:
        if model_id in self.data_models:
            del self.data_models[model_id]

    def get_data_model(self, model_id: str) -> Optional[DataModel]:
        return self.data_models.get(model_id)

    def add_page(self, page: PageSchema) -> None:
        self.pages[page.id] = page

    def remove_page(self, page_id: str) -> None:
        if page_id in self.pages:
            del self.pages[page_id]

    def get_page(self, page_id: str) -> Optional[PageSchema]:
        return self.pages.get(page_id)

    def publish(self, version: Optional[str] = None) -> None:
        self.status = "published"
        self.published_version = version or self.config.version

    def unpublish(self) -> None:
        self.status = "draft"
        self.published_version = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["forms"] = {k: v.to_dict() for k, v in self.forms.items()}
        data["workflows"] = {k: v.to_dict() for k, v in self.workflows.items()}
        data["data_models"] = {k: v.to_dict() for k, v in self.data_models.items()}
        data["pages"] = {k: v.to_dict() for k, v in self.pages.items()}
        return data
