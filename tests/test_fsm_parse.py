import unittest

from rflx.expression import (
    FALSE,
    TRUE,
    Add,
    And,
    Div,
    Equal,
    Greater,
    Length,
    Less,
    Mul,
    Name,
    NotEqual,
    Number,
    Or,
    Sub,
)
from rflx.fsm_expression import (
    Binding,
    Comprehension,
    Contains,
    Conversion,
    Field,
    ForAll,
    ForSome,
    Head,
    MessageAggregate,
    NotContains,
    Opaque,
    Present,
    String,
    SubprogramCall,
    Valid,
)
from rflx.fsm_parser import FSMParser


class TestFSM(unittest.TestCase):  # pylint: disable=too-many-public-methods
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_simple_equation(self) -> None:
        result = FSMParser.expression().parseString("Foo.Bar = abc")[0]
        self.assertEqual(result, Equal(Name("Foo.Bar"), Name("abc")))

    def test_simple_inequation(self) -> None:
        result = FSMParser.expression().parseString("Foo.Bar /= abc")[0]
        self.assertEqual(result, NotEqual(Name("Foo.Bar"), Name("abc")))

    def test_valid(self) -> None:
        result = FSMParser.expression().parseString("Something'Valid")[0]
        self.assertEqual(result, Valid(Name("Something")))

    def test_conjunction_valid(self) -> None:
        result = FSMParser.expression().parseString("Foo'Valid and Bar'Valid")[0]
        self.assertEqual(result, And(Valid(Name("Foo")), Valid(Name("Bar"))))

    def test_opaque(self) -> None:
        result = FSMParser.expression().parseString("Something'Opaque")[0]
        self.assertEqual(result, Opaque(Name("Something")))

    def test_conjunction(self) -> None:
        result = FSMParser.expression().parseString("Foo = Bar and Bar /= Baz")[0]
        self.assertEqual(
            result, And(Equal(Name("Foo"), Name("Bar")), NotEqual(Name("Bar"), Name("Baz"))),
        )

    def test_conjunction_multi(self) -> None:
        result = FSMParser.expression().parseString("Foo = Bar and Bar /= Baz and Baz = Foo")[0]
        expected = And(
            Equal(Name("Foo"), Name("Bar")),
            NotEqual(Name("Bar"), Name("Baz")),
            Equal(Name("Baz"), Name("Foo")),
        )
        self.assertEqual(result, expected)

    def test_disjunction(self) -> None:
        result = FSMParser.expression().parseString("Foo = Bar or Bar /= Baz")[0]
        self.assertEqual(
            result, Or(Equal(Name("Foo"), Name("Bar")), NotEqual(Name("Bar"), Name("Baz"))),
        )

    def test_disjunction_multi(self) -> None:
        result = FSMParser.expression().parseString("Foo = Bar or Bar /= Baz or Baz'Valid = False")[
            0
        ]
        self.assertEqual(
            result,
            Or(
                Equal(Name("Foo"), Name("Bar")),
                NotEqual(Name("Bar"), Name("Baz")),
                Equal(Valid(Name("Baz")), FALSE),
            ),
        )

    def test_in_operator(self) -> None:
        result = FSMParser.expression().parseString("Foo in Bar")[0]
        self.assertEqual(result, Contains(Name("Foo"), Name("Bar")))

    def test_not_in_operator(self) -> None:
        result = FSMParser.expression().parseString("Foo not in Bar")[0]
        self.assertEqual(result, NotContains(Name("Foo"), Name("Bar")))

    def test_not_in_whitespace_operator(self) -> None:
        result = FSMParser.expression().parseString("Foo not   in  Bar")[0]
        self.assertEqual(result, NotContains(Name("Foo"), Name("Bar")))

    def test_parenthesized_expression(self) -> None:
        result = FSMParser.expression().parseString("Foo = True and (Bar = False or Baz = False)")[
            0
        ]
        self.assertEqual(
            result,
            And(
                Equal(Name("Foo"), TRUE), Or(Equal(Name("Bar"), FALSE), Equal(Name("Baz"), FALSE)),
            ),
        )

    def test_parenthesized_expression2(self) -> None:
        result = FSMParser.expression().parseString("Foo'Valid and (Bar'Valid or Baz'Valid)")[0]
        self.assertEqual(
            result, And(Valid(Name("Foo")), Or(Valid(Name("Bar")), Valid(Name("Baz"))))
        )

    def test_numeric_constant_expression(self) -> None:
        result = FSMParser.expression().parseString("Keystore_Message.Length = 0")[0]
        self.assertEqual(result, Equal(Name("Keystore_Message.Length"), Number(0)))

    def test_complex_expression(self) -> None:
        expr = (
            "Keystore_Message'Valid = False "
            "or Keystore_Message.Tag /= KEYSTORE_RESPONSE "
            "or Keystore_Message.Request /= KEYSTORE_REQUEST_PSK_IDENTITIES "
            "or (Keystore_Message.Length = 0 "
            "    and TLS_Handshake.PSK_DHE_KE not in Configuration.PSK_Key_Exchange_Modes)"
        )
        result = FSMParser.expression().parseString(expr)[0]
        expected = Or(
            Equal(Valid(Name("Keystore_Message")), FALSE),
            NotEqual(Name("Keystore_Message.Tag"), Name("KEYSTORE_RESPONSE")),
            NotEqual(Name("Keystore_Message.Request"), Name("KEYSTORE_REQUEST_PSK_IDENTITIES")),
            And(
                Equal(Name("Keystore_Message.Length"), Number(0)),
                NotContains(
                    Name("TLS_Handshake.PSK_DHE_KE"), Name("Configuration.PSK_Key_Exchange_Modes"),
                ),
            ),
        )
        self.assertEqual(result, expected)

    def test_existential_quantification(self) -> None:
        result = FSMParser.expression().parseString("for some X in Y => X = 3")[0]
        self.assertEqual(result, ForSome(Name("X"), Name("Y"), Equal(Name("X"), Number(3))))

    def test_complex_existential_quantification(self) -> None:
        expr = (
            "for some E in Server_Hello_Message.Extensions => "
            "(E.Tag = TLS_Handshake.EXTENSION_SUPPORTED_VERSIONS and "
            "(GreenTLS.TLS_1_3 not in TLS_Handshake.Supported_Versions (E.Data).Versions))"
        )
        result = FSMParser.expression().parseString(expr)[0]
        expected = ForSome(
            Name("E"),
            Name("Server_Hello_Message.Extensions"),
            And(
                Equal(Name("E.Tag"), Name("TLS_Handshake.EXTENSION_SUPPORTED_VERSIONS")),
                NotContains(
                    Name("GreenTLS.TLS_1_3"),
                    Field(
                        Conversion(Name("TLS_Handshake.Supported_Versions"), Name("E.Data")),
                        "Versions",
                    ),
                ),
            ),
        )
        self.assertEqual(
            result, expected, msg=f"\nRESULT:\n{repr(result)}\nEXPECTED:\n{repr(expected)}\n"
        )

    def test_universal_quantification(self) -> None:
        result = FSMParser.expression().parseString("for all X in Y => X = Bar")[0]
        self.assertEqual(result, ForAll(Name("X"), Name("Y"), Equal(Name("X"), Name("Bar"))))

    def test_type_conversion_simple(self) -> None:
        expr = "Foo.T (Bar) = 5"
        result = FSMParser.expression().parseString(expr)[0]
        expected = Equal(Conversion(Name("Foo.T"), Name("Bar")), Number(5))
        self.assertEqual(result, expected)

    def test_type_conversion(self) -> None:
        expr = "TLS_Handshake.Supported_Versions (E.Data) = 5"
        result = FSMParser.expression().parseString(expr)[0]
        expected = Equal(
            Conversion(Name("TLS_Handshake.Supported_Versions"), Name("E.Data")), Number(5),
        )
        self.assertEqual(result, expected)

    def test_use_type_conversion(self) -> None:
        expr = "GreenTLS.TLS_1_3 not in TLS_Handshake.Supported_Versions (E.Data).Versions"
        result = FSMParser.expression().parseString(expr)[0]
        expected = NotContains(
            Name("GreenTLS.TLS_1_3"),
            Field(
                Conversion(Name("TLS_Handshake.Supported_Versions"), Name("E.Data")), "Versions",
            ),
        )
        self.assertEqual(result, expected, msg=f"\n\n{result}\n !=\n{expected}")

    def test_present(self) -> None:
        result = FSMParser.expression().parseString("Something'Present")[0]
        self.assertEqual(result, Present(Name("Something")))

    def test_conjunction_present(self) -> None:
        result = FSMParser.expression().parseString("Foo'Present and Bar'Present")[0]
        self.assertEqual(result, And(Present(Name("Foo")), Present(Name("Bar"))))

    def test_length_lt(self) -> None:
        result = FSMParser.expression().parseString("Foo'Length < 100")[0]
        self.assertEqual(result, Less(Length(Name("Foo")), Number(100)), msg=f"\n\n{result}")

    def test_gt(self) -> None:
        result = FSMParser.expression().parseString("Server_Name_Extension.Data_Length > 0")[0]
        self.assertEqual(result, Greater(Name("Server_Name_Extension.Data_Length"), Number(0)))

    def test_field_simple(self) -> None:
        result = FSMParser.expression().parseString("Types.Bar (Foo).Fld")[0]
        self.assertEqual(result, Field(Conversion(Name("Types.Bar"), Name("Foo")), "Fld"))

    def test_field_length(self) -> None:
        result = FSMParser.expression().parseString("Types.Bar (Foo).Fld'Length")[0]
        self.assertEqual(result, Length(Field(Conversion(Name("Types.Bar"), Name("Foo")), "Fld")))

    def test_field_length_lt(self) -> None:
        result = FSMParser.expression().parseString("Types.Bar (Foo).Fld'Length < 100")[0]
        self.assertEqual(
            result,
            Less(Length(Field(Conversion(Name("Types.Bar"), Name("Foo")), "Fld")), Number(100),),
        )

    def test_list_comprehension(self) -> None:
        result = FSMParser.expression().parseString("[for E in List => E.Bar when E.Tag = Foo]")[0]
        self.assertEqual(
            result,
            Comprehension(
                Name("E"), Name("List"), Name("E.Bar"), Equal(Name("E.Tag"), Name("Foo")),
            ),
        )

    def test_list_comprehension_without_condition(self) -> None:
        result = FSMParser.expression().parseString("[for K in PSKs => K.Identity]")[0]
        expected = Comprehension(Name("K"), Name("PSKs"), Name("K.Identity"), TRUE)
        self.assertEqual(result, expected)

    def test_head_attribute(self) -> None:
        result = FSMParser.expression().parseString("Foo'Head")[0]
        self.assertEqual(result, Head(Name("Foo")))

    def test_head_attribute_comprehension(self) -> None:
        result = FSMParser.expression().parseString(
            "[for E in List => E.Bar when E.Tag = Foo]'Head"
        )[0]
        self.assertEqual(
            result,
            Head(
                Comprehension(
                    Name("E"), Name("List"), Name("E.Bar"), Equal(Name("E.Tag"), Name("Foo")),
                )
            ),
        )

    def test_list_head_field_simple(self) -> None:
        result = FSMParser.expression().parseString("Foo'Head.Data")[0]
        self.assertEqual(result, Field(Head(Name("Foo")), "Data"))

    def test_list_head_field(self) -> None:
        result = FSMParser.expression().parseString(
            "[for E in List => E.Bar when E.Tag = Foo]'Head.Data"
        )[0]
        self.assertEqual(
            result,
            Field(
                Head(
                    Comprehension(
                        Name("E"), Name("List"), Name("E.Bar"), Equal(Name("E.Tag"), Name("Foo")),
                    )
                ),
                "Data",
            ),
        )

    def test_complex(self) -> None:
        result = FSMParser.expression().parseString(
            "(for some S in TLS_Handshake.Key_Share_CH ([for E in Client_Hello_Message.Extensions"
            " => E when E.Tag = TLS_Handshake.EXTENSION_KEY_SHARE]'Head.Data).Shares => S.Group"
            " = Selected_Group) = False"
        )[0]
        expected = Equal(
            ForSome(
                Name("S"),
                Field(
                    Conversion(
                        Name("TLS_Handshake.Key_Share_CH"),
                        Field(
                            Head(
                                Comprehension(
                                    Name("E"),
                                    Name("Client_Hello_Message.Extensions"),
                                    Name("E"),
                                    Equal(
                                        Name("E.Tag"), Name("TLS_Handshake.EXTENSION_KEY_SHARE"),
                                    ),
                                )
                            ),
                            "Data",
                        ),
                    ),
                    "Shares",
                ),
                Equal(Name("S.Group"), Name("Selected_Group")),
            ),
            FALSE,
        )
        self.assertEqual(result, expected)

    def test_simple_aggregate(self) -> None:
        result = FSMParser.expression().parseString("Message'(Data => Foo)")[0]
        expected = MessageAggregate(Name("Message"), {"Data": Name("Foo")})
        self.assertEqual(result, expected)

    def test_null_aggregate(self) -> None:
        result = FSMParser.expression().parseString("Message'(null message)")[0]
        expected = MessageAggregate(Name("Message"), {})
        self.assertEqual(result, expected)

    def test_complex_aggregate(self) -> None:
        result = FSMParser.expression().parseString(
            "Complex.Message'(Data1 => Foo, Data2 => Bar, Data3 => Baz)"
        )[0]
        expected = MessageAggregate(
            Name("Complex.Message"),
            {"Data1": Name("Foo"), "Data2": Name("Bar"), "Data3": Name("Baz")},
        )
        self.assertEqual(result, expected)

    def test_simple_function_call(self) -> None:
        result = FSMParser.expression().parseString("Func (Parameter)")[0]
        expected = SubprogramCall(Name("Func"), [Name("Parameter")])
        self.assertEqual(result, expected, msg=f"\n\n{result}\n !=\n{expected}")

    def test_complex_function_call(self) -> None:
        result = FSMParser.expression().parseString("Complex_Function (Param1, Param2, Param3)")[0]
        expected = SubprogramCall(
            Name("Complex_Function"), [Name("Param1"), Name("Param2"), Name("Param3")],
        )
        self.assertEqual(result, expected)

    def test_simple_binding(self) -> None:
        result = FSMParser.expression().parseString("M1'(Data => B1) where B1 = M2'(Data => B2)")[0]
        expected = Binding(
            MessageAggregate(Name("M1"), {"Data": Name("B1")}),
            {"B1": MessageAggregate(Name("M2"), {"Data": Name("B2")})},
        )
        self.assertEqual(result, expected)

    def test_multi_binding(self) -> None:
        result = FSMParser.expression().parseString(
            "M1'(Data1 => B1, Data2 => B2) where B1 = M2'(Data => B2), B2 = M2'(Data => B3)"
        )[0]
        expected = Binding(
            MessageAggregate(Name("M1"), {"Data1": Name("B1"), "Data2": Name("B2")}),
            {
                "B1": MessageAggregate(Name("M2"), {"Data": Name("B2")}),
                "B2": MessageAggregate(Name("M2"), {"Data": Name("B3")}),
            },
        )
        self.assertEqual(result, expected)

    def test_nested_binding(self) -> None:
        result = FSMParser.expression().parseString(
            "M1'(Data => B1) where B1 = M2'(Data => B2) where B2 = M3'(Data => B3)"
        )[0]
        expected = Binding(
            MessageAggregate(Name("M1"), {"Data": Name("B1")}),
            {
                "B1": Binding(
                    MessageAggregate(Name("M2"), {"Data": Name("B2")}),
                    {"B2": MessageAggregate(Name("M3"), {"Data": Name("B3")})},
                )
            },
        )
        self.assertEqual(
            result, expected, msg=f"\n\n  result={repr(result)},\nexpected={repr(expected)}"
        )

    def test_simple_add(self) -> None:
        result = FSMParser.expression().parseString("Foo + Bar")[0]
        expected = Add(Name("Foo"), Name("Bar"))
        self.assertEqual(result, expected)

    def test_simple_sub(self) -> None:
        result = FSMParser.expression().parseString("Foo - Bar")[0]
        expected = Sub(Name("Foo"), Name("Bar"))
        self.assertEqual(result, expected)

    def test_simple_mul(self) -> None:
        result = FSMParser.expression().parseString("Foo * Bar")[0]
        expected = Mul(Name("Foo"), Name("Bar"))
        self.assertEqual(result, expected)

    def test_simple_div(self) -> None:
        result = FSMParser.expression().parseString("Foo / Bar")[0]
        expected = Div(Name("Foo"), Name("Bar"))
        self.assertEqual(result, expected)

    def test_arith_expression(self) -> None:
        result = FSMParser.expression().parseString("Foo + Bar - Foo2 / Bar * Baz + 3")[0]
        expected = Add(
            Sub(Add(Name("Foo"), Name("Bar")), Mul(Div(Name("Foo2"), Name("Bar")), Name("Baz")),),
            Number(3),
        )
        self.assertEqual(result, expected, msg=f"\n\n{result}\n{expected}")

    def test_string(self) -> None:
        result = FSMParser.expression().parseString('"SomeString"')[0]
        expected = String("SomeString")
        self.assertEqual(result, expected)

    def test_string_with_whitespace(self) -> None:
        result = FSMParser.expression().parseString('"Some String With Whitespace"')[0]
        expected = String("Some String With Whitespace")
        self.assertEqual(result, expected)
