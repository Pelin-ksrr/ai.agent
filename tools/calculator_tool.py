"""
Calculator Tool — safe math expression evaluator.

Uses Python's ``ast`` module to parse and evaluate arithmetic expressions
without calling ``eval()``, eliminating arbitrary-code-execution risk.

Supported operations: + - * / ** %  and parentheses.
"""

import ast
import operator
from typing import Any

from tools.base_tool import BaseTool

# Whitelist of safe AST node types → Python operators
_SAFE_OPERATORS: dict[type, Any] = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.Mod:  operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class CalculatorTool(BaseTool):
    """Evaluates arithmetic expressions safely via AST parsing."""

    # ------------------------------------------------------------------ #
    # BaseTool interface                                                    #
    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluates a mathematical expression and returns the numeric result."

    def execute(self, expression: str) -> str:
        try:
            result = self._safe_eval(expression)
            # Return an integer string when the result is whole, e.g. 4.0 → "4"
            if isinstance(result, float) and result.is_integer():
                return str(int(result))
            return str(round(result, 10))
        except ZeroDivisionError:
            return "Error: Division by zero."
        except ValueError as exc:
            return f"Error: {exc}"
        except Exception as exc:
            return f"Error evaluating '{expression}': {exc}"

    def get_declaration(self) -> dict:
        return {
            "name": self.name,
            "description": (
                "Evaluates a mathematical expression and returns the numeric result. "
                "Supports +, -, *, /, ** (exponentiation), % (modulo), and parentheses."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "A mathematical expression to evaluate. "
                            "Examples: '2 + 3 * 4', '(100 / 4) ** 2', '17 % 5'."
                        ),
                    }
                },
                "required": ["expression"],
            },
        }

    # ------------------------------------------------------------------ #
    # Private helpers                                                       #
    # ------------------------------------------------------------------ #

    def _safe_eval(self, expr: str) -> float:
        """Parse and evaluate *expr* through AST — no ``eval()`` call."""
        try:
            tree = ast.parse(expr.strip(), mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid expression syntax: {exc}") from exc
        return self._eval_node(tree.body)

    def _eval_node(self, node: ast.expr) -> float:  # type: ignore[override]
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return _SAFE_OPERATORS[op_type](left, right)
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return _SAFE_OPERATORS[op_type](self._eval_node(node.operand))
        raise ValueError(f"Unsupported expression element: {ast.dump(node)}")
