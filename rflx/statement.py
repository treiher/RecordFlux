from abc import ABC

from rflx.expression import Expr, Variable


class Statement(ABC):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented


class Assignment(Statement):
    def __init__(self, name: Variable, expression: Expr) -> None:
        self.__name = name
        self.__expression = expression

    def __str__(self) -> str:
        return f"{self.__name} := {self.__expression}"
