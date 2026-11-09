"""Declarative JSON Expression Evaluator."""
from typing import Any, Dict, List

class DeclarativeExpressionEvaluator:
    """Evaluates declarative JSON logic trees with dot-path variable resolution."""

    @classmethod
    def resolve_var(cls, path: str, context: Dict[str, Any], default: Any = None) -> Any:
        parts = path.split(".")
        curr = context
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            elif hasattr(curr, p):
                curr = getattr(curr, p)
            else:
                return default
        return curr

    @classmethod
    def evaluate(cls, expr: Any, context: Dict[str, Any]) -> Any:
        if not isinstance(expr, dict):
            return expr

        for op, args in expr.items():
            if op == "var":
                path = args if isinstance(args, str) else args.get("path")
                default = None if isinstance(args, str) else args.get("default")
                return cls.resolve_var(path, context, default)
            elif op == "==":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] == vals[1]
            elif op == "!=":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] != vals[1]
            elif op == ">":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] > vals[1]
            elif op == ">=":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] >= vals[1]
            elif op == "<":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] < vals[1]
            elif op == "<=":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] <= vals[1]
            elif op == "in":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] in vals[1]
            elif op == "and":
                return all(bool(cls.evaluate(a, context)) for a in args)
            elif op == "or":
                return any(bool(cls.evaluate(a, context)) for a in args)
            elif op == "not":
                return not bool(cls.evaluate(args, context))
            elif op == "+":
                vals = [cls.evaluate(a, context) for a in args]
                return sum(vals)
            elif op == "-":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] - vals[1]
            elif op == "*":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] * vals[1]
            elif op == "/":
                vals = [cls.evaluate(a, context) for a in args]
                return vals[0] / max(0.0001, vals[1])
            elif op == "if":
                cond = cls.evaluate(args[0], context)
                return cls.evaluate(args[1], context) if cond else cls.evaluate(args[2], context)

        return expr
