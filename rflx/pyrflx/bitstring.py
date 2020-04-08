from typing import Union


class Bitstring:
    def __init__(self, bits: str = ""):
        if not self.valid_bitstring(bits):
            raise ValueError("Bitstring does not consist of only 0 and 1")
        self._bits = bits

    def __add__(self, other: "Bitstring") -> "Bitstring":
        return Bitstring(self._bits + other._bits)

    def __iadd__(self, other: "Bitstring") -> "Bitstring":
        self._bits += other._bits
        return self

    def __getitem__(self, key: Union[int, slice]) -> "Bitstring":
        return Bitstring(self._bits[key])

    def __str__(self) -> str:
        return self._bits

    def __int__(self) -> int:
        return int(self._bits, 2)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bitstring):
            return NotImplemented
        return self._bits == other._bits

    def __bytes__(self) -> bytes:
        return b"".join(
            [int(self._bits[i : i + 8], 2).to_bytes(1, "big") for i in range(0, len(self._bits), 8)]
        )

    @classmethod
    def from_bytes(cls, msg: bytes) -> "Bitstring":
        return cls(format(int.from_bytes(msg, "big"), f"0{len(msg) * 8}b"))

    @staticmethod
    def valid_bitstring(bitstring: str) -> bool:
        return all((bit in ["0", "1"] for bit in bitstring))
