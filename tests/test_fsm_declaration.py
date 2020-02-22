import unittest

from pyparsing import ParseException

from rflx.expression import FALSE, Variable
from rflx.fsm_declaration import Argument, Renames, Subprogram, VariableDeclaration
from rflx.fsm_parser import FSMParser


class TestFSM(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_simple_function_declaration(self) -> None:
        result = FSMParser.declaration().parseString(
            "Foo (Arg1 : Arg1_Type; Arg2 : Arg2_Type) return Foo_Type"
        )[0]
        expected = (
            "Foo",
            Subprogram(
                [
                    Argument(Variable("Arg1"), Variable("Arg1_Type")),
                    Argument(Variable("Arg2"), Variable("Arg2_Type")),
                ],
                Variable("Foo_Type"),
            ),
        )
        self.assertEqual(result, expected)

    def test_invalid_function_name(self) -> None:
        with self.assertRaises(ParseException):
            # pylint: disable=expression-not-assigned
            FSMParser.declaration().parseString(
                "Foo.Bar (Arg1 : Arg1_Type; Arg2 : Arg2_Type) return Foo_Type"
            )[0]

    def test_invalid_parameter_name(self) -> None:
        with self.assertRaises(ParseException):
            # pylint: disable=expression-not-assigned
            FSMParser.declaration().parseString(
                "Foo (Arg1 : Arg1_Type; Arg2.Invalid : Arg2_Type) return Foo_Type"
            )[0]

    def test_parameterless_function_declaration(self) -> None:
        result = FSMParser.declaration().parseString("Foo return Foo_Type")[0]
        expected = ("Foo", Subprogram([], Variable("Foo_Type")))
        self.assertEqual(result, expected)

    def test_simple_variable_declaration(self) -> None:
        result = FSMParser.declaration().parseString(
            "Certificate_Authorities : TLS_Handshake.Certificate_Authorities"
        )[0]
        expected = (
            "Certificate_Authorities",
            VariableDeclaration(Variable("TLS_Handshake.Certificate_Authorities")),
        )
        self.assertEqual(result, expected)

    def test_variable_declaration_with_initialization(self) -> None:
        result = FSMParser.declaration().parseString(
            "Certificate_Authorities_Received : Boolean := False"
        )[0]
        expected = (
            "Certificate_Authorities_Received",
            VariableDeclaration(Variable("Boolean"), FALSE),
        )
        self.assertEqual(result, expected)

    def test_renames(self) -> None:
        result = FSMParser.declaration().parseString(
            "Certificate_Message : TLS_Handshake.Certificate renames CCR_Handshake_Message.Payload"
        )[0]
        expected = (
            "Certificate_Message",
            Renames(
                Variable("TLS_Handshake.Certificate"), Variable("CCR_Handshake_Message.Payload")
            ),
        )
        self.assertEqual(result, expected, msg=f"\n\n{result}\n !=\n{expected}")
