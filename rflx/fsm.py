from typing import Dict, Iterable, List, Optional

import yaml
from pyparsing import Keyword

from rflx.expression import FALSE, TRUE, Equal, Expr, Variable
from rflx.model import Element, ModelError
from rflx.parser import Parser


class StateName(Element):
    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name


class Transition(Element):
    def __init__(self, target: StateName, condition: Expr = TRUE):
        self.__target = target
        self.__condition = condition

    @property
    def target(self) -> StateName:
        return self.__target


class State(Element):
    def __init__(self, name: StateName, transitions: Optional[Iterable[Transition]] = None):
        self.__name = name
        self.__transitions = transitions or []

    @property
    def name(self) -> StateName:
        return self.__name

    @property
    def transitions(self) -> Iterable[Transition]:
        return self.__transitions or []


class StateMachine(Element):
    def __init__(self, name: str, initial: StateName, final: StateName, states: Iterable[State]):
        self.__name = name
        self.__initial = initial
        self.__final = final
        self.__states = states

        if not states:
            raise ModelError("empty states")

        self.__validate_state_existence()
        self.__validate_duplicate_states()
        self.__validate_state_reachability()

    def __validate_state_existence(self) -> None:
        state_names = [s.name for s in self.__states]
        if self.__initial not in state_names:
            raise ModelError(
                f'initial state "{self.__initial.name}" does not exist in' f' "{self.__name}"'
            )
        if self.__final not in state_names:
            raise ModelError(
                f'final state "{self.__final.name}" does not exist in' f' "{self.__name}"'
            )
        for s in self.__states:
            for t in s.transitions:
                if t.target not in state_names:
                    raise ModelError(
                        f'transition from state "{s.name.name}" to non-existent state'
                        f' "{t.target.name}" in "{self.__name}"'
                    )

    def __validate_duplicate_states(self) -> None:
        state_names = [s.name for s in self.__states]
        seen: Dict[str, int] = {}
        duplicates: List[str] = []
        for n in [x.name for x in state_names]:
            if n not in seen:
                seen[n] = 1
            else:
                if seen[n] == 1:
                    duplicates.append(n)
                seen[n] += 1

        if duplicates:
            raise ModelError("duplicate states {dups}".format(dups=", ".join(sorted(duplicates))))

    def __validate_state_reachability(self) -> None:
        inputs: Dict[str, List[str]] = {}
        for s in self.__states:
            for t in s.transitions:
                if t.target.name in inputs:
                    inputs[t.target.name].append(s.name.name)
                else:
                    inputs[t.target.name] = [s.name.name]
        unreachable = [
            s.name.name
            for s in self.__states
            if s.name != self.__initial and s.name.name not in inputs
        ]
        if unreachable:
            raise ModelError("unreachable states {states}".format(states=", ".join(unreachable)))

        detached = [
            s.name.name for s in self.__states if s.name != self.__final and not s.transitions
        ]
        if detached:
            raise ModelError("detached states {states}".format(states=", ".join(detached)))


class FSM:
    def __init__(self) -> None:
        self.__fsms: List[StateMachine] = []

    @classmethod
    def logical_equation(cls):
        result = Parser.identifier() + Keyword("=") + Parser.boolean_literal()
        return result.setParseAction(
            lambda t: Equal(Variable(t[0]), TRUE if t[2] == "True" else FALSE)
        )

    def __parse(self, name: str, doc: Dict) -> None:
        if "initial" not in doc:
            raise ModelError("missing initial state")
        if "final" not in doc:
            raise ModelError("missing final state")
        if "states" not in doc:
            raise ModelError("missing states")

        states: List[State] = []
        for s in doc["states"]:
            transitions: Optional[List[Transitions]] = []
            if "transitions" in s:
                for index, t in enumerate(s["transitions"]):
                    if "condition" in t:
                        try:
                            condition = FSM.logical_equation().parseString(t["condition"])[0]
                        except:
                            sname = s["name"]
                            tname = t["target"]
                            raise ModelError(
                                f'error parsing condition {index} from state "{sname}" to "{tname}"'
                            )
                    else:
                        condition = TRUE
                    transitions.append(
                        Transition(target=StateName(t["target"]), condition=condition)
                    )
            states.append(State(name=StateName(s["name"]), transitions=transitions))

        fsm = StateMachine(
            name=name,
            initial=StateName(doc["initial"]),
            final=StateName(doc["final"]),
            states=states,
        )
        self.__fsms.append(fsm)

    def parse(self, name: str, filename: str) -> None:
        with open(filename, "r") as data:
            self.__parse(name, yaml.safe_load(data))

    def parse_string(self, name: str, string: str) -> None:
        self.__parse(name, yaml.safe_load(string))

    @property
    def fsms(self) -> List[StateMachine]:
        return self.__fsms
