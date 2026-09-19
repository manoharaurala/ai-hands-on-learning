"""
DeskBuddy Tools - a tiny microservice exposing two tools:
  POST /calculator  -> evaluates a math expression
  GET  /datetime    -> returns the current date & time

Nothing AI about this file. It's a plain worker department.
The agent (a separate container) calls these over the private Docker network.
"""
import ast
import datetime
import operator

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="DeskBuddy Tools")


class Calc(BaseModel):
    expression: str


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def evaluate_expression(expression: str) -> int | float:
    tree = ast.parse(expression, mode="eval")

    def evaluate(node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left = evaluate(node.left)
            right = evaluate(node.right)
            return OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("Only arithmetic expressions are supported")

    return evaluate(tree.body)


@app.get("/")
def health():
    return {"status": "DeskBuddy Tools is live"}


@app.post("/calculator")
def calculator(c: Calc):
    """Evaluate a math expression like '23*47' or '(100-8)/4'."""
    try:
        result = evaluate_expression(c.expression)
        return {"result": result}
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as error:
        return {"error": str(error)}


@app.get("/datetime")
def now():
    """Return the current date and time in ISO format."""
    return {"now": datetime.datetime.now().isoformat()}
