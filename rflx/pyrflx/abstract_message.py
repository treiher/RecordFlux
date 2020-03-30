from abc import ABC, abstractmethod
from typing import Any, List

from rflx.expression import Expr, Number


class IMessage(ABC):
    @abstractmethod
    def check_model_equality(self, other: "IMessage") -> bool:
        raise NotImplementedError

    @abstractmethod
    def _next_field(self, fld: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def _prev_field(self, fld: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def _get_length_unchecked(self, fld: str) -> Expr:
        raise NotImplementedError

    @abstractmethod
    def _has_length(self, fld: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _get_length(self, fld: str) -> Number:
        raise NotImplementedError

    @abstractmethod
    def _get_first_unchecked(self, fld: str) -> Expr:
        raise NotImplementedError

    @abstractmethod
    def _has_first(self, fld: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _get_first(self, fld: str) -> Number:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def set(self, fld: str, value: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, fld: str) -> Any:
        raise NotImplementedError

    @property
    @abstractmethod
    def binary(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def fields(self) -> List[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def accessible_fields(self) -> List[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def valid_fields(self) -> List[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def required_fields(self) -> List[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def valid_message(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse_from_bytes(self, msg_as_bytes: bytes, original_length_in_bit=0) -> None:
        raise NotImplementedError
