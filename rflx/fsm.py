from typing import Dict, Iterable, Optional

import yaml

from rflx.model import Base, ModelError


class StateName(Base):
    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name


class Transition(Base):
    def __init__(self, target: StateName):
        self.target = target


class State(Base):
    def __init__(self, name: StateName, transitions: Optional[Iterable[Transition]] = None):
        self.__name = name
        self.__transitions = transitions or []

    @property
    def name(self) -> StateName:
        return self.__name

    @property
    def transitions(self) -> Iterable[Transition]:
        return self.__transitions or []


class StateMachine(Base):
    def __init__(self, initial: StateName, final: StateName, states: Iterable[State]):
        self.__initial = initial
        self.__final = final
        self.__states = states

        if not states:
            raise ModelError("empty states")

    def __validate_initial_state(self, name: str) -> None:
        states = [s.name for s in self.__states]
        if self.__initial not in states:
            raise ModelError(f'initial state "{self.__initial.name}" does not exist in "{name}"')
        if self.__final not in states:
            raise ModelError(f'final state "{self.__final.name}" does not exist in "{name}"')
        for s in self.__states:
            for t in s.transitions:
                if t.target not in states:
                    raise ModelError(
                        f'transition from state "{s.name.name}" to non-existent state'
                        f' "{t.target.name}" in "{name}"'
                    )

    def validate(self, name: str) -> None:
        self.__validate_initial_state(name)


class FSM:
    def __init__(self) -> None:
        self.__fsms: Dict[str, StateMachine] = {}

    def __parse(self, name: str, doc: Dict) -> None:
        if "initial" not in doc:
            raise ModelError("missing initial state")
        if "final" not in doc:
            raise ModelError("missing final state")
        if "states" not in doc:
            raise ModelError("missing states")
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
        for f, v in self.__fsms.items():
            v.validate(f)

    def parse(self, name: str, filename: str) -> None:
        with open(filename, "r") as data:
            self.__parse(name, yaml.safe_load(data))

    def parse_string(self, name: str, string: str) -> None:
        self.__parse(name, yaml.safe_load(string))

    @property
    def fsms(self) -> Dict[str, StateMachine]:
        return self.__fsms
