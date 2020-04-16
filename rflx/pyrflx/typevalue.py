from abc import ABC, abstractmethod
from typing import Any, Dict, List, Mapping, Sequence, Tuple, Union

from rflx.common import generic_repr
from rflx.expression import (
    FALSE,
    TRUE,
    UNDEFINED,
    Add,
    Expr,
    First,
    Last,
    Length,
    Name,
    Sub,
    Variable,
)
from rflx.model import (
    FINAL,
    INITIAL,
    Array,
    Enumeration,
    Field,
    Integer,
    Message,
    Number,
    Opaque,
    Scalar,
    Type,
)
from rflx.pyrflx.bitstring import Bitstring


class NotInitializedError(Exception):
    pass


class TypeValue(ABC):

    _value: Any = None

    def __init__(self, vtype: Type) -> None:
        self._type = vtype

    def __repr__(self) -> str:
        return generic_repr(self.__class__.__name__, self.__dict__)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self._value == other._value and self._type == other._type
        return NotImplemented

    def equal_type(self, other: Type) -> bool:
        return isinstance(self._type, type(other))

    @property
    def initialized(self) -> bool:
        return self._value is not None

    def _raise_initialized(self) -> None:
        if not self.initialized:
            raise NotInitializedError("value not initialized")

    def clear(self) -> None:
        self._value = None

    @abstractmethod
    def assign(self, value: Any, check: bool = True) -> None:
        raise NotImplementedError

    @abstractmethod
    def parse(self, value: Bitstring) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def bitstring(self) -> Bitstring:
        raise NotImplementedError

    @property
    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def value(self) -> Any:
        raise NotImplementedError

    @property
    @abstractmethod
    def accepted_type(self) -> type:
        raise NotImplementedError

    @property
    @abstractmethod
    def literals(self) -> Mapping[Name, Expr]:
        raise NotImplementedError

    @classmethod
    def construct(cls, vtype: Type) -> "TypeValue":

        if isinstance(vtype, Integer):
            return IntegerValue(vtype)
        if isinstance(vtype, Enumeration):
            return EnumValue(vtype)
        if isinstance(vtype, Opaque):
            return OpaqueValue(vtype)
        if isinstance(vtype, Array):
            return ArrayValue(vtype)
        if isinstance(vtype, Message):
            return MessageValue(vtype)
        raise ValueError("cannot construct unknown type: " + type(vtype).__name__)


class ScalarValue(TypeValue):

    _type: Scalar

    def __init__(self, vtype: Scalar) -> None:
        super().__init__(vtype)

    @property
    @abstractmethod
    def expr(self) -> Expr:
        return NotImplemented

    @property
    @abstractmethod
    def literals(self) -> Mapping[Name, Expr]:
        raise NotImplementedError

    @property
    def size(self) -> int:
        size_expr = self._type.size.simplified()
        assert isinstance(size_expr, Number)
        return size_expr.value


class IntegerValue(ScalarValue):

    _value: int
    _type: Integer

    def __init__(self, vtype: Integer) -> None:
        super().__init__(vtype)

    @property
    def _first(self) -> int:
        first = self._type.first.simplified()
        assert isinstance(first, Number)
        return first.value

    @property
    def _last(self) -> int:
        last = self._type.last.simplified()
        assert isinstance(last, Number)
        return last.value

    def assign(self, value: int, check: bool = True) -> None:
        if (
            self._type.constraints("__VALUE__", check).simplified(
                {Variable("__VALUE__"): Number(value)}
            )
            != TRUE
        ):
            raise ValueError(f"value {value} not in type range {self._first} .. {self._last}")
        self._value = value

    def parse(self, value: Bitstring) -> None:
        self.assign(int(value))

    @property
    def expr(self) -> Number:
        self._raise_initialized()
        return Number(self._value)

    @property
    def value(self) -> int:
        self._raise_initialized()
        return self._value

    @property
    def bitstring(self) -> Bitstring:
        self._raise_initialized()
        return Bitstring(format(self._value, f"0{self.size}b"))

    @property
    def accepted_type(self) -> type:
        return int

    @property
    def literals(self) -> Mapping[Name, Expr]:
        return {}


class EnumValue(ScalarValue):

    _value: str
    _type: Enumeration

    def __init__(self, vtype: Enumeration) -> None:
        super().__init__(vtype)

    def assign(self, value: str, check: bool = True) -> None:
        if value not in self._type.literals:
            raise KeyError(f"{value} is not a valid enum value")
        assert (
            self._type.constraints("__VALUE__", check).simplified(
                {
                    **{Variable(k): v for k, v in self._type.literals.items()},
                    **{Variable("__VALUE__"): self._type.literals[value]},
                }
            )
            == TRUE
        )
        self._value = value

    def parse(self, value: Bitstring) -> None:

        value_as_int: int = int(value)
        if not Number(value_as_int) in self.literals.values():
            raise KeyError(f"Number {value_as_int} is not a valid enum value")

        for k, v in self.literals.items():
            if v == Number(value_as_int):
                self._value = str(k.name)

    @property
    def value(self) -> str:
        self._raise_initialized()
        return self._value

    @property
    def expr(self) -> Variable:
        self._raise_initialized()
        return Variable(self._value)

    @property
    def bitstring(self) -> Bitstring:
        self._raise_initialized()
        assert isinstance(self._type, Enumeration)
        return Bitstring(format(self._type.literals[self._value].value, f"0{self.size}b"))

    @property
    def accepted_type(self) -> type:
        return str

    @property
    def literals(self) -> Mapping[Name, Expr]:
        return {Variable(k): v for k, v in self._type.literals.items()}


class OpaqueValue(TypeValue):

    _value: bytes

    def __init__(self, vtype: Opaque) -> None:
        super().__init__(vtype)

    def assign(self, value: bytes, check: bool = True) -> None:
        self._value = value

    def parse(self, value: Bitstring) -> None:
        self._value = bytes(value)

    @property
    def size(self) -> int:
        self._raise_initialized()
        return len(self._value) * 8

    @property
    def value(self) -> bytes:
        self._raise_initialized()
        return self._value

    @property
    def bitstring(self) -> Bitstring:
        self._raise_initialized()
        return Bitstring(format(int.from_bytes(self._value, "big"), f"0{self.size}b"))

    @property
    def accepted_type(self) -> type:
        return bytes

    @property
    def literals(self) -> Mapping[Name, Expr]:
        return {}


class ArrayValue(TypeValue):

    _value: List[TypeValue]

    def __init__(self, vtype: Array) -> None:
        super().__init__(vtype)
        self._element_type = vtype.element_type
        self._is_message_array = isinstance(self._element_type, Message)
        self._value = []

    def assign(self, value: List[TypeValue], check: bool = True) -> None:

        for v in value:
            if self._is_message_array:
                if isinstance(v, MessageValue):
                    assert isinstance(self._element_type, Message)
                    if not v.equal_model(self._element_type):
                        raise ValueError(
                            f'cannot assign "{v.name}" to an array of "{self._element_type.name}"'
                        )
                    if not v.valid_message:
                        raise ValueError(
                            f'cannot assign message "{v.name}" to array of messages: '
                            f"all messages must be valid"
                        )
                else:
                    raise ValueError(
                        f"cannot assign {type(v)} to an array of {type(self._element_type)}"
                    )
            else:
                if isinstance(v, MessageValue) or not v.equal_type(self._element_type):
                    raise ValueError(
                        f"cannot assign {type(v)} to an array of {type(self._element_type)}"
                    )

        self._value = value

    def parse(self, value: Bitstring) -> None:

        if self._is_message_array:

            while len(value) != 0:

                nested_message = TypeValue.construct(self._element_type)
                assert isinstance(nested_message, MessageValue)
                try:
                    nested_message.parse(value)
                except (IndexError, ValueError, KeyError) as e:
                    raise ValueError(
                        f"cannot parse nested messages in array of type "
                        f"{self._element_type.full_name}: {e}"
                    )
                if nested_message.valid_message:
                    self._value.append(nested_message)
                else:
                    raise ValueError(
                        f"cannot append to array: message is invalid {nested_message.name}"
                    )
                value = value[len(nested_message.bitstring) :]

        elif isinstance(self._element_type, Scalar):

            value_str = str(value)
            type_size = self._element_type.size
            assert isinstance(type_size, Number)
            type_size_int = type_size.value

            while len(value_str) != 0:
                nested_value = TypeValue.construct(self._element_type)
                nested_value.parse(Bitstring(value_str[:type_size_int]))
                self._value.append(nested_value)
                value_str = value_str[type_size_int:]
        else:
            raise NotImplementedError(f"Arrays of {self._element_type} currently not supported")

    @property
    def size(self) -> int:
        self._raise_initialized()
        return len(self.bitstring)

    @property
    def value(self) -> List[TypeValue]:
        self._raise_initialized()
        return self._value

    @property
    def bitstring(self) -> Bitstring:
        self._raise_initialized()
        bits: List[str] = [str(element.bitstring) for element in self._value]
        return Bitstring(str.join("", bits))

    @property
    def accepted_type(self) -> type:
        return list

    @property
    def literals(self) -> Mapping[Name, Expr]:
        return {}


class MessageValue(TypeValue):
    def __init__(self, message_model: Message) -> None:
        super().__init__(message_model)
        self._model = message_model
        self._fields: Dict[str, MessageValue.Field] = {
            f.name: self.Field(TypeValue.construct(self._model.types[f]))
            for f in self._model.fields
        }
        self.__type_literals: Mapping[Name, Expr] = {}
        self._last_field: str = self._next_field(INITIAL.name)

        for t in [f.typeval.literals for f in self._fields.values()]:
            self.__type_literals = {**self.__type_literals, **t}
        initial = self.Field(OpaqueValue(Opaque()))
        initial.first = Number(0)
        initial.length = Number(0)
        self._fields[INITIAL.name] = initial
        self._preset_fields(INITIAL.name)

    def __copy__(self) -> "MessageValue":
        return MessageValue(self._model)

    def __repr__(self) -> str:
        return generic_repr(self.__class__.__name__, self.__dict__)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self._fields == other._fields and self._model == other._model
        return NotImplemented

    def equal_model(self, other: Message) -> bool:
        return self.name == other.name

    def _next_field(self, fld: str) -> str:
        if fld == FINAL.name:
            return ""
        if fld == INITIAL.name:
            return self._model.outgoing(INITIAL)[0].target.name

        for l in self._model.outgoing(Field(fld)):
            if self.__simplified(l.condition) == TRUE:
                return l.target.name
        return ""

    def _prev_field(self, fld: str) -> str:
        if fld == INITIAL.name:
            return ""
        for l in self._model.incoming(Field(fld)):
            if self.__simplified(l.condition) == TRUE:
                return l.source.name
        return ""

    def _get_length_unchecked(self, fld: str) -> Expr:
        for l in self._model.incoming(Field(fld)):
            if self.__simplified(l.condition) == TRUE and l.length != UNDEFINED:
                return self.__simplified(l.length)

        typeval = self._fields[fld].typeval
        if isinstance(typeval, ScalarValue):
            return Number(typeval.size)
        return UNDEFINED

    def _has_length(self, fld: str) -> bool:
        return isinstance(self._get_length_unchecked(fld), Number)

    def _get_length(self, fld: str) -> Number:
        length = self._get_length_unchecked(fld)
        assert isinstance(length, Number)
        return length

    def _get_first_unchecked(self, fld: str) -> Expr:
        for l in self._model.incoming(Field(fld)):
            if self.__simplified(l.condition) == TRUE and l.first != UNDEFINED:
                return self.__simplified(l.first)
        prv = self._prev_field(fld)
        if prv:
            return self.__simplified(Add(self._fields[prv].first, self._fields[prv].length))
        return UNDEFINED

    def _has_first(self, fld: str) -> bool:
        return isinstance(self._get_first_unchecked(fld), Number)

    def _get_first(self, fld: str) -> Number:
        first = self._get_first_unchecked(fld)
        assert isinstance(first, Number)
        return first

    @property
    def name(self) -> str:
        return self._model.name

    @property
    def accepted_type(self) -> type:
        return bytes

    @property
    def literals(self) -> Mapping[Name, Expr]:
        return {}

    @property
    def size(self) -> int:
        return len(self.bitstring)

    def assign(self, value: bytes, check: bool = True) -> None:

        msg_as_bitstr: Bitstring = Bitstring().from_bytes(value)
        self.parse(msg_as_bitstr)

    def parse(self, value: Bitstring) -> None:

        current_field_name = self._next_field(INITIAL.name)
        last_field_first_in_bitstr = current_field_first_in_bitstr = 0
        current_field_length = 0

        def get_current_pos_in_bitstr(field_name: str) -> int:

            # if the previous node is a virtual node i.e. has the same first as the current node
            # set the current pos in bitstring back to the first position of its predecessor
            this_first = self._fields[field_name].first
            prev_first = self._fields[self._prev_field(field_name)].first

            if not isinstance(prev_first, Number) or not isinstance(this_first, Number):
                return current_field_first_in_bitstr

            return (
                last_field_first_in_bitstr
                if prev_first.value == this_first.value
                else current_field_first_in_bitstr
            )

        def set_field_without_length(field_name: str, field: MessageValue.Field) -> Tuple[int, int]:

            last_pos_in_bitstr = current_pos_in_bitstring = get_current_pos_in_bitstr(field_name)
            assert isinstance(field.typeval, OpaqueValue)
            field.first = self._get_first(field_name)
            self.set(field_name, value[current_pos_in_bitstring:])
            field.length = Number(field.typeval.size)

            return last_pos_in_bitstr, current_pos_in_bitstring

        def set_field_with_length(field_name: str, field_length: int) -> Tuple[int, int]:

            last_pos_in_bitstr = current_pos_in_bitstring = get_current_pos_in_bitstr(field_name)

            if field_length < 8 or field_length % 8 == 0:

                self.set(
                    field_name,
                    value[current_pos_in_bitstring : current_pos_in_bitstring + field_length],
                )
                current_pos_in_bitstring += field_length

            else:
                bytes_used_for_field = field_length // 8 + 1
                first_pos = current_pos_in_bitstring
                field_bits = Bitstring()

                for _ in range(bytes_used_for_field - 1):
                    field_bits += value[current_pos_in_bitstring : current_pos_in_bitstring + 8]
                    current_pos_in_bitstring += 8

                k = field_length // bytes_used_for_field + 1
                field_bits += value[current_pos_in_bitstring + 8 - k : first_pos + field_length]
                current_pos_in_bitstring = first_pos + field_length
                self.set(field_name, field_bits)

            return last_pos_in_bitstr, current_pos_in_bitstring

        while current_field_name != FINAL.name and (
            current_field_first_in_bitstr + current_field_length
        ) <= len(value):

            current_field = self._fields[current_field_name]

            if isinstance(current_field.typeval, OpaqueValue) and not self._has_length(
                current_field_name
            ):

                (
                    last_field_first_in_bitstr,
                    current_field_first_in_bitstr,
                ) = set_field_without_length(current_field_name, current_field)

            elif self._has_length(current_field_name):
                assert isinstance(current_field.length, Number)
                current_field_length = current_field.length.value
                try:
                    (
                        last_field_first_in_bitstr,
                        current_field_first_in_bitstr,
                    ) = set_field_with_length(current_field_name, current_field_length)
                except IndexError:
                    raise IndexError(
                        f"Bitstring representing the message is too short - "
                        f"stopped while parsing field: {current_field_name}"
                    )
            else:
                if current_field_length == 0:
                    raise ValueError("Field cannot have a length of zero")
                if not self._has_length(current_field_name):
                    raise ValueError("Field does not have a length and is not Opaque")

            current_field_name = self._next_field(current_field_name)

    def set(self, fld: str, value: Union[bytes, int, str, Sequence[TypeValue], Bitstring]) -> None:

        if fld in self.accessible_fields:

            field = self._fields[fld]

            if isinstance(value, Bitstring):
                field.first = self._get_first(fld)
                if isinstance(field.typeval, OpaqueValue) and not self._has_length(fld):
                    field.typeval.parse(value)
                    field.length = Number(field.typeval.size)
                else:
                    field.length = self._get_length(fld)
                    field.typeval.parse(value)
            elif isinstance(value, field.typeval.accepted_type):
                field.first = self._get_first(fld)
                if isinstance(field.typeval, OpaqueValue) and not self._has_length(fld):
                    assert isinstance(value, bytes)
                    field.typeval.assign(value)
                    field.length = Number(field.typeval.size)
                else:
                    field.length = self._get_length(fld)
                    field.typeval.assign(value)
            else:
                raise TypeError(
                    f"cannot assign different types: {field.typeval.accepted_type.__name__}"
                    f" != {type(value).__name__}"
                )

        else:
            raise KeyError(f"cannot access field {fld}")

        if all([self.__simplified(o.condition) == FALSE for o in self._model.outgoing(Field(fld))]):
            self._fields[fld].typeval.clear()
            raise ValueError("value does not fulfill field condition")

        if isinstance(field.typeval, OpaqueValue) and field.typeval.size != field.length.value:
            flength = field.typeval.size
            field.typeval.clear()
            raise ValueError(f"invalid data length: {field.length.value} != {flength}")

        if isinstance(field.typeval, ArrayValue) and field.typeval.size != field.length.value:
            flength = field.typeval.size
            field.typeval.clear()
            raise ValueError(f"invalid data length: {field.length.value} != {flength}")

        self._preset_fields(fld)

    def _preset_fields(self, fld: str) -> None:

        nxt = self._next_field(fld)
        while nxt and nxt != FINAL.name:
            field = self._fields[nxt]

            if not self._has_first(nxt) or not self._has_length(nxt):
                break

            field.first = self._get_first(nxt)
            field.length = self._get_length(nxt)
            if (
                field.set
                and isinstance(field.typeval, OpaqueValue)
                and field.typeval.size != field.length.value
            ):
                field.first = UNDEFINED
                field.length = UNDEFINED
                field.typeval.clear()
                break

            self._last_field = nxt
            nxt = self._next_field(nxt)

    def get(self, fld: str) -> Any:
        if fld not in self.valid_fields:
            raise ValueError(f"field {fld} not valid")
        return self._fields[fld].typeval.value

    @property
    def bitstring(self) -> Bitstring:
        bits = ""
        field = self._next_field(INITIAL.name)
        while field and field != FINAL.name:
            field_val = self._fields[field]
            if (
                not field_val.set
                or not isinstance(field_val.first, Number)
                or not field_val.first.value <= len(bits)
            ):
                break
            bits = bits[: field_val.first.value] + str(self._fields[field].typeval.bitstring)
            field = self._next_field(field)
        if len(bits) % 8:
            raise ValueError(f"message length must be dividable by 8 ({len(bits)})")

        return Bitstring(bits)

    @property
    def value(self) -> Any:
        raise NotImplementedError

    @property
    def bytestring(self) -> bytes:
        bits = str(self.bitstring)
        return b"".join(
            [int(bits[i : i + 8], 2).to_bytes(1, "big") for i in range(0, len(bits), 8)]
        )

    @property
    def fields(self) -> List[str]:
        return [f.name for f in self._model.fields]

    @property
    def accessible_fields(self) -> List[str]:

        nxt = self._next_field(INITIAL.name)
        fields: List[str] = []
        while nxt and nxt != FINAL.name:

            if (
                self.__simplified(self._model.field_condition(Field(nxt))) != TRUE
                or not self._has_first(nxt)
                or (
                    not self._has_length(nxt)
                    if not isinstance(self._fields[nxt].typeval, OpaqueValue)
                    else not self._is_valid_opaque_field(nxt)
                )
            ):
                break

            fields.append(nxt)
            nxt = self._next_field(nxt)
        return fields

    def _is_valid_opaque_field(self, field: str) -> bool:

        if self._get_length_unchecked(field) == UNDEFINED:
            return False

        for edge in self._model.incoming(Field(field)):
            if self.__simplified(edge.condition) == TRUE:
                valid_edge = edge
                break
        else:
            return True

        return all(
            [
                bool(
                    (str(ve.name) in self._fields and self._fields[str(ve.name)].set)
                    or (ve == Last("Message"))
                )
                for ve in valid_edge.length.variables()
            ]
        )

    @property
    def valid_fields(self) -> List[str]:
        return [
            f
            for f in self.accessible_fields
            if (
                self._fields[f].set
                and self.__simplified(self._model.field_condition(Field(f))) == TRUE
                and any(
                    [self.__simplified(i.condition) == TRUE for i in self._model.incoming(Field(f))]
                )
                and any(
                    [self.__simplified(o.condition) == TRUE for o in self._model.outgoing(Field(f))]
                )
            )
        ]

    @property
    def required_fields(self) -> List[str]:
        accessible = self.accessible_fields
        valid = self.valid_fields
        return [f for f in accessible if f not in valid]

    @property
    def valid_message(self) -> bool:
        return bool(self.valid_fields) and self._next_field(self.valid_fields[-1]) == FINAL.name

    def __simplified(self, expr: Expr) -> Expr:
        field_values: Mapping[Name, Expr] = {
            **{
                Variable(k): v.typeval.expr
                for k, v in self._fields.items()
                if isinstance(v.typeval, ScalarValue) and v.set
            },
            **{Length(k): v.length for k, v in self._fields.items() if v.set},
            **{First(k): v.first for k, v in self._fields.items() if v.set},
            **{Last(k): v.last for k, v in self._fields.items() if v.set},
        }

        return expr.simplified(field_values).simplified(self.__type_literals)

    class Field:
        def __init__(self, t: TypeValue):
            self.typeval = t
            self.length: Expr = UNDEFINED
            self.first: Expr = UNDEFINED

        def __eq__(self, other: object) -> bool:
            if isinstance(other, MessageValue.Field):
                return (
                    self.length == other.length
                    and self.first == other.first
                    and self.last == other.last
                    and self.typeval == other.typeval
                )
            return NotImplemented

        def __repr__(self) -> str:
            return generic_repr(self.__class__.__name__, self.__dict__)

        @property
        def set(self) -> bool:
            return (
                self.typeval.initialized
                and isinstance(self.length, Number)
                and isinstance(self.first, Number)
                and isinstance(self.last, Number)
            )

        @property
        def last(self) -> Expr:
            return Sub(Add(self.first, self.length), Number(1)).simplified()
