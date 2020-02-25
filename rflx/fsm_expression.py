from typing import Callable, Dict, List, Mapping

import z3

from rflx.expression import (
    Attribute,
    Declaration,
    Expr,
    Name,
    Not,
    Precedence,
    Relation,
    Variable,
    substitution,
)


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

    def __neg__(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping["Name", Expr] = None
    ) -> Expr:
        assert (func and not mapping) or (not func and mapping is not None)
        func = substitution(mapping or {}, func)
        expr = func(self)
        if isinstance(expr, Quantifier):
            return expr.__class__(
                self.__quantifier,
                self.__iterable.substituted(func),
                self.__predicate.substituted(func),
            )
        return expr

    def simplified(self) -> Expr:
        return Quantifier(
            self.__quantifier, self.__iterable.simplified(), self.__predicate.simplified()
        )

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        self.__iterable.validate(declarations)
        self.__predicate.validate(declarations)


class ForSome(Quantifier):
    symbol: str = "some"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError


class ForAll(Quantifier):
    symbol: str = "all"

    def __neg__(self) -> Expr:
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

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping["Name", Expr] = None
    ) -> Expr:
        assert (func and not mapping) or (not func and mapping is not None)
        func = substitution(mapping or {}, func)
        expr = func(self)
        if isinstance(expr, SubprogramCall):
            return expr.__class__(self.__name, [a.substituted(func) for a in self.__arguments])
        return expr

    def simplified(self) -> Expr:
        return SubprogramCall(self.__name, [a.simplified() for a in self.__arguments])

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        for a in self.__arguments:
            a.validate(declarations)


class Conversion(Expr):
    def __init__(self, name: Name, argument: Expr) -> None:
        self.__name = name
        self.__argument = argument

    def __str__(self) -> str:
        return f"{self.__name} ({self.__argument})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping["Name", Expr] = None
    ) -> Expr:
        assert (func and not mapping) or (not func and mapping is not None)
        func = substitution(mapping or {}, func)
        expr = func(self)
        if isinstance(expr, Conversion):
            return expr.__class__(self.__name, self.__argument.substituted(func))
        return expr

    def simplified(self) -> Expr:
        return Conversion(self.__name, self.__argument.simplified())

    @property
    def precedence(self) -> Precedence:
        raise NotImplementedError

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        self.__argument.validate(declarations)


class Field(Expr):
    def __init__(self, expression: Expr, field: str) -> None:
        self.__expression = expression
        self.__field = field

    def __str__(self) -> str:
        return f"{self.__expression}.{self.__field}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping["Name", Expr] = None
    ) -> Expr:
        assert (func and not mapping) or (not func and mapping is not None)
        func = substitution(mapping or {}, func)
        expr = func(self)
        if isinstance(expr, Field):
            return expr.__class__(self.__expression.substituted(func), self.__field)
        return expr

    def simplified(self) -> Expr:
        return Field(self.__expression.simplified(), self.__field)

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        self.__expression.validate(declarations)


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

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping["Name", Expr] = None
    ) -> Expr:
        assert (func and not mapping) or (not func and mapping is not None)
        func = substitution(mapping or {}, func)
        expr = func(self)
        if isinstance(expr, Comprehension):
            return expr.__class__(
                self.__iterator,
                self.__array.substituted(func),
                self.__selector.substituted(func),
                self.__condition.substituted(func),
            )
        return expr

    def simplified(self) -> Expr:
        return Comprehension(
            self.__iterator,
            self.__array.simplified(),
            self.__selector.simplified(),
            self.__condition.simplified(),
        )

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        self.__array.validate(declarations)
        self.__selector.validate(declarations)
        self.__condition.validate(declarations)


class MessageAggregate(Expr):
    def __init__(self, name: Name, data: Dict[str, Expr]) -> None:
        self.__name = name
        self.__data = data

    def __str__(self) -> str:
        data = ", ".join(["{k} => {v}".format(k=k, v=self.__data[k]) for k in self.__data])
        return f"{self.__name}'({data})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping["Name", Expr] = None
    ) -> Expr:
        assert (func and not mapping) or (not func and mapping is not None)
        func = substitution(mapping or {}, func)
        expr = func(self)
        if isinstance(expr, MessageAggregate):
            return expr.__class__(
                self.__name, {k: self.__data[k].substituted(func) for k in self.__data}
            )
        return expr

    def simplified(self) -> Expr:
        return MessageAggregate(self.__name, {k: self.__data[k].simplified() for k in self.__data})

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        for k in self.__data:
            self.__data[k].validate(declarations)


class Binding(Expr):
    def __init__(self, expr: Expr, data: Dict[str, Expr]) -> None:
        self.__expr = expr
        self.__data = data

    def __str__(self) -> str:
        data = ", ".join(["{k} = {v}".format(k=k, v=self.__data[k]) for k in self.__data])
        return f"{self.__expr} where {data}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping["Name", Expr] = None
    ) -> Expr:
        assert (func and not mapping) or (not func and mapping is not None)
        func = substitution(mapping or {}, func)
        expr = func(self)
        if isinstance(expr, Binding):
            return expr.__class__(
                self.__expr.substituted(func),
                {n: e.substituted(func) for n, e in self.__data.items()},
            )
        return expr

    def simplified(self) -> Expr:
        def subst(expression: Expr) -> Expr:
            if isinstance(expression, Variable) and expression.name in self.__data:
                return self.__data[expression.name]
            return expression

        return self.__expr.substituted(subst).simplified()

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

    def simplified(self) -> Expr:
        return self

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError
