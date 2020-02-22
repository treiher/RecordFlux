from abc import ABC
from typing import List, Optional

from rflx.expression import Expr, Variable


class Declaration(ABC):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __repr__(self) -> str:
        args = "\n\t" + ",\n\t".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({args})".replace("\t", "\t    ")


class Argument(Declaration):
    def __init__(self, name: Variable, typ: Variable):
        self.__name = name
        self.__type = typ


class VariableDeclaration(Declaration):
    def __init__(self, typ: Variable, init: Optional[Expr] = None):
        self.__type = typ
        self.__init = init


class Subprogram(Declaration):
    def __init__(self, arguments: List[Argument], return_type: Variable):
        self.__arguments = arguments
        self.__return_type = return_type
