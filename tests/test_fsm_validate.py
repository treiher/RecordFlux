# pylint: disable=too-many-lines
import unittest

from rflx.expression import (
    FALSE,
    TRUE,
    Channel,
    Equal,
    Length,
    Number,
    Renames,
    Subprogram,
    Variable,
    VariableDeclaration,
)
from rflx.fsm import State, StateMachine, StateName, Transition
from rflx.fsm_expression import (
    Binding,
    Comprehension,
    Contains,
    Conversion,
    Field,
    ForAll,
    ForSome,
    MessageAggregate,
    NotContains,
    String,
    SubprogramCall,
    Valid,
)
from rflx.model import ModelError
from rflx.statement import Assignment, Erase, Reset


class TestFSM(unittest.TestCase):  # pylint: disable=too-many-public-methods
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_binding_aggregate(self) -> None:
        binding = Binding(
            MessageAggregate(Variable("M1"), {"Data": Variable("B1")}),
            {"B1": MessageAggregate(Variable("M2"), {"Data": Variable("B2")})},
        )
        expected = MessageAggregate(
            Variable("M1"), {"Data": MessageAggregate(Variable("M2"), {"Data": Variable("B2")})}
        )
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forall_predicate(self) -> None:
        binding = Binding(
            ForAll(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Bar"))),
            {"Bar": Variable("Baz")},
        )
        expected = ForAll(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Baz")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forall_iterable(self) -> None:
        binding = Binding(
            ForAll(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Bar"))),
            {"Y": Variable("Baz")},
        )
        expected = ForAll(Variable("X"), Variable("Baz"), Equal(Variable("X"), Variable("Bar")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forsome_predicate(self) -> None:
        binding = Binding(
            ForSome(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Bar"))),
            {"Bar": Variable("Baz")},
        )
        expected = ForSome(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Baz")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forsome_iterable(self) -> None:
        binding = Binding(
            ForSome(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Bar"))),
            {"Y": Variable("Baz")},
        )
        expected = ForSome(Variable("X"), Variable("Baz"), Equal(Variable("X"), Variable("Bar")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_contains_left(self) -> None:
        binding = Binding(Contains(Variable("X"), Variable("Y")), {"X": Variable("Baz")},)
        expected = Contains(Variable("Baz"), Variable("Y"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_contains_right(self) -> None:
        binding = Binding(Contains(Variable("X"), Variable("Y")), {"Y": Variable("Baz")},)
        expected = Contains(Variable("X"), Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_not_contains_left(self) -> None:
        binding = Binding(NotContains(Variable("X"), Variable("Y")), {"X": Variable("Baz")},)
        expected = NotContains(Variable("Baz"), Variable("Y"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_not_contains_right(self) -> None:
        binding = Binding(NotContains(Variable("X"), Variable("Y")), {"Y": Variable("Baz")},)
        expected = NotContains(Variable("X"), Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_subprogram(self) -> None:
        binding = Binding(
            SubprogramCall(Variable("Sub"), [Variable("A"), Variable("B"), Variable("C")]),
            {"B": Variable("Baz")},
        )
        expected = SubprogramCall(Variable("Sub"), [Variable("A"), Variable("Baz"), Variable("C")])
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_field(self) -> None:
        binding = Binding(Field(Variable("A"), "fld"), {"A": Variable("Baz")})
        expected = Field(Variable("Baz"), "fld")
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_list_comprehension(self) -> None:
        binding = Binding(
            Comprehension(
                Variable("E"),
                Variable("List"),
                Variable("E.Bar"),
                Equal(Variable("E.Tag"), Variable("Foo")),
            ),
            {"List": Variable("Foo")},
        )
        expected = Comprehension(
            Variable("E"),
            Variable("Foo"),
            Variable("E.Bar"),
            Equal(Variable("E.Tag"), Variable("Foo")),
        )
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_length(self) -> None:
        binding = Binding(Length(Variable("A")), {"A": Variable("Baz")})
        expected = Length(Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_simplify_string(self) -> None:
        value = String("Test")
        self.assertEqual(value, value.simplified())

    def test_binding_multiple_bindings(self) -> None:
        binding = Binding(
            Field(Variable("A"), "fld"), {"A": Binding(Variable("B"), {"B": Variable("Baz")})}
        )
        expected = Field(Variable("Baz"), "fld")
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_multiple_variables(self) -> None:
        binding = Binding(
            SubprogramCall(Variable("Sub"), [Variable("A"), Variable("A")]), {"A": Variable("Baz")}
        )
        expected = SubprogramCall(Variable("Sub"), [Variable("Baz"), Variable("Baz")])
        result = binding.simplified()
        self.assertEqual(result, expected, msg=f"{result}\n!=\n{expected}")

    def test_binding_conversion(self) -> None:
        binding = Binding(Conversion(Variable("Type"), Variable("A")), {"A": Variable("Baz")})
        expected = Conversion(Variable("Type"), Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_conversion_name_unchanged(self) -> None:
        binding = Binding(Conversion(Variable("Type"), Variable("A")), {"Type": Variable("Baz")})
        expected = Conversion(Variable("Type"), Variable("A"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_undeclared_variable(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^undeclared variable Undefined in transition 0 of state START"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[
                            Transition(
                                target=StateName("END"),
                                condition=Equal(Variable("Undefined"), TRUE),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_declared_variable(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[
                        Transition(
                            target=StateName("END"), condition=Equal(Variable("Defined"), TRUE)
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={"Defined": VariableDeclaration(Variable("Some_Type"))},
        )

    def test_declared_local_variable(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
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
                    declarations={"Local": VariableDeclaration(Variable("Some_Type"))},
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Variable("Some_Type"))},
        )

    def test_undeclared_local_variable(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^undeclared variable Start_Local in transition 0 of state STATE"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("STATE"))],
                        declarations={"Start_Local": VariableDeclaration(Variable("Some_Type"))},
                    ),
                    State(
                        name=StateName("STATE"),
                        transitions=[
                            Transition(
                                target=StateName("END"),
                                condition=Equal(Variable("Start_Local"), Variable("Global")),
                            )
                        ],
                        declarations={"Local": VariableDeclaration(Variable("Some_Type"))},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Variable("Some_Type"))},
            )

    def test_declared_local_variable_valid(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[
                        Transition(
                            target=StateName("END"),
                            condition=Equal(Valid(Variable("Global")), TRUE),
                        )
                    ],
                    declarations={},
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Variable("Boolean"))},
        )

    def test_declared_local_variable_field(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[
                        Transition(
                            target=StateName("END"),
                            condition=Equal(Field(Variable("Global"), "fld"), TRUE),
                        )
                    ],
                    declarations={},
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Variable("Boolean"))},
        )

    def test_assignment_to_undeclared_variable(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^Assignment to undeclared variable Undefined in action 0 of state START"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[Assignment(Variable("Undefined"), FALSE)],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_assignment_from_undeclared_variable(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^undeclared variable Undefined in assignment in action 0 of state START"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[Assignment(Variable("Global"), Variable("Undefined"))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Variable("Boolean"))},
            )

    def test_erasure_of_undeclared_variable(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^Erasure of undeclared variable Undefined in action 0 of state START"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[Erase(Variable("Undefined"))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_reset_of_undeclared_list(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^Reset of undeclared list Undefined in action 0 of state START"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[Reset(Variable("Undefined"))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_call_to_undeclared_function(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^undeclared subprogram UndefSub called in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Global"),
                                SubprogramCall(Variable("UndefSub"), [Variable("Global")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Variable("Boolean"))},
            )

    def test_call_to_builtin_read(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[
                        Transition(
                            target=StateName("END"), condition=Equal(Variable("Global"), TRUE)
                        )
                    ],
                    declarations={},
                    actions=[
                        Assignment(
                            Variable("Global"),
                            SubprogramCall(Variable("Read"), [Variable("Some_Channel")]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Global": VariableDeclaration(Variable("Boolean")),
                "Some_Channel": Channel(read=True, write=False),
            },
        )

    def test_call_to_builtin_write(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[
                        Transition(
                            target=StateName("END"), condition=Equal(Variable("Success"), TRUE)
                        )
                    ],
                    declarations={},
                    actions=[
                        Assignment(
                            Variable("Success"),
                            SubprogramCall(Variable("Write"), [Variable("Some_Channel"), TRUE]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Success": VariableDeclaration(Variable("Boolean")),
                "Some_Channel": Channel(read=False, write=True),
            },
        )

    def test_call_to_builtin_call(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[Transition(target=StateName("END"))],
                    declarations={},
                    actions=[
                        Assignment(
                            Variable("Result"),
                            SubprogramCall(Variable("Call"), [Variable("Some_Channel"), TRUE]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Variable("Boolean")),
                "Some_Channel": Channel(read=True, write=True),
            },
        )

    def test_call_to_builtin_data_available(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[Transition(target=StateName("END"))],
                    declarations={},
                    actions=[
                        Assignment(
                            Variable("Result"),
                            SubprogramCall(Variable("Data_Available"), [Variable("Some_Channel")]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Variable("Boolean")),
                "Some_Channel": Channel(read=True, write=True),
            },
        )

    def test_call_to_builtin_read_without_arguments(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^no channel argument in call to Read in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(Variable("Result"), SubprogramCall(Variable("Read"), []))
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Result": VariableDeclaration(Variable("Boolean"))},
            )

    def test_call_to_builtin_read_undeclared_channel(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^undeclared channel in call to Read in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(Variable("Read"), [Variable("Undeclared")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Result": VariableDeclaration(Variable("Boolean"))},
            )

    def test_call_to_builtin_read_invalid_channel_type(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^invalid channel type in call to Read in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(Variable("Read"), [Variable("Result")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Result": VariableDeclaration(Variable("Boolean"))},
            )

    def test_call_to_builtin_write_invalid_channel_mode(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel not writable in call to Write in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(Variable("Write"), [Variable("Out_Channel")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Variable("Boolean")),
                    "Out_Channel": Channel(read=True, write=False),
                },
            )

    def test_call_to_builtin_data_available_invalid_channel_mode(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel not readable in call to Data_Available in "
            "assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(
                                    Variable("Data_Available"), [Variable("Out_Channel")]
                                ),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Variable("Boolean")),
                    "Out_Channel": Channel(read=False, write=True),
                },
            )

    def test_call_to_builtin_read_invalid_channel_mode(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel not readable in call to Read in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(Variable("Read"), [Variable("Channel")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Variable("Boolean")),
                    "Channel": Channel(read=False, write=True),
                },
            )

    def test_call_to_builtin_call_channel_not_readable(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel not readable in call to Call in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(Variable("Call"), [Variable("Channel")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Variable("Boolean")),
                    "Channel": Channel(read=False, write=True),
                },
            )

    def test_call_to_builtin_call_channel_not_writable(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel not writable in call to Call in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(Variable("Call"), [Variable("Channel")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Variable("Boolean")),
                    "Channel": Channel(read=True, write=False),
                },
            )

    def test_subprogram_call(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[
                        Transition(
                            target=StateName("END"), condition=Equal(Variable("Result"), TRUE)
                        )
                    ],
                    declarations={},
                    actions=[
                        Assignment(Variable("Result"), SubprogramCall(Variable("SubProg"), []))
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Variable("Boolean")),
                "SubProg": Subprogram([], Variable("Boolean")),
            },
        )

    def test_undeclared_variable_in_subprogram_call(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            r"^undeclared variable Undefined \(parameter 0\) in call to SubProg "
            "in assignment in action 0 of state START",
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Result"),
                                SubprogramCall(Variable("SubProg"), [Variable("Undefined")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Variable("Boolean")),
                    "SubProg": Subprogram([], Variable("Boolean")),
                },
            )

    def test_function_declaration_is_no_builtin_read(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^subprogram declaration shadows builtin subprogram READ"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Read": Subprogram([], Variable("Boolean"))},
            )

    def test_function_declaration_is_no_builtin_write(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^channel declaration shadows builtin subprogram WRITE"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Write": Channel(read=True, write=False)},
            )

    def test_function_declaration_is_no_builtin_call(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^variable declaration shadows builtin subprogram CALL"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Call": VariableDeclaration(Variable("Boolean"))},
            )

    def test_function_declaration_is_no_builtin_data_available(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^renames declaration shadows builtin subprogram DATA_AVAILABLE"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Data_Available": Renames(Variable("Boolean"), Variable("Foo.Bar"))},
            )

    def test_local_variable_shadows_global(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^local variable Global shadows global declaration in state START"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[
                            Transition(
                                target=StateName("END"), condition=Equal(Variable("Global"), TRUE)
                            )
                        ],
                        declarations={"Global": VariableDeclaration(Variable("Boolean"))},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Variable("Boolean"))},
            )

    def test_unused_global_variable(self) -> None:
        with self.assertRaisesRegex(ModelError, "^unused variable Global"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Variable("Boolean"))},
            )

    def test_unused_local_variable(self) -> None:
        with self.assertRaisesRegex(ModelError, "^unused local variable Data"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={"Data": VariableDeclaration(Variable("Boolean"))},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={},
            )

    def test_renames_references_undefined_variable(self) -> None:
        with self.assertRaisesRegex(ModelError, "^undeclared variable Foo in global renames Ren"):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[
                            Transition(
                                target=StateName("END"), condition=Equal(Variable("Ren"), TRUE)
                            )
                        ],
                        declarations={},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Ren": Renames(Variable("Boolean"), Variable("Foo"))},
            )

    def test_binding_as_subprogram_parameter(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[Transition(target=StateName("END"))],
                    declarations={},
                    actions=[
                        Assignment(
                            Variable("Result"),
                            Binding(
                                SubprogramCall(Variable("SubProg"), [Length(Variable("Bound"))]),
                                {"Bound": Variable("Variable")},
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Variable("Boolean")),
                "Variable": VariableDeclaration(Variable("Boolean")),
                "SubProg": Subprogram([], Variable("Boolean")),
            },
        )

    def test_for_all(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[
                        Transition(
                            target=StateName("END"),
                            condition=ForAll(
                                Variable("E"),
                                Variable("List"),
                                Equal(Field(Variable("E"), "Tag"), Number(42)),
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={"List": VariableDeclaration(Variable("Foo"))},
        )

    def test_append_list_attribute(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[Transition(target=StateName("END"))],
                    declarations={},
                    actions=[
                        Assignment(
                            Variable("List"),
                            SubprogramCall(
                                Variable("Append"), [Variable("List"), Variable("Element")]
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "List": VariableDeclaration(Variable("List_Type")),
                "Element": VariableDeclaration(Variable("Element_Type")),
            },
        )

    def test_extend_list_attribute(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[Transition(target=StateName("END"))],
                    declarations={},
                    actions=[
                        Assignment(
                            Variable("List"),
                            SubprogramCall(
                                Variable("Extend"), [Variable("List"), Variable("Element")]
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "List": VariableDeclaration(Variable("List_Type")),
                "Element": VariableDeclaration(Variable("Element_Type")),
            },
        )

    def test_aggregate_with_undefined_parameter(self) -> None:
        with self.assertRaisesRegex(
            ModelError, "^undeclared variable Undef in assignment in action 0 of state START"
        ):
            StateMachine(
                name="fsm",
                initial=StateName("START"),
                final=StateName("END"),
                states=[
                    State(
                        name=StateName("START"),
                        transitions=[Transition(target=StateName("END"))],
                        declarations={},
                        actions=[
                            Assignment(
                                Variable("Data"),
                                MessageAggregate(
                                    Variable("Data_Type"),
                                    {"Foo": Variable("Data"), "Bar": Variable("Undef")},
                                ),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Data": VariableDeclaration(Variable("Data_Type"))},
            )
