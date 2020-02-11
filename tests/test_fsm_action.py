import unittest

from rflx.expression import Variable
from rflx.fsm_parser import FSMParser
from rflx.statement import Assignment


class TestFSM(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_simple_assignment(self) -> None:
        result = FSMParser.action().parseString("Foo := Bar")[0]
        self.assertEqual(result, Assignment(Variable("Foo"), Variable("Bar")))
