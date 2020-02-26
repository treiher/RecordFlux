import unittest

from rflx.expression import (
    FALSE,
    Argument,
    Equal,
    Greater,
    Number,
    Renames,
    Subprogram,
    Variable,
    VariableDeclaration,
)
from rflx.fsm import FSM, State, StateMachine, StateName, Transition
from rflx.fsm_expression import SubprogramCall
from rflx.model import ModelError
from rflx.statement import Assignment


class TestFSM(unittest.TestCase):  # pylint: disable=too-many-public-methods
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    def assert_parse_exception_string(self, string: str, regex: str) -> None:
        with self.assertRaisesRegex(ModelError, regex):
            FSM().parse_string("fsm", string)

    def test_simple_fsm(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                initial: START
                final: END
                states:
                  - name: START
                    transitions:
                      - target: END
                  - name: END
            """,
        )
        expected = StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(name=StateName("START"), transitions=[Transition(target=StateName("END"))]),
                State(name=StateName("END")),
            ],
            declarations={},
        )
        self.assertEqual(f.fsms[0], expected)

    def test_missing_initial(self) -> None:
        self.assert_parse_exception_string(
            """
                final: END
                states:
                  - name: START
                    transitions:
                      - target: END
                  - name: END
            """,
            "^missing initial state",
        )

    def test_missing_final(self) -> None:
        self.assert_parse_exception_string(
            """
                initial: START
                states:
                  - name: START
                    transitions:
                      - target: END
                  - name: END
            """,
            "^missing final state",
        )

    def test_missing_states(self) -> None:
        self.assert_parse_exception_string(
            """
                initial: START
                final: END
            """,
            "^missing states",
        )

    def test_empty_states(self) -> None:
        with self.assertRaisesRegex(ModelError, "^empty states"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[],
                declarations={},
            )

    def test_invalid_initial(self) -> None:
        with self.assertRaisesRegex(
            ModelError, '^initial state "NONEXISTENT" does not exist in "fsm"'
        ):
            StateMachine(
                name="fsm",
                initial=StateName("NONEXISTENT"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"), transitions=[Transition(target=StateName("END"))]
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_invalid_final(self) -> None:
        with self.assertRaisesRegex(
            ModelError, '^final state "NONEXISTENT" does not exist in "fsm"'
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("NONEXISTENT"),
                states=[
                    State(
                        name=StateName("START"), transitions=[Transition(target=StateName("END"))]
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_invalid_target_state(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            '^transition from state "START" to non-existent state' ' "NONEXISTENT" in "fsm"',
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("NONEXISTENT"))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_duplicate_state(self) -> None:
        with self.assertRaisesRegex(ModelError, "^duplicate states START"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"), transitions=[Transition(target=StateName("END"))]
                    ),
                    State(name=StateName("START")),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_multiple_duplicate_states(self) -> None:
        with self.assertRaisesRegex(ModelError, "^duplicate states BAR, FOO, START"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"), transitions=[Transition(target=StateName("END"))]
                    ),
                    State(name=StateName("START")),
                    State(name=StateName("FOO")),
                    State(name=StateName("BAR")),
                    State(name=StateName("FOO")),
                    State(name=StateName("BAR")),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_unreachable_state(self) -> None:
        with self.assertRaisesRegex(ModelError, "^unreachable states UNREACHABLE"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"), transitions=[Transition(target=StateName("END"))]
                    ),
                    State(
                        name=StateName("UNREACHABLE"),
                        transitions=[Transition(target=StateName("END"))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_multiple_unreachable_states(self) -> None:
        with self.assertRaisesRegex(ModelError, "^unreachable states UNREACHABLE1, UNREACHABLE2"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"), transitions=[Transition(target=StateName("END"))]
                    ),
                    State(
                        name=StateName("UNREACHABLE1"),
                        transitions=[Transition(target=StateName("END"))],
                    ),
                    State(
                        name=StateName("UNREACHABLE2"),
                        transitions=[Transition(target=StateName("END"))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_detached_state(self) -> None:
        with self.assertRaisesRegex(ModelError, "^detached states DETACHED"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[
                            Transition(target=StateName("END")),
                            Transition(target=StateName("DETACHED")),
                        ],
                    ),
                    State(name=StateName("DETACHED")),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_multiple_detached_states(self) -> None:
        with self.assertRaisesRegex(ModelError, "^detached states DETACHED1, DETACHED2"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[
                            Transition(target=StateName("END")),
                            Transition(target=StateName("DETACHED1")),
                            Transition(target=StateName("DETACHED2")),
                        ],
                    ),
                    State(name=StateName("DETACHED1")),
                    State(name=StateName("DETACHED2")),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_fsm_with_conditions(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                initial: START
                final: END
                variables:
                    - "Error : Boolean"
                states:
                  - name: START
                    transitions:
                      - target: INTERMEDIATE
                        condition: Error = False
                      - target: END
                  - name: INTERMEDIATE
                    transitions:
                      - target: END
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
                    transitions=[
                        Transition(
                            target=StateName("INTERMEDIATE"),
                            condition=Equal(Variable("Error"), FALSE),
                        ),
                        Transition(target=StateName("END")),
                    ],
                ),
                State(
                    name=StateName("INTERMEDIATE"),
                    transitions=[Transition(target=StateName("END"))],
                ),
                State(name=StateName("END")),
            ],
            declarations={"Error": VariableDeclaration(Variable("Boolean"))},
        )
        self.assertEqual(f.fsms[0], expected)

    def test_fsm_with_invalid_condition(self) -> None:
        with self.assertRaisesRegex(
            ModelError, '^error parsing condition 0 from state "START" to' ' "INTERMEDIATE"'
        ):
            FSM().parse_string(
                "fsm",
                """
                    initial: START
                    final: END
                    states:
                      - name: START
                        transitions:
                          - target: INTERMEDIATE
                            condition: and Invalid
                          - target: END
                      - name: INTERMEDIATE
                        transitions:
                          - target: END
                      - name: END
                """,
            )

    def test_fsm_condition_equal(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                initial: START
                final: END
                variables:
                    - "Error : Boolean"
                    - "Something : Boolean"
                states:
                  - name: START
                    transitions:
                      - target: INTERMEDIATE
                        condition: Error = Something
                      - target: END
                  - name: INTERMEDIATE
                    transitions:
                      - target: END
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
                    transitions=[
                        Transition(
                            target=StateName("INTERMEDIATE"),
                            condition=Equal(Variable("Error"), Variable("Something")),
                        ),
                        Transition(target=StateName("END")),
                    ],
                ),
                State(
                    name=StateName("INTERMEDIATE"),
                    transitions=[Transition(target=StateName("END"))],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Error": VariableDeclaration(Variable("Boolean")),
                "Something": VariableDeclaration(Variable("Boolean")),
            },
        )
        self.assertEqual(f.fsms[0], expected)

    def test_unexpected_elements(self) -> None:
        self.assert_parse_exception_string(
            """
                initial: START
                final: END
                invalid1: FOO
                invalid2: BAR
                states:
                  - name: START
                    transitions:
                      - target: END
                  - name: END
            """,
            r"^unexpected elements \[invalid1, invalid2\]",
        )

    def test_fsm_with_function_decl(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                initial: START
                final: END
                functions:
                    - \"Foo(Bar : T1; Baz : P1.T1) return P2.T3\"
                states:
                  - name: START
                    transitions:
                      - target: END
                        condition: Foo (100, 200) > 1000
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
                    transitions=[
                        Transition(
                            target=StateName("END"),
                            condition=Greater(
                                SubprogramCall(Variable("Foo"), [Number(100), Number(200)]),
                                Number(1000),
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Foo": Subprogram(
                    [
                        Argument(Variable("Bar"), Variable("T1")),
                        Argument(Variable("Baz"), Variable("P1.T1")),
                    ],
                    Variable("P2.T3"),
                )
            },
        )
        self.assertEqual(f.fsms[0], expected)

    def test_fsm_with_variable_decl(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                initial: START
                final: END
                variables:
                    - \"Global : Boolean\"
                states:
                  - name: START
                    variables:
                        - \"Local : Boolean\"
                    transitions:
                      - target: END
                        condition: Local = Global
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
                    transitions=[
                        Transition(
                            target=StateName("END"),
                            condition=Equal(Variable("Local"), Variable("Global")),
                        )
                    ],
                    declarations={"Local": VariableDeclaration(Variable("Boolean"))},
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Variable("Boolean"))},
        )
        self.assertEqual(f.fsms[0], expected)

    def test_fsm_with_actions(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                initial: START
                final: END
                variables:
                    - \"Global : Boolean\"
                states:
                  - name: START
                    transitions:
                      - target: END
                    actions:
                        - Global := False
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
                    declarations={},
                    actions=[Assignment(Variable("Global"), FALSE)],
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Variable("Boolean"))},
        )
        self.assertEqual(f.fsms[0], expected)

    def test_duplicate_variable(self) -> None:
        self.assert_parse_exception_string(
            """
                initial: START
                final: END
                variables:
                    - "Foo : Boolean"
                    - "Foo : Some_Type"
                states:
                  - name: START
                    transitions:
                      - target: END
                  - name: END
            """,
            r"^conflicting variable Foo",
        )

    def test_variable_shadowing_channel_name(self) -> None:
        self.assert_parse_exception_string(
            """
                initial: START
                final: END
                channels:
                    - name: Foo
                      mode: Read
                variables:
                    - "Foo : Boolean"
                states:
                  - name: START
                    transitions:
                      - target: END
                  - name: END
            """,
            r"^conflicting channel Foo",
        )

    def test_channel_shadowing_rename(self) -> None:
        self.assert_parse_exception_string(
            """
                initial: START
                final: END
                channels:
                    - name: Foo
                      mode: Read
                renames:
                    - "Foo : Boolean renames Bar"
                states:
                  - name: START
                    transitions:
                      - target: END
                  - name: END
            """,
            r"^conflicting renames Foo",
        )

    def test_fsm_with_renames(self) -> None:
        f = FSM()
        f.parse_string(
            "fsm",
            """
                initial: START
                final: END
                renames:
                    - "Foo : Boolean renames Bar"
                states:
                  - name: START
                    transitions:
                      - target: END
                        condition: Foo = False
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
                    transitions=[
                        Transition(target=StateName("END"), condition=Equal(Variable("Foo"), FALSE))
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={"Foo": Renames(Variable("Boolean"), Variable("Bar"))},
        )
        self.assertEqual(f.fsms[0], expected)
