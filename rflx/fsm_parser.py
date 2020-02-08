from typing import List

from pyparsing import (
    Forward,
    Keyword,
    Literal,
    StringEnd,
    Suppress,
    Token,
    infixNotation,
    oneOf,
    opAssoc,
)

from rflx.expression import FALSE, TRUE, And, Equal, Expr, NotEqual, Or, Variable
from rflx.fsm_expression import (
    Contains,
    Convert,
    Field,
    ForAll,
    ForSome,
    NotContains,
    Present,
    Valid,
)
from rflx.parser import Parser


class FSMParser:
    @classmethod
    def __parse_equation(cls, tokens: List[List[Expr]]) -> Expr:
        t = tokens[0]
        return Equal(t[0], t[2])

    @classmethod
    def __parse_inequation(cls, tokens: List[List[Expr]]) -> Expr:
        t = tokens[0]
        return NotEqual(t[0], t[2])

    @classmethod
    def __parse_conj(cls, tokens: List[List[Expr]]) -> Expr:
        t = tokens[0]
        return And(*t)

    @classmethod
    def __parse_disj(cls, tokens: List[List[Expr]]) -> Expr:
        t = tokens[0]
        return Or(*t)

    @classmethod
    def __parse_in(cls, tokens: List[List[Expr]]) -> Expr:
        t = tokens[0]
        return Contains(t[0], t[2])

    @classmethod
    def __parse_notin(cls, tokens: List[List[Expr]]) -> Expr:
        t = tokens[0]
        return NotContains(t[0], t[2])

    @classmethod
    def __parse_quantifier(cls, tokens: List[Expr]) -> Expr:
        if not isinstance(tokens[1], Variable):
            raise TypeError("quantifier not of type Variable")
        if tokens[0] == "all":
            return ForAll(tokens[1], tokens[2], tokens[3])
        return ForSome(tokens[1], tokens[2], tokens[3])

    @classmethod
    def __parse_conversion(cls, tokens: List[Expr]) -> Expr:
        if not isinstance(tokens[1], Variable):
            raise TypeError("target not of type Variable")
        if not isinstance(tokens[0], Variable):
            raise TypeError("source not of type Variable")
        return Convert(tokens[1], tokens[0])

    @classmethod
    def expression(cls) -> Token:

        boolean_literal = Parser.boolean_literal()
        boolean_literal.setParseAction(lambda t: TRUE if t[0] == "True" else FALSE)

        identifier = Parser.qualified_identifier()
        identifier.setParseAction(lambda t: Variable(".".join(t)))

        attribute = identifier() + Literal("'") - (Keyword("Valid") | Keyword("Present"))
        attribute.setParseAction(lambda t: Valid(t[0]) if t[2] == "Valid" else Present(t[0]))

        expression = Forward()

        quantifier = (
            Keyword("for").suppress()
            - oneOf(["all", "some"])
            + identifier
            - Keyword("in").suppress()
            + identifier
            - Keyword("=>").suppress()
            + expression
        )
        quantifier.setParseAction(cls.__parse_quantifier)

        lpar, rpar = map(Suppress, "()")
        conversion = identifier + lpar + identifier + rpar
        conversion.setParseAction(cls.__parse_conversion)

        field = conversion + Literal(".").suppress() - Parser.identifier()
        field.setParseAction(lambda t: Field(t[0], t[1]))

        atom = (
            Parser.numeric_literal()
            | boolean_literal
            | quantifier
            | field
            | conversion
            | attribute
            | identifier
        )

        expression <<= infixNotation(
            atom,
            [
                (Keyword("="), 2, opAssoc.LEFT, cls.__parse_equation),
                (Keyword("/="), 2, opAssoc.LEFT, cls.__parse_inequation),
                (Keyword("in"), 2, opAssoc.LEFT, cls.__parse_in),
                (Keyword("not in"), 2, opAssoc.LEFT, cls.__parse_notin),
                (Keyword("and").suppress(), 2, opAssoc.LEFT, cls.__parse_conj),
                (Keyword("or").suppress(), 2, opAssoc.LEFT, cls.__parse_disj),
            ],
        )

        expression.enablePackrat()
        return expression

    @classmethod
    def condition(cls) -> Token:
        return cls.expression() + StringEnd()