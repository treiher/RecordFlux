from abc import ABC
from typing import Mapping

from rflx.expression import Declaration, Expr, ValidationError, Variable


class Statement(ABC):
    def __init__(self, name: Variable) -> None:
        self.__name = name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __repr__(self) -> str:
        args = "\n\t" + ",\n\t".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({args})".replace("\t", "\t    ")

    @property
    def name(self) -> str:
        if isinstance(self.__name.name, str):
            return self.__name.name
        raise TypeError

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        raise NotImplementedError


class Assignment(Statement):
    def __init__(self, name: Variable, expression: Expr) -> None:
        super().__init__(name)
        self.__expression = expression

    def __str__(self) -> str:
        return f"{self.name} := {self.__expression}"

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        if self.name not in declarations:
            raise ValidationError(f"Assignment to undeclared variable {self.name}")
        try:
            self.__expression.simplified().validate(declarations)
        except ValidationError as e:
            raise ValidationError(f"{e} in assignment")
        declarations[self.name].reference()

    @property
    def expression(self) -> Expr:
        return self.__expression


class Erase(Statement):
    def __str__(self) -> str:
        return f"{self.name} := null"

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        if self.name not in declarations:
            raise ValidationError(f"Erasure of undeclared variable {self.name}")


class Reset(Statement):
    def __str__(self) -> str:
        return f"{self.name}'Reset"

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        if self.name not in declarations:
            raise ValidationError(f"Reset of undeclared list {self.name}")
