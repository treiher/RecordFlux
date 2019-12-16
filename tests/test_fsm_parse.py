import unittest

from rflx.expression import And, Equal, NotEqual, Or, Variable
from rflx.fsm_expression import Valid
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

    def test_disjunction(self) -> None:
        result = FSMParser.condition().parseString("Foo = Bar or Bar /= Baz")[0]
        self.assertEqual(
            result,
            Or(Equal(Variable("Foo"), Variable("Bar")), NotEqual(Variable("Bar"), Variable("Baz"))),
        )
