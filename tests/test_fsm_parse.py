import unittest

from rflx.expression import FALSE, TRUE, And, Equal, NotEqual, Number, Or, Variable
from rflx.fsm_expression import Contains, Convert, Field, ForAll, ForSome, NotContains, Valid
from rflx.fsm_parser import FSMParser


class TestFSM(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_simple_equation(self) -> None:
        result = FSMParser.condition().parseString("Foo.Bar = abc")[0]
        self.assertEqual(result, Equal(Variable("Foo.Bar"), Variable("abc")))

    def test_simple_inequation(self) -> None:
        result = FSMParser.condition().parseString("Foo.Bar /= abc")[0]
        self.assertEqual(result, NotEqual(Variable("Foo.Bar"), Variable("abc")))

    def test_valid(self) -> None:
        result = FSMParser.condition().parseString("Something'Valid")[0]
        self.assertEqual(result, Valid(Variable("Something")))

    def test_conjunction_valid(self) -> None:
        result = FSMParser.condition().parseString("Foo'Valid and Bar'Valid")[0]
        self.assertEqual(result, And(Valid(Variable("Foo")), Valid(Variable("Bar"))))

    def test_conjunction(self) -> None:
        result = FSMParser.condition().parseString("Foo = Bar and Bar /= Baz")[0]
        self.assertEqual(
            result,
            And(
                Equal(Variable("Foo"), Variable("Bar")), NotEqual(Variable("Bar"), Variable("Baz"))
            ),
        )

    def test_conjunction_multi(self) -> None:
        result = FSMParser.condition().parseString("Foo = Bar and Bar /= Baz and Baz = Foo")[0]
        expected = And(
            Equal(Variable("Foo"), Variable("Bar")),
            NotEqual(Variable("Bar"), Variable("Baz")),
            Equal(Variable("Baz"), Variable("Foo")),
        )
        self.assertEqual(result, expected)

    def test_disjunction(self) -> None:
        result = FSMParser.condition().parseString("Foo = Bar or Bar /= Baz")[0]
        self.assertEqual(
            result,
            Or(Equal(Variable("Foo"), Variable("Bar")), NotEqual(Variable("Bar"), Variable("Baz"))),
        )

    def test_disjunction_multi(self) -> None:
        result = FSMParser.condition().parseString(
            "Foo = Bar or Bar /= Baz " "or Baz'Valid = False"
        )[0]
        self.assertEqual(
            result,
            Or(
                Equal(Variable("Foo"), Variable("Bar")),
                NotEqual(Variable("Bar"), Variable("Baz")),
                Equal(Valid(Variable("Baz")), FALSE),
            ),
        )

    def test_in_operator(self) -> None:
        result = FSMParser.condition().parseString("Foo in Bar")[0]
        self.assertEqual(result, Contains(Variable("Foo"), Variable("Bar")))

    def test_not_in_operator(self) -> None:
        result = FSMParser.condition().parseString("Foo not in Bar")[0]
        self.assertEqual(result, NotContains(Variable("Foo"), Variable("Bar")))

    def test_parenthesized_expression(self) -> None:
        result = FSMParser.condition().parseString("Foo = True and (Bar = False or Baz = False)")[0]
        self.assertEqual(
            result,
            And(
                Equal(Variable("Foo"), TRUE),
                Or(Equal(Variable("Bar"), FALSE), Equal(Variable("Baz"), FALSE)),
            ),
        )

    def test_parenthesized_expression2(self) -> None:
        result = FSMParser.condition().parseString("Foo'Valid and (Bar'Valid or Baz'Valid)")[0]
        self.assertEqual(
            result, And(Valid(Variable("Foo")), Or(Valid(Variable("Bar")), Valid(Variable("Baz"))))
        )

    def test_numeric_constant_expression(self) -> None:
        result = FSMParser.condition().parseString("Keystore_Message.Length = 0")[0]
        self.assertEqual(result, Equal(Variable("Keystore_Message.Length"), Number(0)))

    def test_complex_expression(self) -> None:
        expr = (
            "Keystore_Message'Valid = False "
            "or Keystore_Message.Tag /= KEYSTORE_RESPONSE "
            "or Keystore_Message.Request /= KEYSTORE_REQUEST_PSK_IDENTITIES "
            "or (Keystore_Message.Length = 0 "
            "    and TLS_Handshake.PSK_DHE_KE not in Configuration.PSK_Key_Exchange_Modes)"
        )
        result = FSMParser.condition().parseString(expr)[0]
        expected = Or(
            Equal(Valid(Variable("Keystore_Message")), FALSE),
            NotEqual(Variable("Keystore_Message.Tag"), Variable("KEYSTORE_RESPONSE")),
            NotEqual(
                Variable("Keystore_Message.Request"), Variable("KEYSTORE_REQUEST_PSK_IDENTITIES")
            ),
            And(
                Equal(Variable("Keystore_Message.Length"), Number(0)),
                NotContains(
                    Variable("TLS_Handshake.PSK_DHE_KE"),
                    Variable("Configuration.PSK_Key_Exchange_Modes"),
                ),
            ),
        )
        self.assertEqual(result, expected)

    def test_existential_quantification(self) -> None:
        result = FSMParser.condition().parseString("for some X in Y => X = 3")[0]
        self.assertEqual(
            result, ForSome(Variable("X"), Variable("Y"), Equal(Variable("X"), Number(3)))
        )

    def test_universal_quantification(self) -> None:
        result = FSMParser.condition().parseString("for all X in Y => X = Bar")[0]
        self.assertEqual(
            result, ForAll(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Bar")))
        )

    def test_type_conversion_simple(self) -> None:
        expr = "Foo (Bar) = 5"
        result = FSMParser.condition().parseString(expr)[0]
        expected = Equal(Convert(Variable("Bar"), Variable("Foo")), Number(5))
        self.assertEqual(result, expected)

    def test_type_conversion(self) -> None:
        expr = "TLS_Handshake.Supported_Versions (E.Data) = 5"
        result = FSMParser.condition().parseString(expr)[0]
        expected = Equal(
            Convert(Variable("E.Data"), Variable("TLS_Handshake.Supported_Versions")), Number(5)
        )
        self.assertEqual(result, expected)

    def test_use_type_conversion(self) -> None:
        expr = "GreenTLS.TLS_1_3 not in TLS_Handshake.Supported_Versions (E.Data).Versions"
        result = FSMParser.condition().parseString(expr)[0]
        expected = NotContains(
            Variable("GreenTLS.TLS_1_3"),
            Field(
                Convert(Variable("E.Data"), Variable("TLS_Handshake.Supported_Versions")),
                "Versions",
            ),
        )
        self.assertEqual(result, expected)
