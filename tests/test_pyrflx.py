# pylint: disable=too-many-lines

import itertools
from pathlib import Path
from typing import List

import pytest

from rflx.expression import UNDEFINED
from rflx.identifier import ID
from rflx.model import (
    FINAL,
    INITIAL,
    Array,
    Enumeration,
    ModularInteger,
    Number,
    Opaque,
    RangeInteger,
    Type,
)
from rflx.pyrflx import (
    ArrayValue,
    Bitstring,
    EnumValue,
    IntegerValue,
    MessageValue,
    NotInitializedError,
    OpaqueValue,
    Package,
    PyRFLX,
    TypeValue,
)

TESTDIR = "tests"
SPECDIR = "specs"


@pytest.fixture(name="pyrflx", scope="module")
def fixture_pyrflx() -> PyRFLX:
    return PyRFLX(
        [
            f"{SPECDIR}/ethernet.rflx",
            f"{SPECDIR}/icmp.rflx",
            f"{SPECDIR}/in_ethernet.rflx",
            f"{SPECDIR}/in_ipv4.rflx",
            f"{SPECDIR}/ipv4.rflx",
            f"{SPECDIR}/tls_alert.rflx",
            f"{SPECDIR}/tls_record.rflx",
            f"{SPECDIR}/tlv.rflx",
            f"{SPECDIR}/udp.rflx",
            f"{TESTDIR}/array_message.rflx",
            f"{TESTDIR}/array_type.rflx",
            f"{TESTDIR}/message_odd_length.rflx",
            f"{TESTDIR}/null_message.rflx",
            f"{TESTDIR}/tlv_with_checksum.rflx",
        ]
    )


@pytest.fixture(name="tlv_checksum_package", scope="module")
def fixture_tlv_checksum_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["TLV_With_Checksum"]


@pytest.fixture(name="ethernet_package", scope="module")
def fixture_ethernet_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["Ethernet"]


@pytest.fixture(name="tls_record_package", scope="module")
def fixture_tls_record_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["TLS_Record"]


@pytest.fixture(name="tls_alert_package", scope="module")
def fixture_tls_alert_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["TLS_Alert"]


@pytest.fixture(name="icmp_package", scope="module")
def fixture_icmp_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["ICMP"]


@pytest.fixture(name="message_odd_length_package", scope="module")
def fixture_message_odd_length_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["Message_Odd_Length"]


@pytest.fixture(name="ipv4_package", scope="module")
def fixture_ipv4_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["IPv4"]


@pytest.fixture(name="array_message_package", scope="module")
def fixture_array_message_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["Array_Message"]


@pytest.fixture(name="array_type_package", scope="module")
def fixture_array_type_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["Array_Type"]


@pytest.fixture(name="udp_package", scope="module")
def fixture_udp_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["UDP"]


@pytest.fixture(name="tlv_package", scope="module")
def fixture_tlv_package(pyrflx: PyRFLX) -> Package:
    return pyrflx["TLV"]


@pytest.fixture(name="tlv_checksum")
def fixture_tlv_checksum(tlv_checksum_package: Package) -> MessageValue:
    return tlv_checksum_package["Message"]


@pytest.fixture(name="tlv")
def fixture_tlv(tlv_package: Package) -> MessageValue:
    return tlv_package["Message"]


@pytest.fixture(name="frame")
def fixture_frame(ethernet_package: Package) -> MessageValue:
    return ethernet_package["Frame"]


@pytest.fixture(name="tls_record")
def fixture_tls_record(tls_record_package: Package) -> MessageValue:
    return tls_record_package["TLS_Record"]


@pytest.fixture(name="alert")
def fixture_alert(tls_alert_package: Package) -> MessageValue:
    return tls_alert_package["Alert"]


@pytest.fixture(name="icmp")
def fixture_echo_request_reply_message(icmp_package: Package) -> MessageValue:
    return icmp_package["Message"]


@pytest.fixture(name="message_odd_length")
def fixture_odd_length(message_odd_length_package: Package) -> MessageValue:
    return message_odd_length_package["Message"]


@pytest.fixture(name="ipv4")
def fixture_ipv4(ipv4_package: Package) -> MessageValue:
    return ipv4_package["Packet"]


@pytest.fixture(name="ipv4_option")
def fixture_ipv4_option(ipv4_package: Package) -> MessageValue:
    return ipv4_package["Option"]


@pytest.fixture(name="array_message")
def fixture_array_message(array_message_package: Package) -> MessageValue:
    return array_message_package["Message"]


@pytest.fixture(name="array_type_foo")
def fixture_array_type_foo(array_type_package: Package) -> MessageValue:
    return array_type_package["Foo"]


@pytest.fixture(name="udp")
def fixture_udp(udp_package: Package) -> MessageValue:
    return udp_package["Datagram"]


def test_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        PyRFLX([f"{tmp_path}/test.rflx"])


def test_package_name() -> None:
    p = Package("Test")
    assert p.name == "Test"


def test_package_iterator(tlv_package: Package) -> None:
    assert [m.name for m in tlv_package] == ["Message"]


def test_message_identifier(frame: MessageValue) -> None:
    assert frame.identifier == ID("Ethernet.Frame")
    assert frame.package == ID("Ethernet")
    assert frame.name == "Frame"


def test_message_eq(tlv_package: Package) -> None:
    m1 = tlv_package["Message"]
    assert m1 == tlv_package["Message"]
    assert m1 is not tlv_package["Message"]
    assert tlv_package["Message"] == tlv_package["Message"]
    assert tlv_package["Message"] is not tlv_package["Message"]
    assert m1 is not None


def test_attributes(pyrflx: PyRFLX) -> None:
    pyrflx = PyRFLX([f"{TESTDIR}/tlv_with_checksum.rflx"])
    assert isinstance(pyrflx["TLV_With_Checksum"], Package)
    tlv_package = pyrflx["TLV_With_Checksum"]
    assert isinstance(tlv_package["Message"], MessageValue)


def test_all_fields(tlv_checksum: MessageValue) -> None:
    assert tlv_checksum.fields == ["Tag", "Length", "Value", "Checksum"]


def test_accessible_fields_initial_fields(tlv_checksum: MessageValue) -> None:
    assert tlv_checksum.accessible_fields == ["Tag"]


def test_accessible_fields_tag_fields(tlv_checksum: MessageValue) -> None:
    tlv_checksum.set("Tag", "Msg_Data")
    assert tlv_checksum.accessible_fields == ["Tag", "Length"]


def test_accessible_fields_length_fields(tlv_checksum: MessageValue) -> None:
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 1)
    assert tlv_checksum.accessible_fields == ["Tag", "Length", "Value", "Checksum"]
    tlv_checksum.set("Value", b"\x01")
    assert tlv_checksum.accessible_fields == ["Tag", "Length", "Value", "Checksum"]


def test_accessible_fields_error_fields(tlv_checksum: MessageValue) -> None:
    tlv_checksum.set("Tag", "Msg_Error")
    assert tlv_checksum.accessible_fields == ["Tag"]


def test_accessible_fields_error_reset_fields(tlv_checksum: MessageValue) -> None:
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 1)
    assert tlv_checksum.accessible_fields == ["Tag", "Length", "Value", "Checksum"]
    tlv_checksum.set("Tag", "Msg_Error")
    assert tlv_checksum.accessible_fields == ["Tag"]


def test_accessible_fields_fields_complex(tlv_checksum: MessageValue) -> None:
    assert tlv_checksum.accessible_fields == ["Tag"]
    tlv_checksum.set("Tag", "Msg_Error")
    assert tlv_checksum.accessible_fields == ["Tag"]
    tlv_checksum.set("Tag", "Msg_Data")
    assert tlv_checksum.accessible_fields == ["Tag", "Length"]
    tlv_checksum.set("Length", 1)
    assert tlv_checksum.accessible_fields == ["Tag", "Length", "Value", "Checksum"]
    tlv_checksum.set("Value", b"\x01")
    assert tlv_checksum.accessible_fields == ["Tag", "Length", "Value", "Checksum"]
    tlv_checksum.set("Checksum", 0xFFFFFFFF)
    assert tlv_checksum.accessible_fields == ["Tag", "Length", "Value", "Checksum"]
    tlv_checksum.set("Tag", "Msg_Error")
    assert tlv_checksum.accessible_fields == ["Tag"]


def test_valid_message(tlv_checksum: MessageValue) -> None:
    assert not tlv_checksum.valid_message
    tlv_checksum.set("Tag", "Msg_Error")
    assert tlv_checksum.valid_message
    tlv_checksum.set("Tag", "Msg_Data")
    assert not tlv_checksum.valid_message
    tlv_checksum.set("Length", 1)
    assert not tlv_checksum.valid_message
    tlv_checksum.set("Value", b"\x01")
    assert not tlv_checksum.valid_message
    tlv_checksum.set("Checksum", 0xFFFFFFFF)
    assert tlv_checksum.valid_message


def test_valid_fields(tlv_checksum: MessageValue) -> None:
    assert tlv_checksum.valid_fields == []
    tlv_checksum.set("Tag", "Msg_Data")
    assert tlv_checksum.valid_fields == ["Tag"]
    tlv_checksum.set("Length", 1)
    assert tlv_checksum.valid_fields == ["Tag", "Length"]
    tlv_checksum.set("Value", b"\x01")
    assert tlv_checksum.valid_fields == ["Tag", "Length", "Value"]
    tlv_checksum.set("Checksum", 0xFFFFFFFF)
    assert tlv_checksum.valid_fields == ["Tag", "Length", "Value", "Checksum"]


def test_set_value(tlv_checksum: MessageValue) -> None:
    v1 = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    v2 = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10"
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 8)
    tlv_checksum.set("Value", v1)
    with pytest.raises(
        ValueError,
        match="invalid data length: input length is 80 while expected input length is 64",
    ):
        tlv_checksum.set("Value", v2)


def test_tlv_message(tlv_checksum: MessageValue) -> None:
    v1 = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 8)
    tlv_checksum.set("Value", v1)
    tlv_checksum.set("Checksum", 2 ** 32 - 1)


def test_tlv_generate(tlv_checksum: MessageValue) -> None:
    test_payload = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    test_data = b"\x40\x08" + test_payload + b"\xff\xff\xff\xff"
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 8)
    tlv_checksum.set("Value", test_payload)
    tlv_checksum.set("Checksum", 0xFFFFFFFF)
    assert tlv_checksum.bytestring == test_data


def test_tlv_change_field(tlv_checksum: MessageValue) -> None:
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 1)
    tlv_checksum.set("Tag", "Msg_Data")
    assert "Length" in tlv_checksum.valid_fields
    tlv_checksum.set("Value", b"a")
    tlv_checksum.set("Checksum", 0)
    tlv_checksum.set("Length", 2)
    assert "Value" not in tlv_checksum.valid_fields
    assert "Checksum" not in tlv_checksum.valid_fields
    tlv_checksum.set("Value", b"ab")
    assert "Checksum" in tlv_checksum.valid_fields


def test_tlv_binary_length(tlv_checksum: MessageValue) -> None:
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 8)
    assert tlv_checksum.bytestring == b"\x40\x08"


def test_tlv_value(tlv_checksum: MessageValue) -> None:
    v1 = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    tlv_checksum.set("Tag", "Msg_Data")
    tlv_checksum.set("Length", 8)
    tlv_checksum.set("Value", v1)
    tlv_checksum.set("Checksum", 2 ** 32 - 1)
    assert tlv_checksum.get("Tag") == "Msg_Data"
    assert tlv_checksum.get("Length") == 8
    assert tlv_checksum.get("Value") == v1
    assert tlv_checksum.get("Checksum") == 0xFFFFFFFF


def test_tlv_get_invalid_field(tlv_checksum: MessageValue) -> None:
    with pytest.raises(ValueError, match=r"field nofield not valid"):
        tlv_checksum.get("nofield")


def test_tlv_set_invalid_field(tlv_checksum: MessageValue) -> None:
    tlv_checksum.set("Tag", "Msg_Data")
    with pytest.raises(KeyError, match=r"cannot access field Value"):
        tlv_checksum.set("Value", b"")
    with pytest.raises(KeyError, match=r"cannot access field Checksum"):
        tlv_checksum.set("Checksum", 8)
    tlv_checksum.set("Tag", "Msg_Error")
    with pytest.raises(KeyError, match=r"cannot access field Length"):
        tlv_checksum.set("Length", 8)


def test_tlv_invalid_value(tlv_checksum: MessageValue) -> None:
    with pytest.raises(
        ValueError,
        match="Error while setting value for field Tag: "
        "cannot assign different types: str != int",
    ):
        tlv_checksum.set("Tag", 1)
    tlv_checksum.set("Tag", "Msg_Data")
    with pytest.raises(
        ValueError,
        match="Error while setting value for field Length: "
        "cannot assign different types: int != str",
    ):
        tlv_checksum.set("Length", "blubb")


def test_tlv_next(tlv_checksum: MessageValue) -> None:
    # pylint: disable=protected-access
    tlv_checksum.set("Tag", "Msg_Data")
    assert tlv_checksum._next_field(INITIAL.name) == "Tag"
    assert tlv_checksum._next_field("Tag") == "Length"
    assert tlv_checksum._next_field(FINAL.name) == ""


def test_tlv_prev(tlv_checksum: MessageValue) -> None:
    # pylint: disable=protected-access
    tlv_checksum.set("Tag", "Msg_Data")
    assert tlv_checksum._prev_field("Tag") == INITIAL.name
    assert tlv_checksum._prev_field(INITIAL.name) == ""
    tlv_checksum.set("Tag", "Msg_Error")
    assert tlv_checksum._prev_field("Length") == ""


def test_tlv_required_fields(tlv_checksum: MessageValue) -> None:
    assert tlv_checksum.required_fields == ["Tag"]
    tlv_checksum.set("Tag", "Msg_Data")
    assert tlv_checksum.required_fields == ["Length"]
    tlv_checksum.set("Length", 1)
    assert tlv_checksum.required_fields == ["Value", "Checksum"]
    tlv_checksum.set("Value", b"\x01")
    assert tlv_checksum.required_fields == ["Checksum"]
    tlv_checksum.set("Checksum", 0xFFFFFFFF)
    assert tlv_checksum.required_fields == []


def test_tlv_length_unchecked(tlv_checksum: MessageValue) -> None:
    # pylint: disable=protected-access
    tlv_checksum.set("Tag", "Msg_Error")
    assert not isinstance(tlv_checksum._get_length_unchecked("Value"), Number)
    tlv_checksum.set("Tag", "Msg_Data")
    assert not isinstance(tlv_checksum._get_length_unchecked("Value"), Number)
    tlv_checksum.set("Length", 1)
    assert isinstance(tlv_checksum._get_length_unchecked("Value"), Number)


def test_tlv_first_unchecked(tlv_checksum: MessageValue) -> None:
    # pylint: disable=protected-access
    tlv_checksum.set("Tag", "Msg_Error")
    assert not isinstance(tlv_checksum._get_first_unchecked("Checksum"), Number)
    tlv_checksum.set("Tag", "Msg_Data")
    assert not isinstance(tlv_checksum._get_first_unchecked("Checksum"), Number)
    tlv_checksum.set("Length", 1)
    assert isinstance(tlv_checksum._get_first_unchecked("Checksum"), Number)


def test_ethernet_all_fields(frame: MessageValue) -> None:
    assert frame.fields == [
        "Destination",
        "Source",
        "Type_Length_TPID",
        "TPID",
        "TCI",
        "Type_Length",
        "Payload",
    ]


def test_ethernet_initial(frame: MessageValue) -> None:
    assert frame.accessible_fields == ["Destination", "Source", "Type_Length_TPID"]


def test_ethernet_set_tltpid(frame: MessageValue) -> None:
    frame.set("Destination", 0)
    frame.set("Source", 1)
    frame.set("Type_Length_TPID", 0x8100)
    assert frame.valid_fields == ["Destination", "Source", "Type_Length_TPID"]
    assert frame.accessible_fields == [
        "Destination",
        "Source",
        "Type_Length_TPID",
        "TPID",
        "TCI",
        "Type_Length",
    ]
    frame.set("Type_Length_TPID", 64)
    assert frame.valid_fields == ["Destination", "Source", "Type_Length_TPID"]
    assert frame.accessible_fields == [
        "Destination",
        "Source",
        "Type_Length_TPID",
        "Type_Length",
    ]


def test_ethernet_set_nonlinear(frame: MessageValue) -> None:
    assert frame.accessible_fields == ["Destination", "Source", "Type_Length_TPID"]
    frame.set("Type_Length_TPID", 0x8100)
    frame.set("TCI", 100)
    assert frame.valid_fields == ["Type_Length_TPID", "TCI"]


def test_ethernet_final(frame: MessageValue) -> None:
    assert not frame.valid_message
    frame.set("Destination", 0)
    assert not frame.valid_message
    frame.set("Source", 1)
    assert not frame.valid_message
    frame.set("Type_Length_TPID", 46)
    assert not frame.valid_message
    frame.set("Type_Length", 46)
    assert not frame.valid_message
    frame.set("Payload", bytes(46))
    assert frame.valid_message


def test_ethernet_802_3(frame: MessageValue) -> None:
    frame.set("Destination", 2 ** 48 - 1)
    frame.set("Source", 0)
    frame.set("Type_Length_TPID", 46)
    frame.set("Type_Length", 46)
    frame.set(
        "Payload",
        (
            b"\x45\x00\x00\x14"
            b"\x00\x01\x00\x00"
            b"\x40\x00\x7c\xe7"
            b"\x7f\x00\x00\x01"
            b"\x7f\x00\x00\x01"
            b"\x00\x00\x00\x00"
            b"\x00\x00\x00\x00"
            b"\x00\x00\x00\x00"
            b"\x00\x00\x00\x00"
            b"\x00\x00\x00\x00"
            b"\x00\x00\x00\x00"
            b"\x00\x00"
        ),
    )
    assert frame.valid_message
    with open(f"{TESTDIR}/ethernet_802.3.raw", "rb") as raw:
        assert frame.bytestring == raw.read()


def test_ethernet_payload(frame: MessageValue) -> None:
    frame.set("Source", 0)
    frame.set("Destination", 0)
    frame.set("Type_Length_TPID", 47)
    frame.set("Type_Length", 1537)
    assert frame.accessible_fields == [
        "Destination",
        "Source",
        "Type_Length_TPID",
        "Type_Length",
        "Payload",
    ]
    frame.set("Payload", bytes(46))
    assert frame.valid_message


def test_ethernet_invalid(frame: MessageValue) -> None:
    frame.set("Destination", 2 ** 48 - 1)
    frame.set("Source", 0)
    frame.set("Type_Length_TPID", 1501)
    with pytest.raises(
        ValueError,
        match=r"none of the field conditions .* for field Type_Length"
        " have been met by the assigned value: 1501",
    ):
        frame.set("Type_Length", 1501)


def test_tls_fields(tls_record: MessageValue) -> None:
    assert tls_record.accessible_fields == ["Tag", "Legacy_Record_Version", "Length"]
    tls_record.set("Tag", "INVALID")
    tls_record.set("Length", 3)
    assert tls_record.accessible_fields == [
        "Tag",
        "Legacy_Record_Version",
        "Length",
        "Fragment",
    ]


def test_tls_invalid_outgoing(tls_record: MessageValue) -> None:
    tls_record.set("Tag", "INVALID")
    with pytest.raises(
        ValueError,
        match=r"none of the field conditions .* for field Length"
        " have been met by the assigned value: 16385",
    ):
        tls_record.set("Length", 2 ** 14 + 1)


def test_tls_invalid_path(alert: MessageValue) -> None:
    alert.set("Level", "WARNING")
    alert.set("Description", "CLOSE_NOTIFY")
    assert alert.valid_message
    assert alert.valid_fields == ["Level", "Description"]
    alert.set("Level", "FATAL")
    assert not alert.valid_message
    assert alert.valid_fields == ["Level"]


def test_tls_length_unchecked(tls_record: MessageValue) -> None:
    # pylint: disable=protected-access
    tls_record.set("Tag", "APPLICATION_DATA")
    tls_record.set("Legacy_Record_Version", "TLS_1_2")
    assert not isinstance(tls_record._get_length_unchecked("Fragment"), Number)


def test_icmp_echo_request(icmp: MessageValue) -> None:
    test_data = (
        b"\x4a\xfc\x0d\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17"
        b"\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27"
        b"\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37"
    )

    icmp.set("Tag", "Echo_Request")
    icmp.set("Code_Zero", 0)
    icmp.set("Checksum", 12824)
    icmp.set("Identifier", 5)
    icmp.set("Sequence_Number", 1)
    icmp.set(
        "Data", test_data,
    )
    assert icmp.bytestring == b"\x08\x00\x32\x18\x00\x05\x00\x01" + test_data
    assert icmp.valid_message


def test_value_mod() -> None:
    # pylint: disable=pointless-statement
    modtype = ModularInteger("Test.Int", Number(2 ** 16))
    modvalue = IntegerValue(modtype)
    assert not modvalue.initialized
    with pytest.raises(NotInitializedError, match="value not initialized"):
        modvalue.value
    with pytest.raises(NotInitializedError, match="value not initialized"):
        modvalue.expr
    modvalue.assign(128)
    assert modvalue.initialized
    assert modvalue.value == 128
    assert str(modvalue.bitstring) == "0000000010000000"
    with pytest.raises(ValueError, match=r"value 65536 not in type range 0 .. 65535"):
        modvalue.assign(2 ** 16)
    with pytest.raises(ValueError, match=r"value -1 not in type range 0 .. 65535"):
        modvalue.assign(-1)


def test_value_range() -> None:
    # pylint: disable=pointless-statement
    rangetype = RangeInteger("Test.Int", Number(8), Number(16), Number(8))
    rangevalue = IntegerValue(rangetype)
    assert not rangevalue.initialized
    with pytest.raises(NotInitializedError, match="value not initialized"):
        rangevalue.value
    with pytest.raises(NotInitializedError, match="value not initialized"):
        rangevalue.expr
    rangevalue.assign(10)
    assert rangevalue.initialized
    assert rangevalue.value == 10
    assert str(rangevalue.bitstring) == "00001010"
    with pytest.raises(ValueError, match=r"value 17 not in type range 8 .. 16"):
        rangevalue.assign(17)
    with pytest.raises(ValueError, match=r"value 7 not in type range 8 .. 16"):
        rangevalue.assign(7)


def test_value_enum() -> None:
    # pylint: disable=pointless-statement
    enumtype = Enumeration("Test.Enum", {"One": Number(1), "Two": Number(2)}, Number(8), False)
    enumvalue = EnumValue(enumtype)
    assert not enumvalue.initialized
    with pytest.raises(NotInitializedError, match="value not initialized"):
        enumvalue.value
    with pytest.raises(NotInitializedError, match="value not initialized"):
        enumvalue.expr
    enumvalue.assign("One")
    assert enumvalue.initialized
    assert enumvalue.value == "One"
    assert str(enumvalue.bitstring) == "00000001"
    with pytest.raises(KeyError, match=r"Three is not a valid enum value"):
        enumvalue.assign("Three")
    with pytest.raises(KeyError, match=r"Number 15 is not a valid enum value"):
        enumvalue.parse(Bitstring("1111"))


def test_value_opaque() -> None:
    # pylint: disable=pointless-statement
    # pylint: disable=protected-access
    opaquevalue = OpaqueValue(Opaque())
    assert not opaquevalue.initialized
    with pytest.raises(NotInitializedError, match="value not initialized"):
        opaquevalue.value
    opaquevalue.assign(b"\x01\x02")
    assert opaquevalue.initialized
    assert opaquevalue.value == b"\x01\x02"
    k = opaquevalue.size
    assert isinstance(k, Number)
    assert k.value == 16
    assert str(opaquevalue.bitstring) == "0000000100000010"
    opaquevalue.parse(Bitstring("1111"))
    assert opaquevalue._value == b"\x0f"


def test_value_equal() -> None:
    # pylint: disable=comparison-with-itself
    ov = OpaqueValue(Opaque())
    enumtype = Enumeration("Test.Enum", {"One": Number(1), "Two": Number(2)}, Number(8), False)
    ev = EnumValue(enumtype)
    rangetype = RangeInteger("Test.Int", Number(8), Number(16), Number(8))
    rv = IntegerValue(rangetype)
    modtype = ModularInteger("Test.Int", Number(2 ** 16))
    mv = IntegerValue(modtype)
    mv2 = IntegerValue(modtype)
    assert ov == ov
    assert ev == ev
    assert rv == rv
    assert mv == mv
    assert ev != rv
    assert mv == mv2
    mv.assign(2)
    assert mv != mv2
    mv2.assign(10)
    assert mv != mv2
    mv.assign(10)
    assert mv == mv2
    rv.assign(10)
    assert mv != rv


def test_value_clear() -> None:
    ov = OpaqueValue(Opaque())
    assert not ov.initialized
    ov.assign(b"")
    assert ov.initialized
    ov.clear()
    assert not ov.initialized


def test_value_invalid() -> None:
    class TestType(Type):
        pass

    t = TestType("Test.Type")
    with pytest.raises(ValueError, match="cannot construct unknown type: TestType"):
        TypeValue.construct(t)


def test_field_eq() -> None:
    f1 = MessageValue.Field(OpaqueValue(Opaque()))
    assert f1 == MessageValue.Field(OpaqueValue(Opaque()))
    f1.typeval.parse(b"")
    assert f1 != MessageValue.Field(OpaqueValue(Opaque()))
    assert f1 is not None


def test_field_set() -> None:
    f = MessageValue.Field(OpaqueValue(Opaque()))
    assert not f.set
    f.typeval.parse(b"\x01")
    assert not f.set
    f.first = Number(1)
    assert f.set


def test_get_first_unchecked_undefined(tlv_checksum: MessageValue) -> None:
    # pylint: disable=protected-access
    assert tlv_checksum._get_first_unchecked("Length") == UNDEFINED


def test_check_nodes_opaque(tlv_checksum: MessageValue, frame: MessageValue) -> None:
    # pylint: disable=protected-access
    assert tlv_checksum._is_valid_opaque_field("Length")
    assert not tlv_checksum._is_valid_opaque_field("Value")
    frame.set("Destination", 2 ** 48 - 1)
    frame.set("Source", 0)
    frame.set("Type_Length_TPID", 1501)
    assert not frame._is_valid_opaque_field("Payload")


def test_icmp_parse_binary(icmp: MessageValue) -> None:
    test_bytes = (
        b"\x08\x00\xe1\x1e\x00\x11\x00\x01\x4a\xfc\x0d\x00\x00\x00\x00\x00"
        b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
        b"\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f"
        b"\x30\x31\x32\x33\x34\x35\x36\x37"
    )
    icmp.parse(test_bytes)
    assert icmp.valid_message
    assert icmp.bytestring == test_bytes
    assert icmp.accepted_type == bytes
    assert icmp.size == Number(448)


def test_ethernet_parse_binary(frame: MessageValue) -> None:
    test_bytes = (
        b"\xe0\x28\x6d\x39\x80\x1e\x1c\x1b\x0d\xe0\xd8\xa8\x08\x00\x45\x00"
        b"\x00\x4c\x1f\x04\x40\x00\x40\x01\xe1\x6a\xc0\xa8\xbc\x3d\xac\xd9"
        b"\x10\x83\x08\x00\xe1\x26\x00\x09\x00\x01\x4a\xfc\x0d\x00\x00\x00"
        b"\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d"
        b"\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d"
        b"\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37"
    )
    frame.parse(test_bytes)
    assert frame.valid_message
    assert frame.bytestring == test_bytes


def test_value_parse_from_bitstring(tlv: MessageValue) -> None:
    # pylint: disable=protected-access
    intval = IntegerValue(ModularInteger("Test.Int", Number(256)))
    intval.parse(b"\x02")
    assert intval.value == 2
    enumval = EnumValue(
        Enumeration("Test.Enum", {"something": Number(1), "other": Number(2)}, Number(2), False,)
    )
    enumval.parse(b"\x01")
    assert enumval.value == "something"
    msg_array = ArrayValue(Array("Test.MsgArray", tlv._type))
    tlv.set("Tag", "Msg_Data")
    tlv.set("Length", 4)
    tlv.set("Value", b"\x00\x00\x00\x00")
    msg_array.parse(tlv.bytestring)


def test_bitstring(tlv_checksum: MessageValue) -> None:
    with pytest.raises(ValueError, match="Bitstring does not consist of only 0 and 1"):
        Bitstring("123")
    assert Bitstring("01") + Bitstring("00") == Bitstring("0100")

    test_bytes = b"\x40"
    with pytest.raises(
        IndexError,
        match=(
            "Bitstring representing the message is too short"
            " - stopped while parsing field: Length"
        ),
    ):
        tlv_checksum.parse(test_bytes)
    assert not tlv_checksum.valid_message


def test_odd_length_binary(message_odd_length: MessageValue) -> None:
    test_bytes = b"\x01\x02\x01\xff\xb8"
    message_odd_length.parse(test_bytes)
    assert message_odd_length.valid_message


def test_array_nested_messages(array_message_package: Package, array_message: MessageValue) -> None:
    array_message_one = array_message_package["Foo"]
    array_message_one.set("Byte", 5)
    array_message_two = array_message_package["Foo"]
    array_message_two.set("Byte", 6)
    foos: List[TypeValue] = [array_message_one, array_message_two]
    array_message.set("Length", 2)
    array_message.set("Bar", foos)
    assert array_message.valid_message
    assert array_message.bytestring == b"\x02\x05\x06"


def test_array_nested_values(array_type_foo: MessageValue) -> None:
    a = IntegerValue(ModularInteger("Array_Type.Byte_One", Number(256)))
    b = IntegerValue(ModularInteger("Array_Type.Byte_Two", Number(256)))
    c = IntegerValue(ModularInteger("Array_Type.Byte_Three", Number(256)))
    a.assign(5)
    b.assign(6)
    c.assign(7)
    byte_array = [a, b, c]
    array_type_foo.set("Length", 3)
    array_type_foo.set("Bytes", byte_array)
    assert array_type_foo.valid_message
    assert array_type_foo.bytestring == b"\x03\x05\x06\x07"


def test_array_preserve_value() -> None:
    intval = IntegerValue(ModularInteger("Test.Int", Number(256)))
    intval.assign(1)
    enumval = EnumValue(
        Enumeration("Test.Enum", {"something": Number(1), "other": Number(2)}, Number(2), False,)
    )
    enumval.assign("something")
    type_array = ArrayValue(Array("Test.Array", ModularInteger("Test.Mod_Int", Number(256))))
    type_array.assign([intval])
    assert type_array.value == [intval]
    with pytest.raises(ValueError, match="cannot assign EnumValue to an array of ModularInteger"):
        type_array.assign([enumval])
    assert type_array.value == [intval]


def test_array_parse_from_bytes(array_message: MessageValue, array_type_foo: MessageValue) -> None:
    array_message.parse(b"\x02\x05\x06")
    assert array_message.bytestring == b"\x02\x05\x06"
    array_type_foo.parse(b"\x03\x05\x06\x07")
    assert array_type_foo.bytestring == b"\x03\x05\x06\x07"


def test_array_assign_incorrect_values(
    tlv: MessageValue, frame: MessageValue, array_type_foo: MessageValue
) -> None:
    # pylint: disable=protected-access
    type_array = ArrayValue(Array("Test.Array", ModularInteger("Test.Mod_Int", Number(256))))
    msg_array = ArrayValue(Array("Test.MsgArray", tlv._type))

    intval = IntegerValue(ModularInteger("Test.Int", Number(256)))
    enumval = EnumValue(
        Enumeration("Test.Enum", {"something": Number(1), "other": Number(2)}, Number(2), False,)
    )
    enumval.assign("something")
    with pytest.raises(ValueError, match="cannot assign EnumValue to an array of ModularInteger"):
        type_array.assign([enumval])

    tlv.set("Tag", "Msg_Data")
    with pytest.raises(
        ValueError,
        match='cannot assign message "Message" to array of messages: all messages must be valid',
    ):
        msg_array.assign([tlv])

    with pytest.raises(ValueError, match="cannot assign EnumValue to an array of Message"):
        msg_array.assign([enumval])

    tlv.set("Tag", "Msg_Data")
    tlv.set("Length", 4)
    tlv.set("Value", b"\x00\x00\x00\x00")

    frame.set("Destination", 0)
    frame.set("Source", 0)
    frame.set("Type_Length_TPID", 47)
    frame.set("Type_Length", 1537)
    frame.set("Payload", bytes(46))

    with pytest.raises(ValueError, match='cannot assign "Frame" to an array of "Message"'):
        msg_array.assign([tlv, frame])

    with pytest.raises(
        ValueError,
        match="cannot parse nested messages in array of type TLV.Message: Error while setting "
        "value for field Tag: 'Number 0 is not a valid enum value'",
    ):
        msg_array.parse(Bitstring("0001111"))

    tlv.set("Tag", "Msg_Data")
    tlv._fields["Length"].typeval.assign(111111111111111, False)
    with pytest.raises(
        ValueError,
        match='cannot assign message "Message" to array of messages: all messages must be valid',
    ):
        msg_array.assign([tlv])
    assert msg_array.value == []

    intval.assign(5)
    array_type_foo.set("Length", 42)
    with pytest.raises(
        ValueError,
        match="invalid data length: input length is 8 while expected input length is 336",
    ):
        array_type_foo.set("Bytes", [intval])


def test_incorrect_nested_message(frame: MessageValue) -> None:
    incorrect_message = (
        b"\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00"
        b"\x81\x00\x00\x01\x08\x00\x45\x00\x00\xe2\x00\x01"
        b"\x00\x00\x40\x00\x7c\xe7\x7f\x00\x00\x01\x7f\x00"
        b"\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x0a"
    )
    with pytest.raises(
        ValueError,
        match="Error while setting value for field Payload: "
        "Error while parsing nested message IPv4.Packet: "
        "Bitstring representing the message is too short - "
        "stopped while parsing field: Payload",
    ):
        frame.parse(incorrect_message)


# rflx-ethernet-tests.adb


def test_ethernet_parsing_ethernet_2(frame: MessageValue) -> None:
    with open("tests/ethernet_ipv4_udp.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    frame.parse(msg_as_bytes)
    assert frame.get("Destination") == int("ffffffffffff", 16)
    assert frame.get("Source") == int("0", 16)
    assert frame.get("Type_Length_TPID") == int("0800", 16)
    k = frame._fields["Payload"].typeval.size
    assert isinstance(k, Number)
    assert k.value // 8 == 46
    assert frame.valid_message
    assert frame.bytestring == msg_as_bytes


def test_ethernet_parsing_ieee_802_3(frame: MessageValue) -> None:
    with open("tests/ethernet_802.3.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    frame.parse(msg_as_bytes)
    assert frame.valid_message
    assert frame.bytestring == msg_as_bytes


def test_ethernet_parsing_ethernet_2_vlan(frame: MessageValue) -> None:
    with open("tests/ethernet_vlan_tag.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    frame.parse(msg_as_bytes)
    assert frame.get("Destination") == int("ffffffffffff", 16)
    assert frame.get("Source") == int("0", 16)
    assert frame.get("Type_Length_TPID") == int("8100", 16)
    assert frame.get("TPID") == int("8100", 16)
    assert frame.get("TCI") == int("1", 16)
    assert frame.get("Type_Length") == int("0800", 16)
    k = frame._fields["Payload"].typeval.size
    assert isinstance(k, Number)
    assert k.value // 8 == 47
    assert frame.valid_message
    assert frame.bytestring == msg_as_bytes


def test_ethernet_parsing_invalid_ethernet_2_too_short(frame: MessageValue) -> None:
    with open("tests/ethernet_invalid_too_short.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    with pytest.raises(
        ValueError,
        match=r"none of the field conditions .* for field Payload"
        " have been met by the assigned value: [01]*",
    ):
        frame.parse(msg_as_bytes)
    assert not frame.valid_message


def test_ethernet_parsing_invalid_ethernet_2_too_long(frame: MessageValue) -> None:
    with open("tests/ethernet_invalid_too_long.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    with pytest.raises(
        ValueError,
        match=r"none of the field conditions .* for field Payload"
        " have been met by the assigned value: [01]*",
    ):
        frame.parse(msg_as_bytes)
    assert not frame.valid_message


def test_ethernet_parsing_invalid_ethernet_2_undefined_type(frame: MessageValue) -> None:
    with open("tests/ethernet_undefined.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    with pytest.raises(
        ValueError,
        match=r"none of the field conditions .* for field Type_Length"
        " have been met by the assigned value: [01]*",
    ):
        frame.parse(msg_as_bytes)

    assert not frame.valid_message


def test_ethernet_parsing_ieee_802_3_invalid_length(frame: MessageValue) -> None:
    with open("tests/ethernet_802.3_invalid_length.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    with pytest.raises(
        IndexError,
        match="Bitstring representing the message is too short"
        " - stopped while parsing field: Payload",
    ):
        frame.parse(msg_as_bytes)

    assert not frame.valid_message


def test_ethernet_parsing_incomplete(frame: MessageValue) -> None:
    test_bytes = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x02"
    with pytest.raises(
        IndexError,
        match="Bitstring representing the message is too short"
        " - stopped while parsing field: Type_Length_TPID",
    ):
        frame.parse(test_bytes)

    assert frame.get("Destination") == int("000000000001", 16)
    assert frame.get("Source") == int("000000000002", 16)
    assert len(frame.valid_fields) == 2
    assert not frame.valid_message


def test_ethernet_generating_ethernet_2(frame: MessageValue) -> None:
    payload = (
        b"\x45\x00\x00\x2e\x00\x01\x00\x00\x40\x11\x7c\xbc"
        b"\x7f\x00\x00\x01\x7f\x00\x00\x01\x00\x35\x00\x35"
        b"\x00\x1a\x01\x4e\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    frame.set("Destination", int("FFFFFFFFFFFF", 16))
    frame.set("Source", int("0", 16))
    frame.set("Type_Length_TPID", int("0800", 16))
    frame.set("Type_Length", int("0800", 16))
    frame.set("Payload", payload)
    with open("tests/ethernet_ipv4_udp.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    assert frame.bytestring == msg_as_bytes


def test_ethernet_generating_ieee_802_3(frame: MessageValue) -> None:
    payload = (
        b"\x45\x00\x00\x14\x00\x01\x00\x00\x40\x00\x7c\xe7"
        b"\x7f\x00\x00\x01\x7f\x00\x00\x01\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    frame.set("Destination", int("FFFFFFFFFFFF", 16))
    frame.set("Source", int("0", 16))
    frame.set("Type_Length_TPID", 46)
    frame.set("Type_Length", 46)
    frame.set("Payload", payload)
    assert frame.valid_message
    with open("tests/ethernet_802.3.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    assert frame.bytestring == msg_as_bytes


def test_ethernet_generating_ethernet_2_vlan(frame: MessageValue) -> None:
    payload = (
        b"\x45\x00\x00\x2f\x00\x01\x00\x00\x40\x00\x7c\xe7"
        b"\x7f\x00\x00\x01\x7f\x00\x00\x01\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a"
    )
    frame.set("Destination", int("FFFFFFFFFFFF", 16))
    frame.set("Source", int("0", 16))
    frame.set("Type_Length_TPID", int("8100", 16))
    frame.set("TPID", int("8100", 16))
    frame.set("TCI", 1)
    frame.set("Type_Length", int("0800", 16))
    frame.set("Payload", payload)
    assert frame.valid_message
    with open("tests/ethernet_vlan_tag.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    assert frame.bytestring == msg_as_bytes


def test_ethernet_generating_ethernet_2_vlan_dynamic() -> None:
    pass  # not relevant for Python implementation, as it tests correct verification in SPARK


# rflx in_ipv4-tests.adb


def test_ipv4_parsing_udp_in_ipv4(ipv4: MessageValue) -> None:
    with open("tests/ipv4_udp.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    ipv4.parse(msg_as_bytes)
    nested_udp = ipv4.get("Payload")
    assert isinstance(nested_udp, MessageValue)
    assert nested_udp.valid_message


def test_ipv4_parsing_udp_in_ipv4_in_ethernet(frame: MessageValue) -> None:
    with open("tests/ethernet_ipv4_udp.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    frame.parse(msg_as_bytes)
    nested_ipv4 = frame.get("Payload")
    assert isinstance(nested_ipv4, MessageValue)
    assert nested_ipv4.valid_message
    assert nested_ipv4.identifier == ID("IPv4.Packet")
    nested_udp = nested_ipv4.get("Payload")
    assert isinstance(nested_udp, MessageValue)
    assert nested_udp.valid_message
    assert nested_udp.identifier == ID("UDP.Datagram")


def test_ethernet_generating_udp_in_ipv4_in_ethernet(
    frame: MessageValue, ipv4: MessageValue, udp: MessageValue
) -> None:
    with open("tests/ethernet_ipv4_udp.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    frame.parse(msg_as_bytes)
    parsed_frame = frame.bytestring

    b = b""
    for _ in itertools.repeat(None, 18):
        b += b"\x00"

    udp.set("Source_Port", 53)
    udp.set("Destination_Port", 53)
    udp.set("Length", 26)
    udp.set("Checksum", int("014E", 16))
    udp.set("Payload", b)
    udp_binary = udp.bytestring

    ipv4.set("Version", 4)
    ipv4.set("IHL", 5)
    ipv4.set("DSCP", 0)
    ipv4.set("ECN", 0)
    ipv4.set("Total_Length", 46)
    ipv4.set("Identification", 1)
    ipv4.set("Flag_R", "False")
    ipv4.set("Flag_DF", "False")
    ipv4.set("Flag_MF", "False")
    ipv4.set("Fragment_Offset", 0)
    ipv4.set("TTL", 64)
    ipv4.set("Protocol", "PROTOCOL_UDP")
    ipv4.set("Header_Checksum", int("7CBC", 16))
    ipv4.set("Source", int("7f000001", 16))
    ipv4.set("Destination", int("7f000001", 16))
    ipv4.set("Payload", udp_binary)
    ip_binary = ipv4.bytestring

    frame.set("Destination", int("FFFFFFFFFFFF", 16))
    frame.set("Source", int("0", 16))
    frame.set("Type_Length_TPID", int("0800", 16))
    frame.set("Type_Length", int("0800", 16))
    frame.set("Payload", ip_binary)

    assert frame.valid_message
    assert frame.bytestring == parsed_frame


# rflx-ipv4-tests.adb


def test_ipv4_parsing_ipv4(ipv4: MessageValue) -> None:
    with open("tests/ipv4_udp.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    ipv4.parse(msg_as_bytes)
    assert ipv4.get("Version") == 4
    assert ipv4.get("IHL") == 5
    assert ipv4.get("DSCP") == 0
    assert ipv4.get("ECN") == 0
    assert ipv4.get("Total_Length") == 44
    assert ipv4.get("Identification") == 1
    assert ipv4.get("Flag_R") == "False"
    assert ipv4.get("Flag_DF") == "False"
    assert ipv4.get("Flag_MF") == "False"
    assert ipv4.get("Fragment_Offset") == 0
    assert ipv4.get("TTL") == 64
    assert ipv4.get("Protocol") == "PROTOCOL_UDP"
    assert ipv4.get("Header_Checksum") == int("7CBE", 16)
    assert ipv4.get("Source") == int("7f000001", 16)
    assert ipv4.get("Destination") == int("7f000001", 16)
    assert ipv4._fields["Payload"].typeval.size == Number(192)


def test_ipv4_parsing_ipv4_option(ipv4_option: MessageValue) -> None:
    expected = b"\x44\x03\x2a"
    ipv4_option.parse(expected)
    assert ipv4_option.get("Copied") == "False"
    assert ipv4_option.get("Option_Class") == "Debugging_And_Measurement"
    assert ipv4_option.get("Option_Number") == 4
    assert ipv4_option.get("Option_Length") == 3
    ip_option = ipv4_option.get("Option_Data")
    assert isinstance(ip_option, bytes)
    assert len(ip_option) == 1


@pytest.mark.skip(reason="ISSUE: Componolit/RecordFlux#61")
def test_ipv4_parsing_ipv4_with_options(ipv4: MessageValue) -> None:
    with open("tests/ipv4-options_udp.raw", "rb") as file:
        msg_as_bytes: bytes = file.read()
    ipv4.parse(msg_as_bytes)
    assert ipv4.valid_message


def test_ipv4_generating_ipv4(ipv4: MessageValue) -> None:
    data = (
        b"\x00\x35\x00\x35\x00\x18\x01\x52\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    ipv4.set("Version", 4)
    ipv4.set("IHL", 5)
    ipv4.set("DSCP", 0)
    ipv4.set("ECN", 0)
    ipv4.set("Total_Length", 44)
    ipv4.set("Identification", 1)
    ipv4.set("Flag_R", "False")
    ipv4.set("Flag_DF", "False")
    ipv4.set("Flag_MF", "False")
    ipv4.set("Fragment_Offset", 0)
    ipv4.set("TTL", 64)
    ipv4.set("Protocol", "PROTOCOL_UDP")
    ipv4.set("Header_Checksum", int("7CBE", 16))
    ipv4.set("Source", int("7f000001", 16))
    ipv4.set("Destination", int("7f000001", 16))
    ipv4.set("Payload", data)
    assert ipv4.valid_message


def test_ipv4_generating_ipv4_option(ipv4_option: MessageValue) -> None:
    ipv4_option.set("Copied", "False")
    ipv4_option.set("Option_Class", "Debugging_And_Measurement")
    ipv4_option.set("Option_Number", 4)
    ipv4_option.set("Option_Length", 3)
    ipv4_option.set("Option_Data", b"\x2a")
    assert ipv4_option.valid_message


# rflx-tlv-tests.adb


def test_tlv_parsing_tlv_data(tlv: MessageValue) -> None:
    test_bytes = b"\x40\x04\x00\x00\x00\x00"
    tlv.parse(test_bytes)
    assert tlv.valid_message
    assert tlv.bytestring == test_bytes


def test_tlv_parsing_tlv_data_zero(tlv: MessageValue) -> None:
    test_bytes = b"\x40\x00"
    tlv.parse(test_bytes)
    assert tlv.get("Tag") == "Msg_Data"
    assert tlv.get("Length") == 0
    assert tlv.valid_message


def test_tlv_parsing_tlv_error(tlv: MessageValue) -> None:
    test_bytes = b"\xc0"
    tlv.parse(test_bytes)
    assert tlv.get("Tag") == "Msg_Error"
    assert tlv.valid_message


def test_tlv_parsing_invalid_tlv_invalid_tag(tlv: MessageValue) -> None:
    test_bytes = b"\x00\x00"
    with pytest.raises(
        ValueError,
        match="Error while setting value for field Tag: 'Number 0 is not a valid enum value'",
    ):
        tlv.parse(test_bytes)
    assert not tlv.valid_message


def test_tlv_generating_tlv_data(tlv: MessageValue) -> None:
    expected = b"\x40\x04\x00\x00\x00\x00"
    tlv.set("Tag", "Msg_Data")
    tlv.set("Length", 4)
    tlv.set("Value", b"\x00\x00\x00\x00")
    assert tlv.valid_message
    assert tlv.bytestring == expected


def test_tlv_generating_tlv_data_zero(tlv: MessageValue) -> None:
    expected = b"\x40\x00"
    tlv.set("Tag", "Msg_Data")
    tlv.set("Length", 0)
    assert not tlv.valid_message
    assert tlv.bytestring == expected


def test_tlv_generating_tlv_error(tlv: MessageValue) -> None:
    tlv.set("Tag", "Msg_Error")
    assert tlv.valid_message
    assert tlv.bytestring == b"\xc0"
