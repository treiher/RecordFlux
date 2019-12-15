from pyparsing import Keyword

from rflx.expression import FALSE, TRUE, Equal, Variable
from rflx.parser import Parser


class FSM_Parser:
    @classmethod
    def expr(cls):
        boolean = Parser.boolean_literal().setParseAction(
            lambda t: TRUE if t[0] == "True" else FALSE
        )
        identifier = Parser.qualified_identifier().setParseAction(lambda t: Variable("".join(t)))
        return boolean | identifier

    @classmethod
    def logical_equation(cls):
        result = cls.expr() + Keyword("=") + cls.expr()
        return result.setParseAction(lambda t: Equal(t[0], t[2]))

    @classmethod
    def condition(cls):
        return cls.logical_equation()
