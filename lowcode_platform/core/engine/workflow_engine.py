from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque
from core.models.workflow import (
    WorkflowSchema, WorkflowInstance, Node, NodeState, CountersignMode
)
from core.storage.database import SQLiteStorage
from utils import generate_id, safe_eval


class NodeExecutor:
    def execute(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        executor = getattr(self, f"_execute_{node.type}", self._execute_default)
        return executor(node, context)
    
    def _execute_start(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        return True, {"message": "流程启动"}
    
    def _execute_end(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        return True, {"message": "流程结束"}
    
    def _execute_task(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        config = node.config
        result = {
            "assignee": config.assignee,
            "assignees": config.assignees,
            "form_id": config.form_id,
            "task_name": node.name,
        }
        return True, result
    
    def _execute_condition(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        return True, {"message": "条件判断节点"}
    
    def _execute_parallel(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        return True, {"message": "并行网关节点", "parallel": True}
    
    def _execute_countersign(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        config = node.config
        result = {
            "assignees": config.assignees,
            "mode": config.countersign_mode,
            "percentage": config.countersign_percentage,
            "countersign": True,
        }
        return True, result
    
    def _execute_subprocess(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        return True, {"message": "子流程节点", "subprocess": True}
    
    def _execute_default(self, node: Node, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        return True, {"message": f"执行节点: {node.name}"}


class WorkflowEngine:
    def __init__(self):
        self.node_executor = NodeExecutor()
        self.storage = SQLiteStorage()
        self._pending_tasks: Dict[str, Dict[str, Any]] = {}
        self._countersign_states: Dict[str, Dict[str, Any]] = {}
    
    def start_workflow(
        self, workflow_schema: WorkflowSchema, initial_data: Optional[Dict[str, Any]] = None,
        started_by: Optional[str] = None
    ) -> WorkflowInstance:
        start_node = workflow_schema.get_start_node()
        if not start_node:
            raise ValueError("流程中没有开始节点")
        
        instance = WorkflowInstance(
            id=generate_id("wf_inst"),
            workflow_id=workflow_schema.id,
            status="running",
            current_node_ids=[],
            context=initial_data or {},
            started_by=started_by,
        )
        
        instance.add_history("start", node_id=start_node.id, node_name=start_node.name)
        
        self.storage.save_workflow_instance(instance.to_dict())
        
        self._execute_node(workflow_schema, instance, start_node)
        
        return instance
    
    def _execute_node(
        self, workflow_schema: WorkflowSchema, instance: WorkflowInstance, node: Node
    ) -> None:
        instance.set_node_state(node.id, "running")
        
        success, result = self.node_executor.execute(node, instance.context)
        
        if not success:
            instance.set_node_state(node.id, "failed")
            instance.status = "error"
            instance.add_history("error", node_id=node.id, error=result.get("error", "执行失败"))
            self._save_instance(instance)
            return
        
        instance.add_history(
            "execute",
            node_id=node.id,
            node_name=node.name,
            node_type=node.type,
            result=result
        )
        
        if node.type == "task":
            task_key = f"{instance.id}_{node.id}"
            self._pending_tasks[task_key] = {
                "instance_id": instance.id,
                "node_id": node.id,
                "assignee": node.config.assignee,
                "assignees": node.config.assignees,
                "form_id": node.config.form_id,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
            instance.current_node_ids = [n for n in instance.current_node_ids if n != node.id]
            instance.current_node_ids.append(node.id)
            instance.set_node_state(node.id, "pending")
        
        elif node.type == "countersign":
            self._handle_countersign(workflow_schema, instance, node, result)
        
        elif node.type == "parallel":
            self._handle_parallel(workflow_schema, instance, node)
        
        elif node.type == "end":
            instance.set_node_state(node.id, "completed")
            instance.status = "completed"
            instance.completed_at = datetime.now()
            instance.current_node_ids = []
            instance.add_history("complete", node_id=node.id)
        
        else:
            instance.set_node_state(node.id, "completed")
            instance.current_node_ids = [n for n in instance.current_node_ids if n != node.id]
            
            next_nodes = workflow_schema.get_next_nodes(node.id, instance.context)
            for next_node in next_nodes:
                if next_node.id not in instance.completed_node_ids:
                    self._execute_node(workflow_schema, instance, next_node)
        
        self._save_instance(instance)
    
    def _handle_parallel(
        self, workflow_schema: WorkflowSchema, instance: WorkflowInstance, node: Node
    ) -> None:
        instance.set_node_state(node.id, "completed")
        instance.current_node_ids = [n for n in instance.current_node_ids if n != node.id]
        
        next_nodes = workflow_schema.get_next_nodes(node.id, instance.context)
        
        for next_node in next_nodes:
            if next_node.id not in instance.completed_node_ids:
                instance.current_node_ids.append(next_node.id)
                self._execute_node(workflow_schema, instance, next_node)
    
    def _handle_countersign(
        self, workflow_schema: WorkflowSchema, instance: WorkflowInstance, node: Node, result: Dict[str, Any]
    ) -> None:
        countersign_key = f"{instance.id}_{node.id}"
        assignees = result.get("assignees", [])
        
        self._countersign_states[countersign_key] = {
            "node_id": node.id,
            "assignees": assignees,
            "approvals": {},
            "mode": result.get("mode", CountersignMode.ALL),
            "percentage": result.get("percentage", 100),
            "status": "pending",
        }
        
        for assignee in assignees:
            self._countersign_states[countersign_key]["approvals"][assignee] = None
        
        task_key = f"{instance.id}_{node.id}"
        self._pending_tasks[task_key] = {
            "instance_id": instance.id,
            "node_id": node.id,
            "assignees": assignees,
            "is_countersign": True,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        instance.current_node_ids = [n for n in instance.current_node_ids if n != node.id]
        instance.current_node_ids.append(node.id)
        instance.set_node_state(node.id, "pending")
    
    def complete_task(
        self, workflow_schema: WorkflowSchema, instance: WorkflowInstance,
        node_id: str, approved: bool, comment: str = "", approver: str = "",
        form_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        node = workflow_schema.get_node(node_id)
        if not node:
            return False
        
        countersign_key = f"{instance.id}_{node_id}"
        task_key = countersign_key
        
        if countersign_key in self._countersign_states:
            return self._complete_countersign(
                workflow_schema, instance, node, approved, comment, approver, form_data
            )
        
        if form_data:
            instance.context.update(form_data)
        
        instance.add_history(
            "complete_task",
            node_id=node_id,
            node_name=node.name,
            approved=approved,
            comment=comment,
            approver=approver,
        )
        
        if not approved:
            instance.set_node_state(node_id, "rejected")
            instance.status = "rejected"
            instance.current_node_ids = []
            instance.add_history("reject", node_id=node_id)
            self._save_instance(instance)
            if task_key in self._pending_tasks:
                del self._pending_tasks[task_key]
            return True
        
        if task_key in self._pending_tasks:
            del self._pending_tasks[task_key]
        
        instance.set_node_state(node_id, "completed")
        instance.current_node_ids = [n for n in instance.current_node_ids if n != node_id]
        
        next_nodes = workflow_schema.get_next_nodes(node_id, instance.context)
        for next_node in next_nodes:
            if next_node.id not in instance.completed_node_ids:
                self._execute_node(workflow_schema, instance, next_node)
        
        self._save_instance(instance)
        return True
    
    def _complete_countersign(
        self, workflow_schema: WorkflowSchema, instance: WorkflowInstance, node: Node,
        approved: bool, comment: str = "", approver: str = "",
        form_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        countersign_key = f"{instance.id}_{node.id}"
        cs_state = self._countersign_states[countersign_key]
        
        if approver not in cs_state["approvals"]:
            return False
        
        cs_state["approvals"][approver] = {
            "approved": approved,
            "comment": comment,
            "time": datetime.now().isoformat(),
        }
        
        instance.add_history(
            "countersign_vote",
            node_id=node.id,
            approver=approver,
            approved=approved,
            comment=comment,
        )
        
        all_voted = all(v is not None for v in cs_state["approvals"].values())
        if not all_voted:
            self._save_instance(instance)
            return True
        
        approved_count = sum(1 for v in cs_state["approvals"].values() if v and v["approved"])
        total_count = len(cs_state["approvals"])
        
        passed = False
        if cs_state["mode"] == CountersignMode.ALL:
            passed = approved_count == total_count
        elif cs_state["mode"] == CountersignMode.ANY:
            passed = approved_count > 0
        elif cs_state["mode"] == CountersignMode.PERCENTAGE:
            passed = (approved_count / total_count * 100) >= cs_state["percentage"]
        
        if form_data:
            instance.context.update(form_data)
        
        task_key = f"{instance.id}_{node.id}"
        if task_key in self._pending_tasks:
            del self._pending_tasks[task_key]
        
        del self._countersign_states[countersign_key]
        
        if not passed:
            instance.set_node_state(node.id, "rejected")
            instance.status = "rejected"
            instance.current_node_ids = []
            instance.add_history("reject", node_id=node.id, reason="会签未通过")
            self._save_instance(instance)
            return True
        
        instance.set_node_state(node.id, "completed")
        instance.current_node_ids = [n for n in instance.current_node_ids if n != node.id]
        
        next_nodes = workflow_schema.get_next_nodes(node.id, instance.context)
        for next_node in next_nodes:
            if next_node.id not in instance.completed_node_ids:
                self._execute_node(workflow_schema, instance, next_node)
        
        self._save_instance(instance)
        return True
    
    def get_pending_tasks(self, assignee: Optional[str] = None) -> List[Dict[str, Any]]:
        tasks = []
        for task_key, task in self._pending_tasks.items():
            if assignee:
                if task.get("assignee") == assignee or assignee in task.get("assignees", []):
                    tasks.append(task)
            else:
                tasks.append(task)
        return tasks
    
    def get_workflow_tasks(self, instance_id: str) -> List[Dict[str, Any]]:
        tasks = []
        for task_key, task in self._pending_tasks.items():
            if task["instance_id"] == instance_id:
                tasks.append(task)
        return tasks
    
    def _save_instance(self, instance: WorkflowInstance) -> None:
        self.storage.update_workflow_instance(
            instance.id,
            status=instance.status,
            current_node_ids=instance.current_node_ids,
            context=instance.context,
            history=instance.history,
            completed_at=instance.completed_at,
        )
    
    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        try:
            return safe_eval(condition, context)
        except Exception:
            return False
