import unittest

from rflx.expression import (
    FALSE,
    TRUE,
    And,
    Equal,
    Greater,
    Length,
    Less,
    NotEqual,
    Number,
    Or,
    Variable,
)
from rflx.fsm_expression import (
    Binding,
    Comprehension,
    Contains,
    Field,
    ForAll,
    ForSome,
    FunctionCall,
    Head,
    MessageAggregate,
    NotContains,
    Present,
    Valid,
)
from rflx.fsm_parser import FSMParser


class TestFSM(unittest.TestCase):  # pylint: disable=too-many-public-methods
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
        result = FSMParser.condition().parseString("Foo = Bar or Bar /= Baz or Baz'Valid = False")[
            0
        ]
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

    def test_not_in_whitespace_operator(self) -> None:
        result = FSMParser.condition().parseString("Foo not   in  Bar")[0]
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

    def test_complex_existential_quantification(self) -> None:
        expr = (
            "for some E in Server_Hello_Message.Extensions => "
            "(E.Tag = TLS_Handshake.EXTENSION_SUPPORTED_VERSIONS and "
            "(GreenTLS.TLS_1_3 not in TLS_Handshake.Supported_Versions (E.Data).Versions))"
        )
        result = FSMParser.condition().parseString(expr)[0]
        expected = ForSome(
            Variable("E"),
            Variable("Server_Hello_Message.Extensions"),
            And(
                Equal(Variable("E.Tag"), Variable("TLS_Handshake.EXTENSION_SUPPORTED_VERSIONS")),
                NotContains(
                    Variable("GreenTLS.TLS_1_3"),
                    Field(
                        FunctionCall(
                            Variable("TLS_Handshake.Supported_Versions"), [Variable("E.Data")]
                        ),
                        "Versions",
                    ),
                ),
            ),
        )
        self.assertEqual(result, expected, msg=f"\nRESULT:\n{result}\nEXPECTED:\n{expected}\n")

    def test_universal_quantification(self) -> None:
        result = FSMParser.condition().parseString("for all X in Y => X = Bar")[0]
        self.assertEqual(
            result, ForAll(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Bar")))
        )

    def test_type_conversion_simple(self) -> None:
        expr = "Foo (Bar) = 5"
        result = FSMParser.condition().parseString(expr)[0]
        expected = Equal(FunctionCall(Variable("Foo"), [Variable("Bar")]), Number(5))
        self.assertEqual(result, expected)

    def test_type_conversion(self) -> None:
        expr = "TLS_Handshake.Supported_Versions (E.Data) = 5"
        result = FSMParser.condition().parseString(expr)[0]
        expected = Equal(
            FunctionCall(Variable("TLS_Handshake.Supported_Versions"), [Variable("E.Data")]),
            Number(5),
        )
        self.assertEqual(result, expected)

    def test_use_type_conversion(self) -> None:
        expr = "GreenTLS.TLS_1_3 not in TLS_Handshake.Supported_Versions (E.Data).Versions"
        result = FSMParser.condition().parseString(expr)[0]
        expected = NotContains(
            Variable("GreenTLS.TLS_1_3"),
            Field(
                FunctionCall(Variable("TLS_Handshake.Supported_Versions"), [Variable("E.Data")]),
                "Versions",
            ),
        )
        self.assertEqual(result, expected)

    def test_present(self) -> None:
        result = FSMParser.condition().parseString("Something'Present")[0]
        self.assertEqual(result, Present(Variable("Something")))

    def test_conjunction_present(self) -> None:
        result = FSMParser.condition().parseString("Foo'Present and Bar'Present")[0]
        self.assertEqual(result, And(Present(Variable("Foo")), Present(Variable("Bar"))))

    def test_length_lt(self) -> None:
        result = FSMParser.condition().parseString("Foo'Length < 100")[0]
        self.assertEqual(result, Less(Length(Variable("Foo")), Number(100)), msg=f"\n\n{result}")

    def test_gt(self) -> None:
        result = FSMParser.condition().parseString("Server_Name_Extension.Data_Length > 0")[0]
        self.assertEqual(result, Greater(Variable("Server_Name_Extension.Data_Length"), Number(0)))

    def test_field_simple(self) -> None:
        result = FSMParser.condition().parseString("Bar (Foo).Fld")[0]
        self.assertEqual(result, Field(FunctionCall(Variable("Bar"), [Variable("Foo")]), "Fld"))

    def test_field_length(self) -> None:
        result = FSMParser.condition().parseString("Bar (Foo).Fld'Length")[0]
        self.assertEqual(
            result, Length(Field(FunctionCall(Variable("Bar"), [Variable("Foo")]), "Fld"))
        )

    def test_field_length_lt(self) -> None:
        result = FSMParser.condition().parseString("Bar (Foo).Fld'Length < 100")[0]
        self.assertEqual(
            result,
            Less(
                Length(Field(FunctionCall(Variable("Bar"), [Variable("Foo")]), "Fld")), Number(100)
            ),
        )

    def test_list_comprehension(self) -> None:
        result = FSMParser.condition().parseString("[for E in List => E.Bar when E.Tag = Foo]")[0]
        self.assertEqual(
            result,
            Comprehension(
                Variable("E"),
                Variable("List"),
                Variable("E.Bar"),
                Equal(Variable("E.Tag"), Variable("Foo")),
            ),
        )

    def test_head_attribute(self) -> None:
        result = FSMParser.condition().parseString("Foo'Head")[0]
        self.assertEqual(result, Head(Variable("Foo")))

    def test_head_attribute_comprehension(self) -> None:
        result = FSMParser.condition().parseString(
            "[for E in List => E.Bar when E.Tag = Foo]'Head"
        )[0]
        self.assertEqual(
            result,
            Head(
                Comprehension(
                    Variable("E"),
                    Variable("List"),
                    Variable("E.Bar"),
                    Equal(Variable("E.Tag"), Variable("Foo")),
                )
            ),
        )

    def test_list_head_field_simple(self) -> None:
        result = FSMParser.condition().parseString("Foo'Head.Data")[0]
        self.assertEqual(result, Field(Head(Variable("Foo")), "Data"))

    def test_list_head_field(self) -> None:
        result = FSMParser.condition().parseString(
            "[for E in List => E.Bar when E.Tag = Foo]'Head.Data"
        )[0]
        self.assertEqual(
            result,
            Field(
                Head(
                    Comprehension(
                        Variable("E"),
                        Variable("List"),
                        Variable("E.Bar"),
                        Equal(Variable("E.Tag"), Variable("Foo")),
                    )
                ),
                "Data",
            ),
        )

    def test_complex(self) -> None:
        result = FSMParser.condition().parseString(
            "(for some S in TLS_Handshake.Key_Share_CH ([for E in Client_Hello_Message.Extensions"
            " => E when E.Tag = TLS_Handshake.EXTENSION_KEY_SHARE]'Head.Data).Shares => S.Group"
            " = Selected_Group) = False"
        )[0]
        expected = Equal(
            ForSome(
                Variable("S"),
                Field(
                    FunctionCall(
                        Variable("TLS_Handshake.Key_Share_CH"),
                        [
                            Field(
                                Head(
                                    Comprehension(
                                        Variable("E"),
                                        Variable("Client_Hello_Message.Extensions"),
                                        Variable("E"),
                                        Equal(
                                            Variable("E.Tag"),
                                            Variable("TLS_Handshake.EXTENSION_KEY_SHARE"),
                                        ),
                                    )
                                ),
                                "Data",
                            )
                        ],
                    ),
                    "Shares",
                ),
                Equal(Variable("S.Group"), Variable("Selected_Group")),
            ),
            FALSE,
        )
        self.assertEqual(result, expected)

    def test_simple_aggregate(self) -> None:
        result = FSMParser.condition().parseString("Message'(Data => Foo)")[0]
        expected = MessageAggregate(Variable("Message"), {"Data": Variable("Foo")})
        self.assertEqual(result, expected)

    def test_complex_aggregate(self) -> None:
        result = FSMParser.condition().parseString(
            "Complex.Message'(Data1 => Foo, Data2 => Bar, Data3 => Baz)"
        )[0]
        expected = MessageAggregate(
            Variable("Complex.Message"),
            {"Data1": Variable("Foo"), "Data2": Variable("Bar"), "Data3": Variable("Baz")},
        )
        self.assertEqual(result, expected)

    def test_simple_function_call(self) -> None:
        result = FSMParser.condition().parseString("Fun (Parameter)")[0]
        expected = FunctionCall(Variable("Fun"), [Variable("Parameter")])
        self.assertEqual(result, expected)

    def test_complex_function_call(self) -> None:
        result = FSMParser.condition().parseString("Complex_Function (Param1, Param2, Param3)")[0]
        expected = FunctionCall(
            Variable("Complex_Function"),
            [Variable("Param1"), Variable("Param2"), Variable("Param3")],
        )
        self.assertEqual(result, expected)

    def test_simple_binding(self) -> None:
        result = FSMParser.condition().parseString("M1'(Data => B1) where B1 = M2'(Data => B2)")[0]
        expected = Binding(
            MessageAggregate(Variable("M1"), {"Data": Variable("B1")}),
            {"B1": MessageAggregate(Variable("M2"), {"Data": Variable("B2")})},
        )
        self.assertEqual(result, expected)

    def test_multi_binding(self) -> None:
        result = FSMParser.condition().parseString(
            "M1'(Data1 => B1, Data2 => B2) where B1 = M2'(Data => B2), B2 = M2'(Data => B3)"
        )[0]
        expected = Binding(
            MessageAggregate(Variable("M1"), {"Data1": Variable("B1"), "Data2": Variable("B2")}),
            {
                "B1": MessageAggregate(Variable("M2"), {"Data": Variable("B2")}),
                "B2": MessageAggregate(Variable("M2"), {"Data": Variable("B3")}),
            },
        )
        self.assertEqual(result, expected)

    def test_nested_binding(self) -> None:
        result = FSMParser.condition().parseString(
            "M1'(Data => B1) where B1 = M2'(Data => B2) where B2 = M3'(Data => B3)"
        )[0]
        expected = Binding(
            MessageAggregate(Variable("M1"), {"Data": Variable("B1")}),
            {
                "B1": Binding(
                    MessageAggregate(Variable("M2"), {"Data": Variable("B2")}),
                    {"B2": MessageAggregate(Variable("M3"), {"Data": Variable("B3")})},
                )
            },
        )
        self.assertEqual(
            result, expected, msg=f"\n\n  result={repr(result)},\nexpected={repr(expected)}"
        )
