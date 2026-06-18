import ast
import operator
from typing import Any, Dict, List, Optional


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Not: operator.not_,
    ast.Invert: operator.invert,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: lambda a, b: a is b,
    ast.IsNot: lambda a, b: a is not b,
}

SAFE_FUNCTIONS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "sorted": sorted,
    "reversed": reversed,
    "range": range,
    "any": any,
    "all": all,
}


class ExpressionEvaluator:
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.context = context or {}
        self._max_depth = 10
        self._current_depth = 0

    def evaluate(self, expression: str, context: Optional[Dict[str, Any]] = None) -> Any:
        if context is not None:
            self.context = context
        try:
            tree = ast.parse(expression, mode="eval")
            return self._eval_node(tree.body)
        except Exception as e:
            raise ValueError(f"表达式求值失败: {str(e)}")

    def _eval_node(self, node: ast.AST) -> Any:
        self._current_depth += 1
        if self._current_depth > self._max_depth:
            raise ValueError("表达式嵌套过深")

        try:
            result = self._dispatch(node)
            return result
        finally:
            self._current_depth -= 1

    def _dispatch(self, node: ast.AST) -> Any:
        node_type = type(node)

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in self.context:
                return self.context[node.id]
            if node.id in SAFE_FUNCTIONS:
                return SAFE_FUNCTIONS[node.id]
            raise NameError(f"未定义的变量或函数: {node.id}")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                left = self._eval_node(node.left)
                right = self._eval_node(node.right)
                return SAFE_OPERATORS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                operand = self._eval_node(node.operand)
                return SAFE_OPERATORS[op_type](operand)

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type in SAFE_OPERATORS:
                    right = self._eval_node(comparator)
                    if not SAFE_OPERATORS[op_type](left, right):
                        result = False
                        break
                    left = right
            return result

        if isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type == ast.And:
                return all(self._eval_node(v) for v in node.values)
            if op_type == ast.Or:
                return any(self._eval_node(v) for v in node.values)

        if isinstance(node, ast.IfExp):
            condition = self._eval_node(node.test)
            if condition:
                return self._eval_node(node.body)
            return self._eval_node(node.orelse)

        if isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            args = [self._eval_node(a) for a in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
            return func(*args, **kwargs)

        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            elements = [self._eval_node(e) for e in node.elts]
            if isinstance(node, ast.List):
                return elements
            if isinstance(node, ast.Tuple):
                return tuple(elements)
            return set(elements)

        if isinstance(node, ast.Dict):
            keys = [self._eval_node(k) if k is not None else None for k in node.keys]
            values = [self._eval_node(v) for v in node.values]
            return dict(zip(keys, values))

        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            if isinstance(node.slice, ast.Slice):
                lower = self._eval_node(node.slice.lower) if node.slice.lower else None
                upper = self._eval_node(node.slice.upper) if node.slice.upper else None
                step = self._eval_node(node.slice.step) if node.slice.step else None
                return value[lower:upper:step]
            else:
                index = self._eval_node(node.slice)
                return value[index]

        if isinstance(node, ast.Attribute):
            value = self._eval_node(node.value)
            attr_name = node.attr
            if hasattr(value, attr_name):
                return getattr(value, attr_name)
            raise AttributeError(f"'{type(value).__name__}' 对象没有属性 '{attr_name}'")

        raise ValueError(f"不支持的表达式类型: {type(node).__name__}")


def safe_eval(expression: str, context: Optional[Dict[str, Any]] = None) -> Any:
    evaluator = ExpressionEvaluator(context or {})
    return evaluator.evaluate(expression)
