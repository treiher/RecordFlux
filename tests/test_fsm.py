import unittest

from rflx.fsm import FSM, State, StateMachine, StateName, Transition


class TestFSM(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None  # pylint: disable=invalid-name

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
            initial=StateName("START"),
            final=StateName("END"),
            states=[
                State(name=StateName("START"), transitions=[Transition(target=StateName("END"))]),
                State(name=StateName("END")),
            ],
        )
        self.assertEqual(f.fsms["fsm"], expected)
