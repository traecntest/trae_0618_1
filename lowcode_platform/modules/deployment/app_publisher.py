import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from core.models.app import AppSchema
from core.engine import AppGenerator
from config.settings import EXPORT_DIR
from utils import to_json


class AppPublisher:
    def __init__(self):
        self.generator = AppGenerator()
        self._deployment_status: Dict[str, Any] = {}

    def publish_app(
        self,
        app_schema: AppSchema,
        target_dir: Optional[Path] = None,
        deploy_type: str = "local"
    ) -> Dict[str, Any]:
        app_schema.publish()
        
        output_dir = self.generator.generate_web_app(app_schema, target_dir)
        
        result = {
            "success": True,
            "app_name": app_schema.config.name,
            "version": app_schema.config.version,
            "output_dir": str(output_dir),
            "deploy_type": deploy_type,
            "published_at": datetime.now().isoformat(),
            "backend_dir": str(output_dir / "backend"),
            "frontend_dir": str(output_dir / "frontend"),
        }
        
        if deploy_type == "docker":
            docker_result = self._build_docker_image(output_dir, app_schema)
            result.update(docker_result)
        elif deploy_type == "local":
            local_result = self._prepare_local_deploy(output_dir, app_schema)
            result.update(local_result)
        
        self._save_deployment_record(app_schema.id, result)
        
        return result

    def _build_docker_image(self, output_dir: Path, app_schema: AppSchema) -> Dict[str, Any]:
        image_name = app_schema.config.name.lower().replace(" ", "-")
        image_tag = f"{image_name}:{app_schema.config.version}"
        
        try:
            subprocess.run(
                ["docker", "build", "-t", image_tag, "."],
                cwd=output_dir,
                check=True,
                capture_output=True,
                text=True
            )
            return {
                "docker_image": image_tag,
                "docker_build_success": True,
            }
        except subprocess.CalledProcessError as e:
            return {
                "docker_build_success": False,
                "docker_error": e.stderr,
            }
        except FileNotFoundError:
            return {
                "docker_build_success": False,
                "docker_error": "Docker 未安装或不在 PATH 中",
            }

    def _prepare_local_deploy(self, output_dir: Path, app_schema: AppSchema) -> Dict[str, Any]:
        port = app_schema.config.deployment.port
        start_commands = {
            "backend": f"cd backend && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port {port}",
            "frontend": "cd frontend && npm install && npm run serve",
            "full": f"启动后端: uvicorn main:app --host 0.0.0.0 --port {port}\n启动前端: npm run serve",
        }
        
        return {
            "access_url": f"http://localhost:{port}",
            "start_commands": start_commands,
            "api_docs_url": f"http://localhost:{port}/docs",
        }

    def _save_deployment_record(self, app_id: str, result: Dict[str, Any]) -> None:
        record_dir = EXPORT_DIR / "deployments"
        record_dir.mkdir(exist_ok=True)
        
        record_file = record_dir / f"{app_id}_deployments.json"
        records = []
        
        if record_file.exists():
            from utils import from_json
            with open(record_file, "r", encoding="utf-8") as f:
                records = from_json(f.read())
        
        records.append(result)
        
        with open(record_file, "w", encoding="utf-8") as f:
            f.write(to_json(records))

    def unpublish_app(self, app_schema: AppSchema) -> Dict[str, Any]:
        app_schema.unpublish()
        
        return {
            "success": True,
            "app_name": app_schema.config.name,
            "unpublished_at": datetime.now().isoformat(),
        }

    def get_deployment_history(self, app_id: str) -> list:
        record_file = EXPORT_DIR / "deployments" / f"{app_id}_deployments.json"
        if record_file.exists():
            from utils import from_json
            with open(record_file, "r", encoding="utf-8") as f:
                return from_json(f.read())
        return []

    def export_app_package(self, app_schema: AppSchema, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            output_path = EXPORT_DIR / f"{app_schema.config.name.replace(' ', '_')}_package.zip"
        
        app_dir = self.generator.generate_web_app(app_schema)
        
        zip_path = Path(output_path)
        if zip_path.suffix != ".zip":
            zip_path = zip_path.with_suffix(".zip")
        
        shutil.make_archive(
            str(zip_path.with_suffix("")),
            "zip",
            root_dir=app_dir.parent,
            base_dir=app_dir.name
        )
        
        return zip_path

    def import_app_package(self, package_path: Path) -> Optional[AppSchema]:
        package_path = Path(package_path)
        if not package_path.exists():
            return None
        
        extract_dir = EXPORT_DIR / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        extract_dir.mkdir(exist_ok=True)
        
        shutil.unpack_archive(str(package_path), str(extract_dir))
        
        schema_file = extract_dir / "app_schema.json"
        if schema_file.exists():
            from utils import from_json
            with open(schema_file, "r", encoding="utf-8") as f:
                data = from_json(f.read())
            return AppSchema.from_dict(data)
        
        return None

    def validate_app(self, app_schema: AppSchema) -> Dict[str, Any]:
        issues = []
        warnings = []
        
        if not app_schema.config.name:
            issues.append("应用名称不能为空")
        
        if not app_schema.forms:
            warnings.append("应用没有定义任何表单")
        
        if not app_schema.pages:
            warnings.append("应用没有定义任何页面")
        
        for form_id, form in app_schema.forms.items():
            if not form.fields:
                warnings.append(f"表单 '{form.name}' 没有定义任何字段")
        
        for workflow_id, workflow in app_schema.workflows.items():
            if not workflow.get_start_node():
                issues.append(f"流程 '{workflow.name}' 没有开始节点")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "forms_count": len(app_schema.forms),
            "workflows_count": len(app_schema.workflows),
            "pages_count": len(app_schema.pages),
            "data_models_count": len(app_schema.data_models),
        }

    def start_preview(self, app_schema: AppSchema, port: int = 8000) -> subprocess.Popen:
        app_dir = self.generator.generate_web_app(app_schema)
        backend_dir = app_dir / "backend"
        
        pip_process = subprocess.Popen(
            ["pip", "install", "-r", "requirements.txt"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        pip_process.wait()
        
        process = subprocess.Popen(
            ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return process

    def stop_preview(self, process: subprocess.Popen) -> None:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
