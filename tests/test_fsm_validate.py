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
    Name,
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
            MessageAggregate(Variable("M1"), {"Data": Name("B1")}),
            {"B1": MessageAggregate(Variable("M2"), {"Data": Variable("B2")})},
        )
        expected = MessageAggregate(
            Variable("M1"), {"Data": MessageAggregate(Variable("M2"), {"Data": Variable("B2")})}
        )
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forall_predicate(self) -> None:
        binding = Binding(
            ForAll(Variable("X"), Variable("Y"), Equal(Variable("X"), Name("Bar"))),
            {"Bar": Variable("Baz")},
        )
        expected = ForAll(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Baz")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forall_iterable(self) -> None:
        binding = Binding(
            ForAll(Variable("X"), Name("Y"), Equal(Variable("X"), Variable("Bar"))),
            {"Y": Variable("Baz")},
        )
        expected = ForAll(Variable("X"), Variable("Baz"), Equal(Variable("X"), Variable("Bar")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forsome_predicate(self) -> None:
        binding = Binding(
            ForSome(Variable("X"), Variable("Y"), Equal(Variable("X"), Name("Bar"))),
            {"Bar": Variable("Baz")},
        )
        expected = ForSome(Variable("X"), Variable("Y"), Equal(Variable("X"), Variable("Baz")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_forsome_iterable(self) -> None:
        binding = Binding(
            ForSome(Variable("X"), Name("Y"), Equal(Variable("X"), Variable("Bar"))),
            {"Y": Variable("Baz")},
        )
        expected = ForSome(Variable("X"), Variable("Baz"), Equal(Variable("X"), Variable("Bar")))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_contains_left(self) -> None:
        binding = Binding(Contains(Name("X"), Variable("Y")), {"X": Variable("Baz")},)
        expected = Contains(Variable("Baz"), Variable("Y"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_contains_right(self) -> None:
        binding = Binding(Contains(Variable("X"), Name("Y")), {"Y": Variable("Baz")},)
        expected = Contains(Variable("X"), Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_not_contains_left(self) -> None:
        binding = Binding(NotContains(Name("X"), Name("Y")), {"X": Variable("Baz")},)
        expected = NotContains(Variable("Baz"), Name("Y"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_not_contains_right(self) -> None:
        binding = Binding(NotContains(Name("X"), Name("Y")), {"Y": Variable("Baz")},)
        expected = NotContains(Name("X"), Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_subprogram(self) -> None:
        binding = Binding(
            SubprogramCall(Variable("Sub"), [Variable("A"), Name("B"), Variable("C")]),
            {"B": Variable("Baz")},
        )
        expected = SubprogramCall(Variable("Sub"), [Variable("A"), Variable("Baz"), Variable("C")])
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_field(self) -> None:
        binding = Binding(Field(Name("A"), "fld"), {"A": Variable("Baz")})
        expected = Field(Variable("Baz"), "fld")
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_list_comprehension(self) -> None:
        binding = Binding(
            Comprehension(
                Variable("E"),
                Name("List"),
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
        binding = Binding(Length(Name("A")), {"A": Variable("Baz")})
        expected = Length(Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_simplify_string(self) -> None:
        value = String("Test")
        self.assertEqual(value, value.simplified())

    def test_binding_multiple_bindings(self) -> None:
        binding = Binding(
            Field(Name("A"), "fld"), {"A": Binding(Name("B"), {"B": Variable("Baz")})}
        )
        expected = Field(Variable("Baz"), "fld")
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_multiple_variables(self) -> None:
        binding = Binding(
            SubprogramCall(Variable("Sub"), [Name("A"), Name("A")]), {"A": Variable("Baz")}
        )
        expected = SubprogramCall(Variable("Sub"), [Variable("Baz"), Variable("Baz")])
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_conversion(self) -> None:
        binding = Binding(Conversion(Name("Type"), Name("A")), {"A": Variable("Baz")})
        expected = Conversion(Variable("Type"), Variable("Baz"))
        result = binding.simplified()
        self.assertEqual(result, expected)

    def test_binding_conversion_name_unchanged(self) -> None:
        binding = Binding(Conversion(Name("Type"), Name("A")), {"Type": Variable("Baz")})
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
                                target=StateName("END"), condition=Equal(Name("Undefined"), TRUE)
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
                        Transition(target=StateName("END"), condition=Equal(Name("Defined"), TRUE))
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={"Defined": VariableDeclaration(Name("Some_Type"))},
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
                            target=StateName("END"), condition=Equal(Name("Local"), Name("Global"))
                        )
                    ],
                    declarations={"Local": VariableDeclaration(Name("Some_Type"))},
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Name("Some_Type"))},
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
                        declarations={"Start_Local": VariableDeclaration(Name("Some_Type"))},
                    ),
                    State(
                        name=StateName("STATE"),
                        transitions=[
                            Transition(
                                target=StateName("END"),
                                condition=Equal(Name("Start_Local"), Name("Global")),
                            )
                        ],
                        declarations={"Local": VariableDeclaration(Name("Some_Type"))},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Name("Some_Type"))},
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
                            target=StateName("END"), condition=Equal(Valid(Name("Global")), TRUE)
                        )
                    ],
                    declarations={},
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Name("Boolean"))},
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
                            condition=Equal(Field(Name("Global"), "fld"), TRUE),
                        )
                    ],
                    declarations={},
                ),
                State(name=StateName("END")),
            ],
            declarations={"Global": VariableDeclaration(Name("Boolean"))},
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
                        actions=[Assignment(Name("Undefined"), FALSE)],
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
                        actions=[Assignment(Name("Global"), Name("Undefined"))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Name("Boolean"))},
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
                        actions=[Erase(Name("Undefined"))],
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
                        actions=[Reset(Name("Undefined"))],
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
                                Name("Global"), SubprogramCall(Name("UndefSub"), [Name("Global")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Name("Boolean"))},
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
                        Transition(target=StateName("END"), condition=Equal(Name("Global"), TRUE))
                    ],
                    declarations={},
                    actions=[
                        Assignment(
                            Name("Global"), SubprogramCall(Name("Read"), [Name("Some_Channel")])
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Global": VariableDeclaration(Name("Boolean")),
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
                        Transition(target=StateName("END"), condition=Equal(Name("Success"), TRUE))
                    ],
                    declarations={},
                    actions=[
                        Assignment(
                            Name("Success"),
                            SubprogramCall(Name("Write"), [Name("Some_Channel"), TRUE]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Success": VariableDeclaration(Name("Boolean")),
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
                            Name("Result"),
                            SubprogramCall(Name("Call"), [Name("Some_Channel"), TRUE]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Name("Boolean")),
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
                            Name("Result"),
                            SubprogramCall(Name("Data_Available"), [Name("Some_Channel")]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Name("Boolean")),
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
                        actions=[Assignment(Name("Result"), SubprogramCall(Name("Read"), []))],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Result": VariableDeclaration(Name("Boolean"))},
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
                                Name("Result"), SubprogramCall(Name("Read"), [Name("Undeclared")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Result": VariableDeclaration(Name("Boolean"))},
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
                                Name("Result"), SubprogramCall(Name("Read"), [Name("Result")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Result": VariableDeclaration(Name("Boolean"))},
            )

    def test_call_to_builtin_write_invalid_channel_mode(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel Out_Channel not writable in call to Write"
            " in assignment in action 0 of state START",
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
                                Name("Result"), SubprogramCall(Name("Write"), [Name("Out_Channel")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Name("Boolean")),
                    "Out_Channel": Channel(read=True, write=False),
                },
            )

    def test_call_to_builtin_data_available_invalid_channel_mode(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel Out_Channel not readable in call to Data_Available in "
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
                                Name("Result"),
                                SubprogramCall(Name("Data_Available"), [Name("Out_Channel")]),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Name("Boolean")),
                    "Out_Channel": Channel(read=False, write=True),
                },
            )

    def test_call_to_builtin_read_invalid_channel_mode(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel Channel not readable in call to Read "
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
                                Name("Result"), SubprogramCall(Name("Read"), [Name("Channel")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Name("Boolean")),
                    "Channel": Channel(read=False, write=True),
                },
            )

    def test_call_to_builtin_call_channel_not_readable(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel Channel not readable in call to Call in "
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
                                Name("Result"), SubprogramCall(Name("Call"), [Name("Channel")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Name("Boolean")),
                    "Channel": Channel(read=False, write=True),
                },
            )

    def test_call_to_builtin_call_channel_not_writable(self) -> None:
        with self.assertRaisesRegex(
            ModelError,
            "^channel Channel not writable in call to Call"
            " in assignment in action 0 of state START",
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
                                Name("Result"), SubprogramCall(Name("Call"), [Name("Channel")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Name("Boolean")),
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
                        Transition(target=StateName("END"), condition=Equal(Name("Result"), TRUE))
                    ],
                    declarations={},
                    actions=[Assignment(Name("Result"), SubprogramCall(Name("SubProg"), []))],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Name("Boolean")),
                "SubProg": Subprogram([], Name("Boolean")),
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
                                Name("Result"), SubprogramCall(Name("SubProg"), [Name("Undefined")])
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={
                    "Result": VariableDeclaration(Name("Boolean")),
                    "SubProg": Subprogram([], Name("Boolean")),
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
                declarations={"Read": Subprogram([], Name("Boolean"))},
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
                declarations={"Call": VariableDeclaration(Name("Boolean"))},
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
                declarations={"Data_Available": Renames(Name("Boolean"), Name("Foo.Bar"))},
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
                                target=StateName("END"), condition=Equal(Name("Global"), TRUE)
                            )
                        ],
                        declarations={"Global": VariableDeclaration(Name("Boolean"))},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Global": VariableDeclaration(Name("Boolean"))},
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
                declarations={"Global": VariableDeclaration(Name("Boolean"))},
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
                        declarations={"Data": VariableDeclaration(Name("Boolean"))},
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
                            Transition(target=StateName("END"), condition=Equal(Name("Ren"), TRUE))
                        ],
                        declarations={},
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Ren": Renames(Name("Boolean"), Name("Foo"))},
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
                            Name("Result"),
                            Binding(
                                SubprogramCall(Name("SubProg"), [Length(Name("Bound"))]),
                                {"Bound": Name("Variable")},
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "Result": VariableDeclaration(Name("Boolean")),
                "Variable": VariableDeclaration(Name("Boolean")),
                "SubProg": Subprogram([], Name("Boolean")),
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
                                Name("E"), Name("List"), Equal(Field(Name("E"), "Tag"), Number(42))
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={"List": VariableDeclaration(Name("Foo"))},
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
                            Name("List"),
                            SubprogramCall(Name("Append"), [Name("List"), Name("Element")]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "List": VariableDeclaration(Name("List_Type")),
                "Element": VariableDeclaration(Name("Element_Type")),
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
                            Name("List"),
                            SubprogramCall(Name("Extend"), [Name("List"), Name("Element")]),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={
                "List": VariableDeclaration(Name("List_Type")),
                "Element": VariableDeclaration(Name("Element_Type")),
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
                                Name("Data"),
                                MessageAggregate(
                                    Name("Data_Type"), {"Foo": Name("Data"), "Bar": Name("Undef")}
                                ),
                            )
                        ],
                    ),
                    State(name=StateName("END")),
                ],
                declarations={"Data": VariableDeclaration(Name("Data_Type"))},
            )

    def test_comprehension(self) -> None:  # pylint: disable=no-self-use
        StateMachine(
            name="fsm",
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(
                    name=StateName("START"),
                    transitions=[Transition(target=StateName("END"))],
                    actions=[
                        Assignment(
                            Name("Input"),
                            Comprehension(
                                Name("K"),
                                Name("Input"),
                                Field(Name("K"), "Data"),
                                Equal(Field(Name("K"), "Valid"), TRUE),
                            ),
                        )
                    ],
                ),
                State(name=StateName("END")),
            ],
            declarations={"Input": VariableDeclaration(Name("Foo"))},
        )
