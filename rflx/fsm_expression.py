from typing import Dict, List

import z3

from rflx.expression import Attribute, Expr, Not, Precedence, Relation, Variable


class Valid(Attribute):
    pass


class Present(Attribute):
    pass


class Head(Attribute):
    pass


class Quantifier(Expr):
    def __init__(self, quantifier: Variable, iteratable: Expr, predicate: Expr) -> None:
        self.__quantifier = quantifier
        self.__iterable = iteratable
        self.__predicate = predicate
        self.symbol: str = ""

    def __repr__(self) -> str:
        return f"for {self.symbol} {self.__quantifier} in {self.__iterable} => {self.__predicate}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def simplified(self) -> Expr:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class ForSome(Quantifier):
    symbol: str = "some"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def simplified(self) -> Expr:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class ForAll(Quantifier):
    symbol: str = "all"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def simplified(self) -> Expr:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Contains(Relation):
    @property
    def symbol(self) -> str:
        return " in "

    def __neg__(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.set_operator

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class NotContains(Relation):
    @property
    def symbol(self) -> str:
        return " not in "

    def __neg__(self) -> Expr:
        return Not(Contains(self.left, self.right))

    @property
    def precedence(self) -> Precedence:
        return Precedence.set_operator

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class FunctionCall(Expr):
    def __init__(self, name: Variable, arguments: List[Expr]) -> None:
        self.__name = name
        self.__arguments = arguments

    def __repr__(self) -> str:
        arguments = ", ".join(["{a}" for a in self.__arguments])
        return f"{self.__name} ({arguments})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Field(Expr):
    def __init__(self, expression: Expr, field: str) -> None:
        self.__expression = expression
        self.__field = field

    def __repr__(self) -> str:
        return f"{self.__expression}.{self.__field}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Comprehension(Expr):
    def __init__(self, iterator: Variable, array: Expr, selector: Expr, condition: Expr) -> None:
        self.__iterator = iterator
        self.__array = array
        self.__selector = selector
        self.__condition = condition

    def __repr__(self) -> str:
        return (
            f"[for {self.__iterator} in {self.__array} => "
            f"{self.__selector} when {self.__condition}]"
        )

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class MessageAggregate(Expr):
    def __init__(self, name: Variable, data: Dict[str, Expr]) -> None:
        self.__name = name
        self.__data = data

    def __repr__(self) -> str:
        data = ", ".join(["{k} => {v}".format(k=k, v=self.__data[k]) for k in self.__data])
        return f"{self.__name}'({data})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Binding(Expr):
    def __init__(self, expr: Expr, data: Dict[str, Expr]) -> None:
        self.__expr = expr
        self.__data = data

    def __repr__(self) -> str:
        data = ", ".join(["{k} = {v}".format(k=k, v=self.__data[k]) for k in self.__data])
        return f"{self.__expr} where {data}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError
