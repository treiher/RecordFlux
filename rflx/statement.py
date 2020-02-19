from abc import ABC

from rflx.expression import Expr, Variable


class Statement(ABC):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __repr__(self) -> str:
        args = "\n\t" + ",\n\t".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({args})".replace("\t", "\t    ")


class Assignment(Statement):
    def __init__(self, name: Variable, expression: Expr) -> None:
        self.__name = name
        self.__expression = expression

    def __str__(self) -> str:
        return f"{self.__name} := {self.__expression}"


class Erase(Statement):
    def __init__(self, name: Variable) -> None:
        self.__name = name

    def __str__(self) -> str:
        return f"{self.__name} := null"
