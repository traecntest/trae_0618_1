import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader
from config.settings import EXPORT_DIR, RESOURCES_DIR
from core.models.app import AppSchema
from utils import to_json


class AppGenerator:
    def __init__(self):
        template_dir = RESOURCES_DIR / "templates"
        template_dir.mkdir(exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            variable_start_string="<%",
            variable_end_string="%>",
            block_start_string="<%%",
            block_end_string="%%>",
            comment_start_string="<#",
            comment_end_string="#>"
        )
        self._ensure_templates()
    
    def _ensure_templates(self):
        templates = {
            "fastapi_main.py": self._get_fastapi_main_template(),
            "fastapi_models.py": self._get_fastapi_models_template(),
            "fastapi_database.py": self._get_fastapi_database_template(),
            "fastapi_auth.py": self._get_fastapi_auth_template(),
            "vue_app.vue": self._get_vue_app_template(),
            "vue_router.js": self._get_vue_router_template(),
            "vue_store.js": self._get_vue_store_template(),
            "vue_form.vue": self._get_vue_form_template(),
            "vue_page.vue": self._get_vue_page_template(),
            "Dockerfile": self._get_dockerfile_template(),
            "requirements.txt": self._get_requirements_template(),
        }
        
        for name, content in templates.items():
            template_path = RESOURCES_DIR / "templates" / name
            if not template_path.exists():
                template_path.write_text(content, encoding="utf-8")
    
    def generate_web_app(self, app_schema: AppSchema, output_dir: Optional[Path] = None) -> Path:
        if output_dir is None:
            output_dir = EXPORT_DIR / app_schema.config.name.replace(" ", "_")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        backend_dir = output_dir / "backend"
        frontend_dir = output_dir / "frontend"
        
        self._generate_backend(app_schema, backend_dir)
        self._generate_frontend(app_schema, frontend_dir)
        self._generate_dockerfile(app_schema, output_dir)
        self._generate_readme(app_schema, output_dir)
        self._generate_app_metadata(app_schema, output_dir)
        
        return output_dir
    
    def _generate_backend(self, app_schema: AppSchema, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        context = {
            "app_name": app_schema.config.name,
            "app_description": app_schema.config.description,
            "version": app_schema.config.version,
            "api_prefix": app_schema.config.api_prefix,
            "enable_auth": app_schema.config.enable_auth,
            "database_url": app_schema.config.deployment.database_url,
            "forms": app_schema.forms,
            "data_models": app_schema.data_models,
            "workflows": app_schema.workflows,
            "pages": app_schema.pages,
        }
        
        main_template = self.env.get_template("fastapi_main.py")
        models_template = self.env.get_template("fastapi_models.py")
        database_template = self.env.get_template("fastapi_database.py")
        auth_template = self.env.get_template("fastapi_auth.py")
        
        (output_dir / "main.py").write_text(main_template.render(context), encoding="utf-8")
        (output_dir / "models.py").write_text(models_template.render(context), encoding="utf-8")
        (output_dir / "database.py").write_text(database_template.render(context), encoding="utf-8")
        if app_schema.config.enable_auth:
            (output_dir / "auth.py").write_text(auth_template.render(context), encoding="utf-8")
        
        self._generate_routers(app_schema, output_dir)
        
        requirements_template = self.env.get_template("requirements.txt")
        (output_dir / "requirements.txt").write_text(
            requirements_template.render(context), encoding="utf-8"
        )
        
        schemas_dir = output_dir / "schemas"
        schemas_dir.mkdir(exist_ok=True)
        for form_id, form in app_schema.forms.items():
            (schemas_dir / f"form_{form_id}.json").write_text(form.to_json(), encoding="utf-8")
        for wf_id, workflow in app_schema.workflows.items():
            (schemas_dir / f"workflow_{wf_id}.json").write_text(workflow.to_json(), encoding="utf-8")
        for dm_id, data_model in app_schema.data_models.items():
            (schemas_dir / f"datamodel_{dm_id}.json").write_text(data_model.to_json(), encoding="utf-8")
    
    def _generate_routers(self, app_schema: AppSchema, output_dir: Path) -> None:
        routers_dir = output_dir / "routers"
        routers_dir.mkdir(exist_ok=True)
        
        init_content = ""
        for form_id, form in app_schema.forms.items():
            router_content = self._generate_form_router(form, app_schema)
            (routers_dir / f"{form.name.lower().replace(' ', '_')}.py").write_text(
                router_content, encoding="utf-8"
            )
            init_content += f"from .{form.name.lower().replace(' ', '_')} import router as {form.name.lower().replace(' ', '_')}_router\n"
        
        (routers_dir / "__init__.py").write_text(init_content, encoding="utf-8")
    
    def _generate_form_router(self, form, app_schema) -> str:
        return f'''from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from database import get_db
from models import FormData

router = APIRouter(prefix="/forms/{form.name.lower().replace(' ', '_')}", tags=["{form.name}"])


class FormDataCreate(BaseModel):
    data: dict
    workflow_instance_id: Optional[str] = None


class FormDataResponse(BaseModel):
    id: str
    form_id: str
    data: dict
    status: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=FormDataResponse)
async def create_form_data(form_data: FormDataCreate, db = Depends(get_db)):
    db_form = FormData(
        id="fd_{{datetime.now().timestamp()}}",
        form_id="{form.id}",
        workflow_instance_id=form_data.workflow_instance_id,
        data=form_data.data,
        status="submitted"
    )
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    return db_form


@router.get("/", response_model=List[FormDataResponse])
async def list_form_data(skip: int = 0, limit: int = 100, db = Depends(get_db)):
    return db.query(FormData).filter(FormData.form_id == "{form.id}").offset(skip).limit(limit).all()


@router.get("/{{item_id}}", response_model=FormDataResponse)
async def get_form_data(item_id: str, db = Depends(get_db)):
    db_form = db.query(FormData).filter(FormData.id == item_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Data not found")
    return db_form


@router.put("/{{item_id}}", response_model=FormDataResponse)
async def update_form_data(item_id: str, form_data: FormDataCreate, db = Depends(get_db)):
    db_form = db.query(FormData).filter(FormData.id == item_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Data not found")
    db_form.data = form_data.data
    db.commit()
    db.refresh(db_form)
    return db_form


@router.delete("/{{item_id}}")
async def delete_form_data(item_id: str, db = Depends(get_db)):
    db_form = db.query(FormData).filter(FormData.id == item_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Data not found")
    db.delete(db_form)
    db.commit()
    return {{"message": "Deleted successfully"}}
'''
    
    def _generate_frontend(self, app_schema: AppSchema, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        context = {
            "app_name": app_schema.config.name,
            "app_description": app_schema.config.description,
            "version": app_schema.config.version,
            "api_prefix": app_schema.config.api_prefix,
            "forms": app_schema.forms,
            "pages": app_schema.pages,
            "menus": app_schema.menus,
        }
        
        src_dir = output_dir / "src"
        src_dir.mkdir(exist_ok=True)
        views_dir = src_dir / "views"
        views_dir.mkdir(exist_ok=True)
        
        app_template = self.env.get_template("vue_app.vue")
        router_template = self.env.get_template("vue_router.js")
        store_template = self.env.get_template("vue_store.js")
        form_template = self.env.get_template("vue_form.vue")
        page_template = self.env.get_template("vue_page.vue")
        
        (src_dir / "App.vue").write_text(app_template.render(context), encoding="utf-8")
        (src_dir / "router.js").write_text(router_template.render(context), encoding="utf-8")
        (src_dir / "store.js").write_text(store_template.render(context), encoding="utf-8")
        
        for form_id, form in app_schema.forms.items():
            form_context = {**context, "form": form}
            (views_dir / f"{form.name.lower().replace(' ', '_')}_form.vue").write_text(
                form_template.render(form_context), encoding="utf-8"
            )
        
        for page_id, page in app_schema.pages.items():
            page_context = {**context, "page": page}
            (views_dir / f"{page.name.lower().replace(' ', '_')}_page.vue").write_text(
                page_template.render(page_context), encoding="utf-8"
            )
        
        package_json = {
            "name": app_schema.config.name.lower().replace(" ", "-"),
            "version": app_schema.config.version,
            "private": True,
            "scripts": {
                "serve": "vue-cli-service serve",
                "build": "vue-cli-service build",
            },
            "dependencies": {
                "vue": "^3.2.0",
                "vue-router": "^4.0.0",
                "vuex": "^4.0.0",
                "axios": "^1.6.0",
                "element-plus": "^2.4.0",
            },
        }
        (output_dir / "package.json").write_text(to_json(package_json), encoding="utf-8")
    
    def _generate_dockerfile(self, app_schema: AppSchema, output_dir: Path) -> None:
        template = self.env.get_template("Dockerfile")
        context = {
            "app_name": app_schema.config.name,
            "port": app_schema.config.deployment.port,
        }
        (output_dir / "Dockerfile").write_text(template.render(context), encoding="utf-8")
    
    def _generate_readme(self, app_schema: AppSchema, output_dir: Path) -> None:
        readme_content = f"""# {app_schema.config.name}

{app_schema.config.description}

## 版本信息
- 版本: {app_schema.config.version}
- 生成时间: {app_schema.updated_at if hasattr(app_schema, 'updated_at') else 'N/A'}

## 功能特性
- 表单数量: {len(app_schema.forms)} 个
- 工作流数量: {len(app_schema.workflows)} 个
- 数据模型数量: {len(app_schema.data_models)} 个
- 页面数量: {len(app_schema.pages)} 个

## 快速开始

### 方式一: Docker 部署

```bash
docker build -t {app_schema.config.name.lower().replace(' ', '-')} .
docker run -p {app_schema.config.deployment.port}:{app_schema.config.deployment.port} {app_schema.config.name.lower().replace(' ', '-')}
```

### 方式二: 本地运行

#### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port {app_schema.config.deployment.port}
```

#### 前端
```bash
cd frontend
npm install
npm run serve
```

## API 文档

启动后访问: http://localhost:{app_schema.config.deployment.port}/docs
"""
        (output_dir / "README.md").write_text(readme_content, encoding="utf-8")
    
    def _generate_app_metadata(self, app_schema: AppSchema, output_dir: Path) -> None:
        (output_dir / "app_schema.json").write_text(
            to_json(app_schema.to_dict()), encoding="utf-8"
        )
    
    def _get_fastapi_main_template(self) -> str:
        return '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routers import *

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="{{ app_name }}",
    description="{{ app_description }}",
    version="{{ version }}",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

{% if enable_auth %}
from auth import auth_router
app.include_router(auth_router, prefix="{{ api_prefix }}")
{% endif %}

app.include_router(form1_router, prefix="{{ api_prefix }}")

@app.get("/")
async def root():
    return {"message": "Welcome to {{ app_name }} API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
'''
    
    def _get_fastapi_models_template(self) -> str:
        return '''from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class FormData(Base):
    __tablename__ = "form_data"
    
    id = Column(String, primary_key=True, index=True)
    form_id = Column(String, index=True)
    workflow_instance_id = Column(String, index=True, nullable=True)
    data = Column(Text)
    status = Column(String, default="draft")
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, index=True)
    status = Column(String)
    current_node_ids = Column(Text)
    context = Column(Text)
    history = Column(Text)
    started_by = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
'''
    
    def _get_fastapi_database_template(self) -> str:
        return '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "{{ database_url }}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    
    def _get_fastapi_auth_template(self) -> str:
        return '''from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import get_db
from models import User

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="{{ api_prefix }}/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    full_name: str = ""


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@auth_router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/register")
async def register(user_data: UserCreate, db = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    import hashlib
    hashed = hashlib.sha256(user_data.password.encode()).hexdigest()
    user = User(
        id=f"user_{datetime.now().timestamp()}",
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed,
    )
    db.add(user)
    db.commit()
    return {"message": "User created successfully"}
'''
    
    def _get_vue_app_template(self) -> str:
        return '''<template>
  <div id="app">
    <el-container>
      <el-header v-if="showHeader">
        <h1>{{ appName }}</h1>
      </el-header>
      <el-container>
        <el-aside width="200px" v-if="showSidebar">
          <el-menu
            :default-active="activeMenu"
            router
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
          >
            <el-menu-item
              v-for="menu in menus"
              :key="menu.path"
              :index="menu.path"
            >
              {{ menu.name }}
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
export default {
  name: "App",
  data() {
    return {
      appName: "{{ app_name }}",
      showHeader: true,
      showSidebar: true,
      menus: {{ menus | tojson }},
    };
  },
  computed: {
    activeMenu() {
      return this.$route.path;
    },
  },
};
</script>

<style>
#app {
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
}
</style>
'''
    
    def _get_vue_router_template(self) -> str:
        return '''import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Home",
    component: () => import("./views/home_page.vue"),
  },
{% for page_id, page in pages.items() %}
  {
    path: "{{ page.route }}",
    name: "{{ page.name }}",
    component: () => import("./views/{{ page.name.lower().replace(' ', '_') }}_page.vue"),
  },
{% endfor %}
{% for form_id, form in forms.items() %}
  {
    path: "/form/{{ form.name.lower().replace(' ', '_') }}",
    name: "{{ form.name }}",
    component: () => import("./views/{{ form.name.lower().replace(' ', '_') }}_form.vue"),
  },
{% endfor %}
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
'''
    
    def _get_vue_store_template(self) -> str:
        return '''import { createStore } from "vuex";
import axios from "axios";

const API_BASE = "{{ api_prefix }}";

export default createStore({
  state: {
    user: null,
    token: localStorage.getItem("token") || "",
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem("token", token);
    },
    SET_USER(state, user) {
      state.user = user;
    },
    LOGOUT(state) {
      state.token = "";
      state.user = null;
      localStorage.removeItem("token");
    },
  },
  actions: {
    async login({ commit }, credentials) {
      const formData = new FormData();
      formData.append("username", credentials.username);
      formData.append("password", credentials.password);
      const response = await axios.post(`${API_BASE}/auth/token`, formData);
      commit("SET_TOKEN", response.data.access_token);
      return response.data;
    },
    logout({ commit }) {
      commit("LOGOUT");
    },
  },
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
});
'''
    
    def _get_vue_form_template(self) -> str:
        return '''<template>
  <div class="form-container">
    <h2>{{ form.name }}</h2>
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="submitForm"
    >
{% for field in form.fields %}
      <el-form-item label="{{ field.label }}" prop="{{ field.name }}" {% if field.required %}required{% endif %}>
{% if field.field_type == 'text' or field.field_type == 'number' %}
        <el-input
          v-model="formData.{{ field.name }}"
          :placeholder="'{{ field.placeholder }}'"
          :type="'{{ field.field_type }}'"
        />
{% elif field.field_type == 'textarea' %}
        <el-input
          v-model="formData.{{ field.name }}"
          type="textarea"
          :rows="3"
          :placeholder="'{{ field.placeholder }}'"
        />
{% elif field.field_type == 'select' %}
        <el-select v-model="formData.{{ field.name }}" placeholder="{{ field.placeholder }}">
          <el-option
            v-for="opt in {{ field.options }}"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
{% elif field.field_type == 'checkbox' %}
        <el-checkbox v-model="formData.{{ field.name }}">{{ field.label }}</el-checkbox>
{% elif field.field_type == 'radio' %}
        <el-radio-group v-model="formData.{{ field.name }}">
          <el-radio
            v-for="opt in {{ field.options }}"
            :key="opt.value"
            :label="opt.value"
          >{{ opt.label }}</el-radio>
        </el-radio-group>
{% elif field.field_type == 'date' %}
        <el-date-picker
          v-model="formData.{{ field.name }}"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
        />
{% elif field.field_type == 'datetime' %}
        <el-date-picker
          v-model="formData.{{ field.name }}"
          type="datetime"
          placeholder="选择日期时间"
          value-format="YYYY-MM-DD HH:mm:ss"
        />
{% elif field.field_type == 'file' %}
        <el-upload
          v-model="formData.{{ field.name }}"
          action="#"
          :auto-upload="false"
        >
          <el-button>点击上传</el-button>
        </el-upload>
{% else %}
        <el-input v-model="formData.{{ field.name }}" />
{% endif %}
      </el-form-item>
{% endfor %}
      <el-form-item>
        <el-button type="primary" @click="submitForm">提交</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "{{ form.name }}Form",
  data() {
    return {
      formData: {
{% for field in form.fields %}
        {{ field.name }}: {% if field.default_value is not none %}{{ field.default_value }}{% else %}{% if field.field_type == 'checkbox' %}false{% else %}""{% endif %}{% endif %},
{% endfor %}
      },
      rules: {
{% for field in form.fields %}
{% if field.required %}
        {{ field.name }}: [{ required: true, message: "{{ field.label }}是必填项", trigger: "blur" }],
{% endif %}
{% endfor %}
      },
    };
  },
  methods: {
    async submitForm() {
      try {
        await axios.post("/api/v1/forms/{{ form.name.lower().replace(' ', '_') }}/", {
          data: this.formData,
        });
        this.$message.success("提交成功!");
        this.resetForm();
      } catch (error) {
        this.$message.error("提交失败");
      }
    },
    resetForm() {
      this.$refs.formRef.resetFields();
    },
  },
};
</script>

<style scoped>
.form-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}
</style>
'''
    
    def _get_vue_page_template(self) -> str:
        return '''<template>
  <div class="page-container">
    <h2>{{ page.title || page.name }}</h2>
    <div class="page-content">
      <div v-for="component in pageComponents" :key="component.id">
        <component :is="getComponentType(component.type)" :data="component" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "{{ page.name }}Page",
  data() {
    return {
      pageComponents: {{ page.root_component.children | tojson }},
    };
  },
  methods: {
    getComponentType(type) {
      return `component-${type}`;
    },
  },
};
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.page-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
'''
    
    def _get_dockerfile_template(self) -> str:
        return '''FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE {{ port }}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{{ port }}"]
'''
    
    def _get_requirements_template(self) -> str:
        return '''fastapi>=0.104.1
uvicorn>=0.24.0
sqlalchemy>=2.0.23
pydantic>=2.5.2
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.6
jinja2>=3.1.2
'''
