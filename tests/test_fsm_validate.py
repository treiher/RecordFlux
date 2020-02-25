import unittest

from rflx.expression import (
    FALSE,
    TRUE,
    Channel,
    Equal,
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
            ModelError, "^Undeclared variable Undefined in transition 0 of state START"
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
            ModelError, "^Undeclared variable Start_Local in transition 0 of state STATE"
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
            ModelError, "^Undeclared variable Undefined in assignment in action 0 of state START"
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
            "^Undeclared subprogram UndefSub called in assignment in action 0 of state START",
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
                    transitions=[Transition(target=StateName("END"))],
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
                    transitions=[Transition(target=StateName("END"))],
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
            "^No channel argument in call to Read in assignment in action 0 of state START",
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
            "^Undeclared channel in call to Read in assignment in action 0 of state START",
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
            "^Invalid channel type in call to Read in assignment in action 0 of state START",
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
            "^Channel not writable in call to Write in assignment in action 0 of state START",
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
            "^Channel not readable in call to Data_Available in "
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
            "^Channel not readable in call to Read in assignment in action 0 of state START",
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
            "^Channel not readable in call to Call in assignment in action 0 of state START",
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
            "^Channel not writable in call to Call in assignment in action 0 of state START",
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
                    transitions=[Transition(target=StateName("END"))],
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
            r"^Undeclared variable Undefined \(parameter 0\) in call to SubProg "
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
            ModelError, "^Subprogram declaration shadows builtin subprogram READ"
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
            ModelError, "^Channel declaration shadows builtin subprogram WRITE"
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
            ModelError, "^VariableDeclaration declaration shadows builtin subprogram CALL"
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
            ModelError, "^Renames declaration shadows builtin subprogram DATA_AVAILABLE"
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
