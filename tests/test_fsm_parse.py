import unittest

from rflx.fsm_parser import FSMParser


class TestFSM(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

    @classmethod
    def test_simple_equation(cls) -> None:
        FSMParser.condition().parseString("Foo.Bar = abc")
