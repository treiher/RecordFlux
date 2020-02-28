from typing import Callable, Dict, List, Mapping

import z3

from rflx.expression import (
    Attribute,
    Channel,
    Declaration,
    Expr,
    Name,
    Not,
    Precedence,
    Relation,
    ValidationError,
    Variable,
    VariableDeclaration,
    substitution,
)


class FSMAttribute(Attribute):
    def variables(self, proof: bool = False) -> List["Variable"]:
        return self.prefix.variables(proof)


class Valid(FSMAttribute):
    pass


class Present(FSMAttribute):
    pass


class Head(FSMAttribute):
    pass


class Opaque(Attribute):
    def simplified(self) -> Expr:
        if isinstance(self.prefix, Expr):
            return Opaque(self.prefix.simplified())
        return self


class Quantifier(Expr):
    def __init__(self, quantifier: Variable, iterable: Expr, predicate: Expr) -> None:
        self.__quantifier = quantifier
        self.__iterable = iterable
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
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping[Name, Expr] = None
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
        quantifier: Mapping[str, Declaration] = {
            self.__quantifier.name: VariableDeclaration()
        } if isinstance(self.__quantifier.name, str) else {}
        self.__iterable.validate({**declarations, **quantifier})
        self.__predicate.validate({**declarations, **quantifier})

    def variables(self, proof: bool = False) -> List["Variable"]:
        return [
            v
            for v in self.__predicate.variables(proof) + self.__iterable.variables()
            if v != self.__quantifier
        ]


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
    def __init__(self, name: Variable, arguments: List[Expr]) -> None:
        self.__name = name
        self.__arguments = arguments

    def __str__(self) -> str:
        arguments = ", ".join([f"{a}" for a in self.__arguments])
        return f"{self.__name} ({arguments})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping[Name, Expr] = None
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

    def __valid_list_operation(self) -> bool:
        if isinstance(self.__name.name, str) and self.__name.name.upper() in ["APPEND", "EXTEND"]:
            return True
        return False

    def __valid_channel_operation(self, declarations: Mapping[str, Declaration]) -> bool:
        if isinstance(self.__name.name, str) and self.__name.name.upper() not in [
            "READ",
            "WRITE",
            "CALL",
            "DATA_AVAILABLE",
        ]:
            return False

        args = self.__arguments
        if len(args) < 1:
            raise ValidationError(f"no channel argument in call to {self.__name}")
        if not isinstance(args[0], Variable) or not isinstance(args[0].name, str):
            raise ValidationError(f"invalid channel type in call to {self.__name}")
        if args[0].name not in declarations:
            raise ValidationError(f"undeclared channel in call to {self.__name}")
        channel_name = args[0].name
        channel = declarations[channel_name]
        if not isinstance(channel, Channel):
            raise ValidationError(f"invalid channel type in call to {self.__name}")
        if self.__name.name in ["Write", "Call"] and not channel.writable:
            raise ValidationError(f"channel {channel_name} not writable in call to {self.__name}")
        if self.__name.name in ["Call", "Read", "Data_Available"] and not channel.readable:
            raise ValidationError(f"channel {channel_name} not readable in call to {self.__name}")
        channel.reference()
        return True

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        if not self.__valid_channel_operation(declarations) and not self.__valid_list_operation():
            if not isinstance(self.__name.name, str) or self.__name.name not in declarations:
                raise ValidationError(f"undeclared subprogram {self.__name} called")
            declarations[self.__name.name].reference()
        for index, a in enumerate(self.__arguments):
            try:
                a.validate(declarations)
            except ValidationError as e:
                raise ValidationError(f"{e} (parameter {index}) in call to {self.__name}")

    def variables(self, proof: bool = False) -> List["Variable"]:
        result = []
        for t in self.__arguments:
            result.extend(t.variables(proof))
        return result


class Conversion(Expr):
    def __init__(self, name: Variable, argument: Expr) -> None:
        self.__name = name
        self.__argument = argument

    def __str__(self) -> str:
        return f"{self.__name} ({self.__argument})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping[Name, Expr] = None
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

    def variables(self, proof: bool = False) -> List["Variable"]:
        return self.__argument.variables(proof)


class Field(Expr):
    def __init__(self, expression: Expr, field: str) -> None:
        self.__expression = expression
        self.__field = field

    def __str__(self) -> str:
        return f"{self.__expression}.{self.__field}"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping[Name, Expr] = None
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

    def variables(self, proof: bool = False) -> List["Variable"]:
        return self.__expression.variables(proof)


class Comprehension(Expr):
    def __init__(self, iterator: Variable, array: Expr, selector: Expr, condition: Expr) -> None:
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
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping[Name, Expr] = None
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
        quantifier: Mapping[str, Declaration] = {
            self.__iterator.name: VariableDeclaration()
        } if isinstance(self.__iterator.name, str) else {}
        self.__array.validate({**declarations, **quantifier})
        self.__selector.validate({**declarations, **quantifier})
        self.__condition.validate({**declarations, **quantifier})

    def variables(self, proof: bool = False) -> List["Variable"]:
        return [
            v
            for v in self.__array.variables(proof)
            + self.__selector.variables()
            + self.__condition.variables()
            if v != self.__iterator
        ]


class MessageAggregate(Expr):
    def __init__(self, name: Variable, data: Dict[str, Expr]) -> None:
        self.__name = name
        self.__data = data

    def __str__(self) -> str:
        data = ", ".join(["{k} => {v}".format(k=k, v=self.__data[k]) for k in self.__data])
        return f"{self.__name}'({data})"

    def __neg__(self) -> Expr:
        raise NotImplementedError

    def substituted(
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping[Name, Expr] = None
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

    def variables(self, proof: bool = False) -> List["Variable"]:
        result = []
        for _, v in self.__data.items():
            result.extend(v.variables(proof))
        return result


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
        self, func: Callable[[Expr], Expr] = None, mapping: Mapping[Name, Expr] = None
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
                return self.__data[expression.name].simplified()
            return expression

        return self.__expr.substituted(subst).simplified()

    @property
    def precedence(self) -> Precedence:
        return Precedence.undefined

    def z3expr(self) -> z3.ExprRef:
        raise NotImplementedError

    def variables(self, proof: bool = False) -> List["Variable"]:
        return self.simplified().variables(proof)


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

    def validate(self, declarations: Mapping[str, Declaration]) -> None:
        pass
