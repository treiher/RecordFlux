from typing import Dict, List, Mapping

import z3

from rflx.expression import Attribute, Expr, Name, Not, Precedence, Relation


class Valid(Attribute):
    pass


class Present(Attribute):
    pass


class Head(Attribute):
    pass


class Opaque(Attribute):
    pass


class Quantifier(Expr):
    def __init__(self, quantifier: Name, iteratable: Expr, predicate: Expr) -> None:
        self.__quantifier = quantifier
        self.__iterable = iteratable
        self.__predicate = predicate
        self.symbol: str = ""

    def __str__(self) -> str:
        return f"for {self.symbol} {self.__quantifier} in {self.__iterable} => {self.__predicate}"

    def __neg__(self) -> "Expr":
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        return Quantifier(
            self.__quantifier, self.__iterable.simplified(facts), self.__predicate.simplified(facts)
        )

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class ForSome(Quantifier):
    symbol: str = "some"

    def __neg__(self) -> "Expr":
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class ForAll(Quantifier):
    symbol: str = "all"

    def __neg__(self) -> "Expr":
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
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


class SubprogramCall(Expr):
    def __init__(self, name: Name, arguments: List[Expr]) -> None:
        self.__name = name
        self.__arguments = arguments

    def __str__(self) -> str:
        arguments = ", ".join([f"{a}" for a in self.__arguments])
        return f"{self.__name} ({arguments})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        return SubprogramCall(self.__name, [a.simplified(facts) for a in self.__arguments])

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Conversion(Expr):
    def __init__(self, name: Name, argument: Expr) -> None:
        self.__name = name
        self.__argument = argument

    def __str__(self) -> str:
        return f"{self.__name} ({self.__argument})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        return Conversion(self.__name, self.__argument.simplified(facts))

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Field(Expr):
    def __init__(self, expression: Expr, field: str) -> None:
        self.__expression = expression
        self.__field = field

    def __str__(self) -> str:
        return f"{self.__expression}.{self.__field}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        return Field(self.__expression.simplified(facts), self.__field)

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Comprehension(Expr):
    def __init__(self, iterator: Name, array: Expr, selector: Expr, condition: Expr) -> None:
        self.__iterator = iterator
        self.__array = array
        self.__selector = selector
        self.__condition = condition

    def __str__(self) -> str:
        return (
            f"[for {self.__iterator} in {self.__array} => "
            f"{self.__selector} when {self.__condition}]"
        )

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        return Comprehension(
            self.__iterator,
            self.__array.simplified(facts),
            self.__selector.simplified(facts),
            self.__condition.simplified(facts),
        )

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class MessageAggregate(Expr):
    def __init__(self, name: Name, data: Dict[str, Expr]) -> None:
        self.__name = name
        self.__data = data

    def __str__(self) -> str:
        data = ", ".join(["{k} => {v}".format(k=k, v=self.__data[k]) for k in self.__data])
        return f"{self.__name}'({data})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        return MessageAggregate(
            self.__name, {k: self.__data[k].simplified(facts) for k in self.__data}
        )

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class Binding(Expr):
    def __init__(self, expr: Expr, data: Dict[str, Expr]) -> None:
        self.__expr = expr
        self.__data = data

    def __str__(self) -> str:
        data = ", ".join(["{k} = {v}".format(k=k, v=self.__data[k]) for k in self.__data])
        return f"{self.__expr} where {data}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        simplified_data = {Name(k): self.__data[k].simplified() for k in self.__data}
        if facts:
            simplified_data.update(facts)
        return self.__expr.simplified(simplified_data)

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class String(Expr):
    def __init__(self, data: str) -> None:
        self.__data = data

    def __str__(self) -> str:
        return f'"{self.__data}"'

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def simplified(self, facts: Mapping[Name, Expr] = None) -> Expr:
        return self

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError
