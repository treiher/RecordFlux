import unittest

from pyparsing import ParseException

from rflx.expression import (
    FALSE,
    Argument,
    Channel,
    Name,
    PrivateDeclaration,
    Renames,
    Subprogram,
    Variable,
    VariableDeclaration,
)
from rflx.fsm import FSM, State, StateMachine, StateName, Transition
from rflx.fsm_expression import Field, SubprogramCall
from rflx.fsm_parser import FSMParser
from rflx.model import ModelError
from rflx.statement import Assignment


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
            VariableDeclaration(Name("TLS_Handshake.Certificate_Authorities")),
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
                Name("TLS_Handshake.Certificate"), Field(Name("CCR_Handshake_Message"), "Payload"),
            ),
        )
        self.assertEqual(result, expected)

    def test_private_variable_declaration(self) -> None:
        result = FSMParser.declaration().parseString("Hash_Context is private")[0]
        expected = ("Hash_Context", PrivateDeclaration())
        self.assertEqual(result, expected)

    def test_channels(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                channels:
                    - name: Channel1_Read_Write
                      mode: Read_Write
                    - name: Channel2_Read
                      mode: Read
                    - name: Channel3_Write
                      mode: Write
                initial: START
                final: END
                states:
                  - name: START
                    transitions:
                      - target: END
                    variables:
                      - "Local : Boolean"
                    actions:
                      - Local := Write(Channel1_Read_Write, Read(Channel2_Read))
                      - Local := Write(Channel3_Write, Local)
                  - name: END
            """,
        )
        expected = StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[Transition(target=StateName("END"))],
                    declarations={"Local": VariableDeclaration(Name("Boolean"))},
                    actions=[
                        Assignment(
                            Name("Local"),
                            SubprogramCall(
                                Name("Write"),
                                [
                                    Name("Channel1_Read_Write"),
                                    SubprogramCall(Name("Read"), [Name("Channel2_Read")]),
                                ],
                            ),
                        ),
                        Assignment(
                            Name("Local"),
                            SubprogramCall(Name("Write"), [Name("Channel3_Write"), Name("Local")],),
                        ),
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Channel1_Read_Write": Channel(read=True, write=True),
                "Channel2_Read": Channel(read=True, write=False),
                "Channel3_Write": Channel(read=False, write=True),
            },
        )
        self.assertEqual(f.fsms[0], expected)

    def test_channel_with_invalid_mode(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^Channel Channel1_Read_Write has invalid mode Invalid"
        ):
            FSM().parse_string(
                "fsm",
                """
                    channels:
                        - name: Channel1_Read_Write
                          mode: Invalid
                    initial: START
                    final: END
                    states:
                      - name: START
                        transitions:
                          - target: END
                      - name: END
                """,
            )

    def test_channel_without_name(self) -> None:
        with self.assertRaisesRegex(ModelError, "^Channel 0 has no name"):
            FSM().parse_string(
                "fsm",
                """
                    channels:
                        - mode: Read_Write
                    initial: START
                    final: END
                    states:
                      - name: START
                        transitions:
                          - target: END
                      - name: END
                """,
            )

    def test_channel_without_mode(self) -> None:
        with self.assertRaisesRegex(ModelError, "^Channel Channel_Without_Mode has no mode"):
            FSM().parse_string(
                "fsm",
                """
                    channels:
                        - name: Channel_Without_Mode
                    initial: START
                    final: END
                    states:
                      - name: START
                        transitions:
                          - target: END
                      - name: END
                """,
            )
