from typing import Dict, Iterable, Optional

import yaml

from rflx.model import Element


class StateName(Element):
    def __init__(self, name: str):
        self.name = name


class Transition(Element):
    def __init__(self, target: StateName):
        self.target = target


class State(Element):
    def __init__(self, name: StateName, transitions: Optional[Iterable[Transition]] = None):
        self.name = name
        self.transitions = transitions or []


class StateMachine(Element):
    def __init__(self, initial: StateName, final: StateName, states: Iterable[State]):
        self.initial = initial
        self.final = final
        self.states = states


class FSM:
    def __init__(self) -> None:
        self.__fsms: Dict[str, StateMachine] = {}

    def parse_string(self, name: str, string: str) -> None:
        doc = yaml.load(string)
        self.__fsms[name] = StateMachine(
            initial=StateName(doc["initial"]),
            final=StateName(doc["final"]),
            states=[
                State(
                    StateName(s["name"]),
                    [Transition(StateName(t["target"])) for t in s["transitions"]]
                    if "transitions" in s
                    else None,
                )
                for s in doc["states"]
            ],
        )

    @property
    def fsms(self) -> Dict[str, StateMachine]:
        return self.__fsms
