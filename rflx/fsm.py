from typing import Any, Dict, Iterable, List, Optional

import yaml
from pyparsing import ParseFatalException

from rflx.expression import TRUE, Expr
from rflx.fsm_declaration import Channel, Declaration
from rflx.fsm_parser import FSMParser
from rflx.model import Element, ModelError
from rflx.statement import Statement


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
    def __init__(
        self,
        name: StateName,
        transitions: Optional[Iterable[Transition]] = None,
        actions: Optional[Iterable[Statement]] = None,
    ):
        self.__name = name
        self.__transitions = transitions or []
        self.__actions = actions or []

    @property
    def name(self) -> StateName:
        return self.__name

    @property
    def transitions(self) -> Iterable[Transition]:
        return self.__transitions or []


class StateMachine(Element):
    def __init__(
        self,
        name: str,
        initial: StateName,
        final: StateName,
        states: Iterable[State],
        declarations: Dict[str, Declaration],
    ):  # pylint: disable=too-many-arguments
        self.__name = name
        self.__initial = initial
        self.__final = final
        self.__states = states
        self.__declarations = declarations

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
    def __parse_functions(cls, doc: Dict[str, Any], result: Dict[str, Declaration]) -> None:
        if "functions" not in doc:
            return
        for index, f in enumerate(doc["functions"]):
            try:
                name, declaration = FSMParser.declaration().parseString(f)[0]
            except Exception as e:
                raise ModelError(f"error parsing global function declaration {index} ({e})")
            result[name] = declaration

    @classmethod
    def __parse_variables(cls, doc: Dict[str, Any], result: Dict[str, Declaration]) -> None:
        if "variables" not in doc:
            return
        for index, f in enumerate(doc["variables"]):
            try:
                name, declaration = FSMParser.declaration().parseString(f)[0]
            except Exception as e:
                raise ModelError(f"error parsing global variable declaration {index} ({e})")
            result[name] = declaration

    @classmethod
    def __parse_types(cls, doc: Dict[str, Any], result: Dict[str, Declaration]) -> None:
        if "types" not in doc:
            return
        for index, f in enumerate(doc["types"]):
            try:
                name, declaration = FSMParser.declaration().parseString(f)[0]
            except Exception as e:
                raise ModelError(f"error parsing private variable declaration {index} ({e})")
            result[name] = declaration

    @classmethod
    def __parse_channels(cls, doc: Dict[str, Any], result: Dict[str, Declaration]) -> None:
        if "channels" not in doc:
            return
        for index, f in enumerate(doc["channels"]):
            if "name" not in f:
                raise ModelError(f"Channel {index} has no name")
            if "mode" not in f:
                raise ModelError(f"Channel {f['name']} has no mode")
            modes = {
                "Read": {"read": True, "write": False},
                "Write": {"read": False, "write": True},
                "Read_Write": {"read": True, "write": True},
            }
            mode = f["mode"]
            try:
                result[f["name"]] = Channel(modes[mode]["read"], modes[mode]["write"])
            except KeyError:
                raise ModelError(f"Channel {f['name']} has invalid mode {mode}")

    @classmethod
    def __parse_declarations(cls, doc: Dict[str, Any]) -> Dict[str, Declaration]:
        result: Dict[str, Declaration] = {}
        cls.__parse_functions(doc, result)
        cls.__parse_variables(doc, result)
        cls.__parse_types(doc, result)
        cls.__parse_channels(doc, result)
        return result

    @classmethod
    def __parse_transitions(cls, state: Dict) -> List[Transition]:
        transitions: List[Transition] = []
        sname = state["name"]
        if "transitions" in state:
            for index, t in enumerate(state["transitions"]):
                rest = t.keys() - ["condition", "target", "doc"]
                if rest:
                    elements = ", ".join(sorted(rest))
                    raise ModelError(
                        f"unexpected elements [{elements}] in transition {index} state {sname}"
                    )
                condition = TRUE
                if "condition" in t:
                    try:
                        condition = FSMParser.expression().parseString(t["condition"])[0]
                    except ParseFatalException as e:
                        tname = t["target"]
                        raise ModelError(
                            f"error parsing condition {index} from state "
                            f'"{sname}" to "{tname}" ({e})'
                        )
                transitions.append(Transition(target=StateName(t["target"]), condition=condition))
        return transitions

    def __parse(self, name: str, doc: Dict[str, Any]) -> None:
        if "initial" not in doc:
            raise ModelError("missing initial state")
        if "final" not in doc:
            raise ModelError("missing final state")
        if "states" not in doc:
            raise ModelError("missing states")

        rest = set(doc.keys()) - set(
            ["channels", "variables", "functions", "initial", "final", "states", "renames", "types"]
        )
        if rest:
            raise ModelError("unexpected elements [{}]".format(", ".join(sorted(rest))))

        states: List[State] = []
        for s in doc["states"]:
            state = s["name"]
            rest = s.keys() - ["name", "actions", "transitions", "variables", "doc"]
            if rest:
                elements = ", ".join(sorted(rest))
                raise ModelError(f"unexpected elements [{elements}] in state {state}")
            transitions: List[Transition] = []
            transitions = self.__parse_transitions(s)
            actions: List[Statement] = []
            if "actions" in s and s["actions"]:
                for index, a in enumerate(s["actions"]):
                    try:
                        actions.append(FSMParser.action().parseString(a)[0])
                    except Exception as e:
                        sname = s["name"]
                        raise ModelError(f"error parsing action {index} of state {sname} ({e})")
            states.append(
                State(name=StateName(s["name"]), transitions=transitions, actions=actions)
            )

        fsm = StateMachine(
            name=name,
            initial=StateName(doc["initial"]),
            final=StateName(doc["final"]),
            states=states,
            declarations=self.__parse_declarations(doc),
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
