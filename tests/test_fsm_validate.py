import unittest

from rflx.expression import TRUE, Equal, Variable, VariableDeclaration
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
)
from rflx.model import ModelError


class TestFSM(unittest.TestCase):
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
