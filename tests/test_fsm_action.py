import unittest

from rflx.expression import Variable
from rflx.fsm_expression import SubprogramCall
from rflx.fsm_parser import FSMParser
from rflx.statement import Assignment


class TestFSM(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_simple_assignment(self) -> None:
        result = FSMParser.action().parseString("Foo := Bar")[0]
        self.assertEqual(result, Assignment(Variable("Foo"), Variable("Bar")))

    def test_simple_subprogram_call(self) -> None:
        result = FSMParser.action().parseString("Sub (Arg)")[0]
        expected = SubprogramCall(Variable("Sub"), [Variable("Arg")])
        self.assertEqual(result, expected)

    def test_list_append(self) -> None:
        result = FSMParser.action().parseString("Extensions_List'Append (Foo)")[0]
        expected = Assignment(
            Variable("Extensions_List"),
            SubprogramCall(Variable("Append"), [Variable("Extensions_List"), Variable("Foo")]),
        )
        self.assertEqual(result, expected)
