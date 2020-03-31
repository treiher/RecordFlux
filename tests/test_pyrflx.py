import itertools
import unittest
from tempfile import TemporaryDirectory

from rflx import model
from rflx.expression import UNDEFINED, Expr
from rflx.model import (
    FINAL,
    INITIAL,
    Enumeration,
    ModularInteger,
    Number,
    Opaque,
    RangeInteger,
    Type,
)
from rflx.pyrflx import (
    EnumValue,
    Field,
    IntegerValue,
    Message,
    NotInitializedError,
    OpaqueValue,
    Package,
    PyRFLX,
    TypeValue,
)
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-lines
from rflx.pyrflx.bitstring import Bitstring


class TestPyRFLX(unittest.TestCase):
    testdir: str
    specdir: str
    package_tlv_checksum: Package
    packe_tlv: Package
    package_ethernet: Package
    package_tls_record: Package
    package_tls_alert: Package
    package_icmp: Package
    package_test_odd_length: Package
    package_ipv4: Package
    package_array_typevalue: Package
    package_array_nested_msg: Package
    package_udp: Package

    @classmethod
    def setUpClass(cls) -> None:
        cls.testdir = "tests"
        cls.specdir = "specs"
        pyrflx = PyRFLX(
            [
                f"{cls.testdir}/tlv_with_checksum.rflx",
                f"{cls.specdir}/ethernet.rflx",
                f"{cls.specdir}/tls_record.rflx",
                f"{cls.specdir}/tls_alert.rflx",
                f"{cls.specdir}/icmp.rflx",
                f"{cls.testdir}/test_odd_length.rflx",
                f"{cls.specdir}/ipv4.rflx",
                f"{cls.testdir}/array_message.rflx",
                f"{cls.testdir}/array_type.rflx",
                f"{cls.specdir}/udp.rflx",
                f"{cls.specdir}/tlv.rflx",
            ]
        )
        # einzelne Packages
        cls.package_tlv_checksum = pyrflx["TLV_Checksum"]
        cls.package_ethernet = pyrflx["Ethernet"]
        cls.package_tls_record = pyrflx["TLS_Record"]
        cls.package_tls_alert = pyrflx["TLS_Alert"]
        cls.package_icmp = pyrflx["ICMP"]
        cls.package_test_odd_length = pyrflx["TEST"]
        cls.package_ipv4 = pyrflx["IPv4"]
        cls.package_array_nested_msg = pyrflx["Test_Array_Message"]
        cls.package_array_typevalue = pyrflx["Test_Array_TypeValue"]
        cls.package_udp = pyrflx["UDP"]
        cls.package_tlv = pyrflx["TLV"]

    def setUp(self) -> None:
        # Messages
        self.tlv_checksum = self.package_tlv_checksum["Message"]
        self.tlv = self.package_tlv["Message"]
        self.frame = self.package_ethernet["Frame"]
        self.record = self.package_tls_record["TLS_Record"]
        self.alert = self.package_tls_alert["Alert"]
        self.icmp = self.package_icmp["Echo_Message"]
        self.odd_length = self.package_test_odd_length["Test"]
        self.ipv4 = self.package_ipv4["Packet"]
        self.ipv4_option = self.package_ipv4["Option"]
        self.array_test_nested_msg = self.package_array_nested_msg["Bars"]
        self.array_test_typeval = self.package_array_typevalue["Foo"]
        self.udp = self.package_udp["Datagram"]

    def test_file_not_found(self) -> None:
        with self.assertRaises(FileNotFoundError):
            with TemporaryDirectory() as tmpdir:
                PyRFLX([f"{tmpdir}/test.rflx"])

    def test_message_eq(self) -> None:
        m1 = self.package_tlv["Message"]
        self.assertEqual(m1, self.package_tlv["Message"])
        self.assertIsNot(m1, self.package_tlv["Message"])
        self.assertEqual(self.package_tlv["Message"], self.package_tlv["Message"])
        self.assertIsNot(self.package_tlv["Message"], self.package_tlv["Message"])
        self.assertNotEqual(m1, None)

    def test_attributes(self) -> None:
        pyrflx = PyRFLX([f"{self.testdir}/tlv_with_checksum.rflx"])
        self.assertIsInstance(pyrflx["TLV_Checksum"], Package)
        package_tlv = pyrflx["TLV_Checksum"]
        self.assertIsInstance(package_tlv["Message"], Message)

    def test_all_fields(self) -> None:
        self.assertEqual(self.tlv_checksum.fields, ["Tag", "Length", "Value", "Checksum"])

    def test_initial_fields(self) -> None:
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag"])

    def test_tag_fields(self) -> None:
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag", "Length"])

    def test_length_fields(self) -> None:
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 1)
        self.assertEqual(
            self.tlv_checksum.accessible_fields, ["Tag", "Length", "Value", "Checksum"]
        )
        self.tlv_checksum.set("Value", b"\x01")
        self.assertEqual(
            self.tlv_checksum.accessible_fields, ["Tag", "Length", "Value", "Checksum"]
        )

    def test_error_fields(self) -> None:
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag"])

    def test_error_reset_fields(self) -> None:
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 1)
        self.assertEqual(
            self.tlv_checksum.accessible_fields, ["Tag", "Length", "Value", "Checksum"]
        )
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag"])

    def test_fields_complex(self) -> None:
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag"])
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag"])
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag", "Length"])
        self.tlv_checksum.set("Length", 1)
        self.assertEqual(
            self.tlv_checksum.accessible_fields, ["Tag", "Length", "Value", "Checksum"]
        )
        self.tlv_checksum.set("Value", b"\x01")
        self.assertEqual(
            self.tlv_checksum.accessible_fields, ["Tag", "Length", "Value", "Checksum"]
        )
        self.tlv_checksum.set("Checksum", 0xFFFFFFFF)
        self.assertEqual(
            self.tlv_checksum.accessible_fields, ["Tag", "Length", "Value", "Checksum"]
        )
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertEqual(self.tlv_checksum.accessible_fields, ["Tag"])

    def test_valid_message(self) -> None:
        self.assertFalse(self.tlv_checksum.valid_message)
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertTrue(self.tlv_checksum.valid_message)
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertFalse(self.tlv_checksum.valid_message)
        self.tlv_checksum.set("Length", 1)
        self.assertFalse(self.tlv_checksum.valid_message)
        self.tlv_checksum.set("Value", b"\x01")
        self.assertFalse(self.tlv_checksum.valid_message)
        self.tlv_checksum.set("Checksum", 0xFFFFFFFF)
        self.assertTrue(self.tlv_checksum.valid_message)

    def test_valid_fields(self) -> None:
        self.assertEqual(self.tlv_checksum.valid_fields, [])
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertEqual(self.tlv_checksum.valid_fields, ["Tag"])
        self.tlv_checksum.set("Length", 1)
        self.assertEqual(self.tlv_checksum.valid_fields, ["Tag", "Length"])
        self.tlv_checksum.set("Value", b"\x01")
        self.assertEqual(self.tlv_checksum.valid_fields, ["Tag", "Length", "Value"])
        self.tlv_checksum.set("Checksum", 0xFFFFFFFF)
        self.assertEqual(self.tlv_checksum.valid_fields, ["Tag", "Length", "Value", "Checksum"])

    def test_set_value(self) -> None:
        v1 = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        v2 = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10"
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 8)
        self.tlv_checksum.set("Value", v1)
        with self.assertRaisesRegex(ValueError, "invalid data length: 64 != 80"):
            self.tlv_checksum.set("Value", v2)

    def test_tlv_message(self) -> None:
        v1 = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 8)
        self.tlv_checksum.set("Value", v1)
        self.tlv_checksum.set("Checksum", 2 ** 32 - 1)

    def test_tlv_generate(self) -> None:
        test_payload = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        test_data = b"\x40\x08" + test_payload + b"\xff\xff\xff\xff"
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 8)
        self.tlv_checksum.set("Value", test_payload)
        self.tlv_checksum.set("Checksum", 0xFFFFFFFF)
        self.assertEqual(self.tlv_checksum.binary, test_data)

    def test_tlv_change_field(self) -> None:
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 1)
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertIn("Length", self.tlv_checksum.valid_fields)
        self.tlv_checksum.set("Value", b"a")
        self.tlv_checksum.set("Checksum", 0)
        self.tlv_checksum.set("Length", 2)
        self.assertNotIn("Value", self.tlv_checksum.valid_fields)
        self.assertNotIn("Checksum", self.tlv_checksum.valid_fields)
        self.tlv_checksum.set("Value", b"ab")
        self.assertIn("Checksum", self.tlv_checksum.valid_fields)

    def test_tlv_binary_length(self) -> None:
        # pylint: disable=pointless-statement
        self.tlv_checksum.set("Tag", "Msg_Data")
        with self.assertRaisesRegex(ValueError, r"message length must be dividable by 8 \(2\)"):
            self.tlv_checksum.binary
        self.tlv_checksum.set("Length", 8)
        self.assertEqual(self.tlv_checksum.binary, b"\x40\x08")

    def test_tlv_value(self) -> None:
        v1 = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 8)
        self.tlv_checksum.set("Value", v1)
        self.tlv_checksum.set("Checksum", 2 ** 32 - 1)
        self.assertEqual(self.tlv_checksum.get("Tag"), "Msg_Data")
        self.assertEqual(self.tlv_checksum.get("Length"), 8)
        self.assertEqual(self.tlv_checksum.get("Value"), v1)
        self.assertEqual(self.tlv_checksum.get("Checksum"), 0xFFFFFFFF)

    def test_tlv_get_invalid_field(self) -> None:
        with self.assertRaisesRegex(ValueError, r"field nofield not valid"):
            self.tlv_checksum.get("nofield")

    def test_tlv_set_invalid_field(self) -> None:
        self.tlv_checksum.set("Tag", "Msg_Data")
        with self.assertRaisesRegex(KeyError, r"cannot access field Value"):
            self.tlv_checksum.set("Value", b"")
        with self.assertRaisesRegex(KeyError, r"cannot access field Checksum"):
            self.tlv_checksum.set("Checksum", 8)
        self.tlv_checksum.set("Tag", "Msg_Error")
        with self.assertRaisesRegex(KeyError, r"cannot access field Length"):
            self.tlv_checksum.set("Length", 8)

    def test_tlv_invalid_value(self) -> None:
        with self.assertRaisesRegex(TypeError, r"cannot assign different types: str != int"):
            self.tlv_checksum.set("Tag", 1)
        self.tlv_checksum.set("Tag", "Msg_Data")
        with self.assertRaisesRegex(TypeError, r"cannot assign different types: int != str"):
            self.tlv_checksum.set("Length", "blubb")

    def test_tlv_next(self) -> None:
        # pylint: disable=protected-access
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertEqual(self.tlv_checksum._next_field(INITIAL.name), "Tag")
        self.assertEqual(self.tlv_checksum._next_field("Tag"), "Length")
        self.assertEqual(self.tlv_checksum._next_field(FINAL.name), "")

    def test_tlv_prev(self) -> None:
        # pylint: disable=protected-access
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertEqual(self.tlv_checksum._prev_field("Tag"), INITIAL.name)
        self.assertEqual(self.tlv_checksum._prev_field(INITIAL.name), "")
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertEqual(self.tlv_checksum._prev_field("Length"), "")

    def test_tlv_required_fields(self) -> None:
        self.assertEqual(self.tlv_checksum.required_fields, ["Tag"])
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertEqual(self.tlv_checksum.required_fields, ["Length"])
        self.tlv_checksum.set("Length", 1)
        self.assertEqual(self.tlv_checksum.required_fields, ["Value", "Checksum"])
        self.tlv_checksum.set("Value", b"\x01")
        self.assertEqual(self.tlv_checksum.required_fields, ["Checksum"])
        self.tlv_checksum.set("Checksum", 0xFFFFFFFF)
        self.assertEqual(self.tlv_checksum.required_fields, [])

    def test_tlv_length_unchecked(self) -> None:
        # pylint: disable=protected-access
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertNotIsInstance(self.tlv_checksum._get_length_unchecked("Value"), Number)
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertNotIsInstance(self.tlv_checksum._get_length_unchecked("Value"), Number)
        self.tlv_checksum.set("Length", 1)
        self.assertIsInstance(self.tlv_checksum._get_length_unchecked("Value"), Number)

    def test_tlv_first_unchecked(self) -> None:
        # pylint: disable=protected-access
        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertNotIsInstance(self.tlv_checksum._get_first_unchecked("Checksum"), Number)
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.assertNotIsInstance(self.tlv_checksum._get_first_unchecked("Checksum"), Number)
        self.tlv_checksum.set("Length", 1)
        self.assertIsInstance(self.tlv_checksum._get_first_unchecked("Checksum"), Number)

    def test_ethernet_all_fields(self) -> None:
        self.assertEqual(
            self.frame.fields,
            ["Destination", "Source", "Type_Length_TPID", "TPID", "TCI", "Type_Length", "Payload"],
        )

    def test_ethernet_initial(self) -> None:
        self.assertEqual(
            self.frame.accessible_fields, ["Destination", "Source", "Type_Length_TPID"]
        )

    def test_ethernet_set_tltpid(self) -> None:
        self.frame.set("Destination", 0)
        self.frame.set("Source", 1)
        self.frame.set("Type_Length_TPID", 0x8100)
        self.assertEqual(self.frame.valid_fields, ["Destination", "Source", "Type_Length_TPID"])
        self.assertEqual(
            self.frame.accessible_fields,
            ["Destination", "Source", "Type_Length_TPID", "TPID", "TCI", "Type_Length"],
        )
        self.frame.set("Type_Length_TPID", 64)
        self.assertEqual(self.frame.valid_fields, ["Destination", "Source", "Type_Length_TPID"])
        self.assertEqual(
            self.frame.accessible_fields,
            ["Destination", "Source", "Type_Length_TPID", "Type_Length"],
        )

    def test_ethernet_set_nonlinear(self) -> None:
        self.assertEqual(
            self.frame.accessible_fields, ["Destination", "Source", "Type_Length_TPID"]
        )
        self.frame.set("Type_Length_TPID", 0x8100)
        self.frame.set("TCI", 100)
        self.assertEqual(self.frame.valid_fields, ["Type_Length_TPID", "TCI"])

    def test_ethernet_final(self) -> None:
        self.assertFalse(self.frame.valid_message)
        self.frame.set("Destination", 0)
        self.assertFalse(self.frame.valid_message)
        self.frame.set("Source", 1)
        self.assertFalse(self.frame.valid_message)
        self.frame.set("Type_Length_TPID", 46)
        self.assertFalse(self.frame.valid_message)
        self.frame.set("Type_Length", 46)
        self.assertFalse(self.frame.valid_message)
        self.frame.set("Payload", bytes(46))
        self.assertTrue(self.frame.valid_message)

    def test_ethernet_802_3(self) -> None:
        self.frame.set("Destination", 2 ** 48 - 1)
        self.frame.set("Source", 0)
        self.frame.set("Type_Length_TPID", 46)
        self.frame.set("Type_Length", 46)
        self.frame.set(
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
        self.assertTrue(self.frame.valid_message)
        with open(f"{self.testdir}/ethernet_802.3.raw", "rb") as raw:
            self.assertEqual(self.frame.binary, raw.read())

    def test_ethernet_payload(self) -> None:
        self.frame.set("Source", 0)
        self.frame.set("Destination", 0)
        self.frame.set("Type_Length_TPID", 47)
        self.frame.set("Type_Length", 1537)
        self.assertEqual(
            self.frame.accessible_fields,
            ["Destination", "Source", "Type_Length_TPID", "Type_Length", "Payload"],
        )
        self.frame.set("Payload", bytes(46))
        self.assertTrue(self.frame.valid_message)

    def test_ethernet_invalid(self) -> None:
        self.frame.set("Destination", 2 ** 48 - 1)
        self.frame.set("Source", 0)
        self.frame.set("Type_Length_TPID", 1501)
        with self.assertRaisesRegex(ValueError, "value does not fulfill field condition"):
            self.frame.set("Type_Length", 1501)

    def test_tls_fields(self) -> None:
        self.assertEqual(self.record.accessible_fields, ["Tag", "Legacy_Record_Version", "Length"])
        self.record.set("Tag", "INVALID")
        self.record.set("Length", 3)
        self.assertEqual(
            self.record.accessible_fields, ["Tag", "Legacy_Record_Version", "Length", "Fragment"]
        )

    def test_tls_invalid_outgoing(self) -> None:
        self.record.set("Tag", "INVALID")
        with self.assertRaisesRegex(ValueError, "value does not fulfill field condition"):
            self.record.set("Length", 2 ** 14 + 1)

    def test_tls_invalid_path(self) -> None:
        self.alert.set("Level", "WARNING")
        self.alert.set("Description", "CLOSE_NOTIFY")
        self.assertTrue(self.alert.valid_message)
        self.assertEqual(self.alert.valid_fields, ["Level", "Description"])
        self.alert.set("Level", "FATAL")
        self.assertFalse(self.alert.valid_message)
        self.assertEqual(self.alert.valid_fields, ["Level"])

    def test_tls_length_unchecked(self) -> None:
        # pylint: disable=protected-access
        self.record.set("Tag", "APPLICATION_DATA")
        self.record.set("Legacy_Record_Version", "TLS_1_2")
        self.assertNotIsInstance(self.record._get_length_unchecked("Fragment"), Number)

    def test_icmp_echo_request(self) -> None:
        test_data = (
            b"\x4a\xfc\x0d\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17"
            b"\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27"
            b"\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37"
        )

        self.icmp.set("Tag", "Echo_Request")
        self.icmp.set("Code", 0)
        self.icmp.set("Checksum", 12824)
        self.icmp.set("Identifier", 5)
        self.icmp.set("Sequence_Number", 1)
        self.icmp.set(
            "Data", test_data,
        )
        self.assertEqual(self.icmp.binary, b"\x08\x00\x32\x18\x00\x05\x00\x01" + test_data)
        self.assertTrue(self.icmp.valid_message)

    def test_value_mod(self) -> None:
        # pylint: disable=pointless-statement
        modtype = ModularInteger("Test.Int", Number(2 ** 16))
        modvalue = IntegerValue(modtype)
        self.assertFalse(modvalue.initialized)
        with self.assertRaisesRegex(NotInitializedError, "value not initialized"):
            modvalue.value
        with self.assertRaisesRegex(NotInitializedError, "value not initialized"):
            modvalue.expr
        modvalue.assign(128)
        self.assertTrue(modvalue.initialized)
        self.assertEqual(modvalue.value, 128)
        self.assertEqual(modvalue.binary, "0000000010000000")
        with self.assertRaisesRegex(ValueError, r"value 65536 not in type range 0 .. 65535"):
            modvalue.assign(2 ** 16)
        with self.assertRaisesRegex(ValueError, r"value -1 not in type range 0 .. 65535"):
            modvalue.assign(-1)

    def test_value_range(self) -> None:
        # pylint: disable=pointless-statement
        rangetype = RangeInteger("Test.Int", Number(8), Number(16), Number(8))
        rangevalue = IntegerValue(rangetype)
        self.assertFalse(rangevalue.initialized)
        with self.assertRaisesRegex(NotInitializedError, "value not initialized"):
            rangevalue.value
        with self.assertRaisesRegex(NotInitializedError, "value not initialized"):
            rangevalue.expr
        rangevalue.assign(10)
        self.assertTrue(rangevalue.initialized)
        self.assertEqual(rangevalue.value, 10)
        self.assertEqual(rangevalue.binary, "00001010")
        with self.assertRaisesRegex(ValueError, r"value 17 not in type range 8 .. 16"):
            rangevalue.assign(17)
        with self.assertRaisesRegex(ValueError, r"value 7 not in type range 8 .. 16"):
            rangevalue.assign(7)

    def test_value_enum(self) -> None:
        # pylint: disable=pointless-statement
        enumtype = Enumeration("Test.Enum", {"One": Number(1), "Two": Number(2)}, Number(8), False)
        enumvalue = EnumValue(enumtype)
        self.assertFalse(enumvalue.initialized)
        with self.assertRaisesRegex(NotInitializedError, "value not initialized"):
            enumvalue.value
        with self.assertRaisesRegex(NotInitializedError, "value not initialized"):
            enumvalue.expr
        enumvalue.assign("One")
        self.assertTrue(enumvalue.initialized)
        self.assertEqual(enumvalue.value, "One")
        self.assertEqual(enumvalue.binary, "00000001")
        with self.assertRaisesRegex(KeyError, r"Three is not a valid enum value"):
            enumvalue.assign("Three")
        with self.assertRaisesRegex(KeyError, r"Number 15 is not a valid enum value"):
            enumvalue.assign_bitvalue(Bitstring("1111"), True)

    def test_value_opaque(self) -> None:
        # pylint: disable=pointless-statement
        # pylint: disable=protected-access
        opaquevalue = OpaqueValue(Opaque())
        self.assertFalse(opaquevalue.initialized)
        with self.assertRaisesRegex(NotInitializedError, "value not initialized"):
            opaquevalue.value
        opaquevalue.assign(b"\x01\x02")
        self.assertTrue(opaquevalue.initialized)
        self.assertEqual(opaquevalue.value, b"\x01\x02")
        self.assertEqual(opaquevalue.length, 16)
        self.assertEqual(opaquevalue.binary, "0000000100000010")
        opaquevalue.assign_bitvalue(Bitstring("1111"), True)
        self.assertEqual(opaquevalue._value, b"\x0f")

    def test_value_equal(self) -> None:
        ov = OpaqueValue(Opaque())
        enumtype = Enumeration("Test.Enum", {"One": Number(1), "Two": Number(2)}, Number(8), False)
        ev = EnumValue(enumtype)
        rangetype = RangeInteger("Test.Int", Number(8), Number(16), Number(8))
        rv = IntegerValue(rangetype)
        modtype = ModularInteger("Test.Int", Number(2 ** 16))
        mv = IntegerValue(modtype)
        mv2 = IntegerValue(modtype)
        self.assertEqual(ov, ov)
        self.assertEqual(ev, ev)
        self.assertEqual(rv, rv)
        self.assertEqual(mv, mv)
        self.assertNotEqual(ev, rv)
        self.assertEqual(mv, mv2)
        mv.assign(2)
        self.assertNotEqual(mv, mv2)
        mv2.assign(10)
        self.assertNotEqual(mv, mv2)
        mv.assign(10)
        self.assertEqual(mv, mv2)
        rv.assign(10)
        self.assertNotEqual(mv, rv)

    def test_value_clear(self) -> None:
        ov = OpaqueValue(Opaque())
        self.assertFalse(ov.initialized)
        ov.assign(b"", True)
        self.assertTrue(ov.initialized)
        ov.clear()
        self.assertFalse(ov.initialized)

    def test_value_invalid(self) -> None:
        class TestType(Type):
            @property
            def size(self) -> Expr:
                return UNDEFINED

            def constraints(self, name: str, proof: bool = False) -> Expr:
                return UNDEFINED

        t = TestType("Test.Type")
        with self.assertRaisesRegex(ValueError, "cannot construct unknown type: TestType"):
            TypeValue.construct(t, [])

    def test_field_eq(self) -> None:
        f1 = Field(OpaqueValue(Opaque()))
        self.assertEqual(f1, Field(OpaqueValue(Opaque())))
        f1.typeval.assign(b"", True)
        self.assertNotEqual(f1, Field(OpaqueValue(Opaque())))
        self.assertNotEqual(f1, None)

    def test_field_set(self) -> None:
        f = Field(OpaqueValue(Opaque()))
        self.assertFalse(f.set)
        f.typeval.assign(b"", True)
        self.assertFalse(f.set)
        f.first = Number(1)
        self.assertFalse(f.set)
        f.length = Number(2)
        self.assertTrue(f.set)

    def test_package_name(self) -> None:
        p = Package("Test")
        self.assertEqual(p.name, "Test")

    def test_package_iterator(self) -> None:
        self.assertEqual([m.name for m in self.package_tlv], ["Message"])

    def test_tlv_get_first_unchecked_undefined(self) -> None:
        # pylint: disable=protected-access
        self.assertEqual(self.tlv_checksum._get_first_unchecked("Length"), UNDEFINED)

    def test_check_nodes_opaque(self) -> None:
        # pylint: disable=protected-access
        self.assertFalse(self.tlv_checksum._check_nodes_opaque("Length"))
        self.assertTrue(self.tlv_checksum._check_nodes_opaque("Value"))

        self.frame.set("Destination", 2 ** 48 - 1)
        self.frame.set("Source", 0)
        self.frame.set("Type_Length_TPID", 1501)
        self.frame._fields["Type_Length"].typeval.assign(1501, True)

        self.assertTrue(self.frame._check_nodes_opaque("Payload"))

    def test_icmp_parse_binary(self) -> None:
        test_bytes = (
            b"\x08\x00\xe1\x1e\x00\x11\x00\x01\x4a\xfc\x0d\x00\x00\x00\x00\x00"
            b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
            b"\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f"
            b"\x30\x31\x32\x33\x34\x35\x36\x37"
        )

        self.icmp.parse_from_bytes(test_bytes)
        self.assertTrue(self.icmp.valid_message)
        self.assertEqual(self.icmp.binary, test_bytes)

    def test_ethernet_parse_binary(self) -> None:
        test_bytes = (
            b"\xe0\x28\x6d\x39\x80\x1e\x1c\x1b\x0d\xe0\xd8\xa8\x08\x00\x45\x00"
            b"\x00\x4c\x1f\x04\x40\x00\x40\x01\xe1\x6a\xc0\xa8\xbc\x3d\xac\xd9"
            b"\x10\x83\x08\x00\xe1\x26\x00\x09\x00\x01\x4a\xfc\x0d\x00\x00\x00"
            b"\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d"
            b"\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d"
            b"\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37"
        )

        self.frame.parse_from_bytes(test_bytes)
        self.assertTrue(self.frame.valid_message)
        self.assertEqual(self.frame.binary, test_bytes)

    def test_tlv_checksum_binary(self) -> None:
        test_bytes = b"\x01"
        self.tlv_checksum.parse_from_bytes(test_bytes, 2)
        self.assertFalse(self.tlv_checksum.valid_message)

    def test_odd_length_binary(self) -> None:
        test_bytes = b"\x01\x02\x01\xff\xb8"
        self.odd_length.parse_from_bytes(test_bytes)
        self.assertTrue(self.odd_length.valid_message)

    def test_parsing_ethernet_2(self) -> None:

        with open(f"tests/ethernet_ipv4_udp.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.frame.parse_from_bytes(msg_as_bytes)

        self.assertEqual(int("ffffffffffff", 16), self.frame.get("Destination"))
        self.assertEqual(int("0", 16), self.frame.get("Source"))
        self.assertEqual(int("0800", 16), self.frame.get("Type_Length_TPID"))
        self.assertEqual(46, self.frame._fields["Payload"].length.value // 8)

        self.assertTrue(self.frame.valid_message)
        self.assertEqual(msg_as_bytes, self.frame.binary)

    def test_parsing_ieee_802_3(self) -> None:

        with open(f"tests/ethernet_802.3.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.frame.parse_from_bytes(msg_as_bytes)
        self.assertTrue(self.frame.valid_message)
        self.assertEqual(self.frame.binary, msg_as_bytes)

    def test_parsing_ethernet_2_vlan(self) -> None:

        with open(f"tests/ethernet_vlan_tag.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.frame.parse_from_bytes(msg_as_bytes)

        self.assertEqual(int("ffffffffffff", 16), self.frame.get("Destination"))
        self.assertEqual(int("0", 16), self.frame.get("Source"))
        self.assertEqual(int("8100", 16), self.frame.get("Type_Length_TPID"))
        self.assertEqual(int("8100", 16), self.frame.get("TPID"))
        self.assertEqual(int("1", 16), self.frame.get("TCI"))
        self.assertEqual(47, self.frame._fields["Payload"].length.value // 8)

        self.assertTrue(self.frame.valid_message)
        self.assertEqual(self.frame.binary, msg_as_bytes)

    def test_ethernet_invalid_ethernet_2_too_short(self) -> None:
        with open(f"tests/ethernet_invalid_too_short.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        with self.assertRaisesRegex(ValueError, "value does not fulfill field condition"):
            self.frame.parse_from_bytes(msg_as_bytes)

        self.assertFalse(self.frame.valid_message)

    def test_ethernet_invalid_ethernet_2_too_long(self) -> None:

        with open("tests/ethernet_invalid_too_long.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        with self.assertRaisesRegex(ValueError, "value does not fulfill field condition"):
            self.frame.parse_from_bytes(msg_as_bytes)

        self.assertFalse(self.frame.valid_message)

    def test_parsing_invalid_ethernet_2_undefined_type(self) -> None:

        with open("tests/ethernet_undefined.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        with self.assertRaisesRegex(ValueError, "value does not fulfill field condition"):
            self.frame.parse_from_bytes(msg_as_bytes)

        self.assertFalse(self.frame.valid_message)

    def test_ethernet_ieee_802_3_invalid_length(self) -> None:

        # valid message, but not valid field
        with open(f"tests/ethernet_802.3_invalid_length.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        with self.assertRaisesRegex(ValueError, "invalid data length: 12000 != 368"):
            self.frame.parse_from_bytes(msg_as_bytes)

        self.assertFalse(self.frame.valid_message)

    def test_parsing_incomplete(self) -> None:

        test_bytes = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x02"

        self.frame.parse_from_bytes(test_bytes)

        self.assertEqual(int("000000000001", 16), self.frame.get("Destination"))
        self.assertEqual(int("000000000002", 16), self.frame.get("Source"))
        assert len(self.frame.valid_fields) == 2
        self.assertFalse(self.frame.valid_message)

    def test_generating_ethernet_2(self) -> None:

        payload = (
            b"\x45\x00\x00\x2e\x00\x01\x00\x00\x40\x11\x7c\xbc"
            b"\x7f\x00\x00\x01\x7f\x00\x00\x01\x00\x35\x00\x35"
            b"\x00\x1a\x01\x4e\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )

        self.frame.set("Destination", int("FFFFFFFFFFFF", 16))
        self.frame.set("Source", int("0", 16))
        self.frame.set("Type_Length_TPID", int("0800", 16))
        self.frame.set("Type_Length", int("0800", 16))
        self.frame.set("Payload", payload)

        with open("tests/ethernet_ipv4_udp.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.assertEqual(self.frame.binary, msg_as_bytes)

    def test_generating_ieee_802_3(self) -> None:

        payload = (
            b"\x45\x00\x00\x14\x00\x01\x00\x00\x40\x00\x7c\xe7"
            b"\x7f\x00\x00\x01\x7f\x00\x00\x01\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )

        self.frame.set("Destination", int("FFFFFFFFFFFF", 16))
        self.frame.set("Source", int("0", 16))
        self.frame.set("Type_Length_TPID", 46)
        self.frame.set("Type_Length", 46)
        self.frame.set("Payload", payload)

        self.assertTrue(self.frame.valid_message)

        with open("tests/ethernet_802.3.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.assertEqual(self.frame.binary, msg_as_bytes)

    def test_generating_ethernet_2_vlan(self) -> None:

        payload = (
            b"\x45\x00\x00\x14\x00\x01\x00\x00\x40\x00\x7c\xe7"
            b"\x7f\x00\x00\x01\x7f\x00\x00\x01\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a"
        )

        self.frame.set("Destination", int("FFFFFFFFFFFF", 16))
        self.frame.set("Source", int("0", 16))
        self.frame.set("Type_Length_TPID", int("8100", 16))
        self.frame.set("TPID", int("8100", 16))
        self.frame.set("TCI", 1)
        self.frame.set("Type_Length", int("0800", 16))
        self.frame.set("Payload", payload)

        self.assertTrue(self.frame.valid_message)

        with open("tests/ethernet_vlan_tag.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        print(self.frame.binary.hex())
        print(msg_as_bytes.hex())

        self.assertEqual(self.frame.binary, msg_as_bytes)

    def test_generating_ethernet_2_vlan_dynamic(self) -> None:
        pass

    # rflx-in_ethernet-test

    def test_parsing_ipv4_in_ethernet(self) -> None:
        pass

    def test_generating_ipv4_in_ethernet(self) -> None:
        pass

    # reflx-in_ipv4_test

    def test_parsing_udp_in_ipv4(self) -> None:
        pass

    def test_parsing_udp_in_ipv4_in_ethernet(self) -> None:
        pass

    def test_generating_udp_in_ipv4_in_ethernet(self) -> None:

        with open("tests/ethernet_ipv4_udp.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.frame.parse_from_bytes(msg_as_bytes)

        parsed_frame = self.frame.binary

        b = b""
        for _ in itertools.repeat(None, 18):
            b += b"\x00"

        self.udp.set("Source_Port", 53)
        self.udp.set("Destination_Port", 53)
        self.udp.set("Length", 26)
        self.udp.set("Checksum", int("014E", 16))
        self.udp.set("Payload", b)
        udp_binary = self.udp.binary

        self.ipv4.set("Version", 4)
        self.ipv4.set("IHL", 5)
        self.ipv4.set("DSCP", 0)
        self.ipv4.set("ECN", 0)
        self.ipv4.set("Total_Length", 46)
        self.ipv4.set("Identification", 1)
        self.ipv4.set("Flag_R", "False")
        self.ipv4.set("Flag_DF", "False")
        self.ipv4.set("Flag_MF", "False")
        self.ipv4.set("Fragment_Offset", 0)
        self.ipv4.set("TTL", 64)
        self.ipv4.set("Protocol", "PROTOCOL_UDP")
        self.ipv4.set("Header_Checksum", int("7CBC", 16))
        self.ipv4.set("Source", int("7f000001", 16))
        self.ipv4.set("Destination", int("7f000001", 16))
        self.ipv4.set("Payload", udp_binary)
        ip_binary = self.ipv4.binary

        self.frame.set("Destination", int("FFFFFFFFFFFF", 16))
        self.frame.set("Source", int("0", 16))
        self.frame.set("Type_Length_TPID", int("0800", 16))
        self.frame.set("Type_Length", int("0800", 16))
        self.frame.set("Payload", ip_binary)

        self.assertTrue(self.frame.valid_message)
        self.assertEqual(parsed_frame, self.frame.binary)

    # rflx-in_tlv-tests

    def test_null_in_tlv(self) -> None:
        pass

    # rflx ipv4 tests

    def test_parsing_ipv4(self) -> None:

        with open("tests/ipv4_udp.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.ipv4.parse_from_bytes(msg_as_bytes)

        self.assertEqual(self.ipv4.get("Version"), 4)
        self.assertEqual(self.ipv4.get("IHL"), 5)
        self.assertEqual(self.ipv4.get("DSCP"), 0)
        self.assertEqual(self.ipv4.get("ECN"), 0)
        self.assertEqual(self.ipv4.get("Total_Length"), 44)
        self.assertEqual(self.ipv4.get("Identification"), 1)
        self.assertEqual(self.ipv4.get("Flag_R"), "False")
        self.assertEqual(self.ipv4.get("Flag_DF"), "False")
        self.assertEqual(self.ipv4.get("Flag_MF"), "False")
        self.assertEqual(self.ipv4.get("Fragment_Offset"), 0)
        self.assertEqual(self.ipv4.get("TTL"), 64)
        self.assertEqual(self.ipv4.get("Protocol"), "PROTOCOL_UDP")
        self.assertEqual(self.ipv4.get("Header_Checksum"), int("7CBE", 16))
        self.assertEqual(self.ipv4.get("Source"), int("7f000001", 16))
        self.assertEqual(self.ipv4.get("Destination"), int("7f000001", 16))
        self.assertEqual(self.ipv4._fields["Payload"].length, Number(192))

    def test_parsing_ipv4_with_options(self) -> None:
        """
        with open("tests/ipv4-options_udp.raw", "rb") as file:
            msg_as_bytes: bytes = file.read()

        self.ipv4.parse_from_bytes(msg_as_bytes)

        for i in self.ipv4.get("Options"):
            self.assertTrue(i.valid_message)

        self.assertTrue(self.ipv4.valid_message)
        self.assertEqual(self.ipv4.binary, msg_as_bytes)
        """

    def test_parsing_ipv4_option(self) -> None:
        pass

    def test_generating_ipv4(self) -> None:

        data = (
            b"\x00\x35\x00\x35\x00\x18\x01\x52\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )

        self.ipv4.set("Version", 4)
        self.ipv4.set("IHL", 5)
        self.ipv4.set("DSCP", 0)
        self.ipv4.set("ECN", 0)
        self.ipv4.set("Total_Length", 44)
        self.ipv4.set("Identification", 1)
        self.ipv4.set("Flag_R", "False")
        self.ipv4.set("Flag_DF", "False")
        self.ipv4.set("Flag_MF", "False")
        self.ipv4.set("Fragment_Offset", 0)
        self.ipv4.set("TTL", 64)
        self.ipv4.set("Protocol", "PROTOCOL_UDP")
        self.ipv4.set("Header_Checksum", int("7CBE", 16))
        self.ipv4.set("Source", int("7f000001", 16))
        self.ipv4.set("Destination", int("7f000001", 16))
        self.ipv4.set("Payload", data)

        self.assertTrue(self.ipv4.valid_message)

    def test_generating_ipv4_option(self) -> None:

        self.ipv4_option.set("Copied", "False")
        self.ipv4_option.set("Option_Class", "Debugging_And_Measurement")
        self.ipv4_option.set("Option_Number", 4)
        self.ipv4_option.set("Option_Length", 3)
        self.ipv4_option.set("Option_Data", b"\x2a")

        self.assertTrue(self.ipv4_option.valid_message)

    # rflx tlv tests

    # works only with tlv not tlv_checksum
    def test_parsing_tlv_data(self) -> None:
        test_bytes = b"\x40\x04\x00\x00\x00\x00"
        self.tlv.parse_from_bytes(test_bytes)
        self.assertTrue(self.tlv.valid_message)
        self.assertEqual(test_bytes, self.tlv.binary)

    def test_parsing_tlv_data_zero(self) -> None:
        test_bytes = b"\x40\x00"
        self.tlv_checksum.parse_from_bytes(test_bytes)
        self.assertEqual(self.tlv_checksum.get("Tag"), "Msg_Data")
        self.assertEqual(self.tlv_checksum.get("Length"), 0)
        self.assertFalse(self.tlv_checksum.valid_message)

    def test_parsing_tlv_error(self) -> None:

        test_bytes = b"\xc0"
        self.tlv_checksum.parse_from_bytes(test_bytes)
        self.assertEqual(self.tlv_checksum.get("Tag"), "Msg_Error")
        self.assertTrue(self.tlv_checksum.valid_message)

    def test_parsing_invalid_tlv_invalid_tag(self) -> None:
        test_bytes = b"\x00\x00"
        with self.assertRaisesRegex(KeyError, "Number 0 is not a valid enum value"):
            self.tlv_checksum.parse_from_bytes(test_bytes)

    def test_generating_tlv_data(self) -> None:
        expected = b"\x40\x04\x00\x00\x00\x00"

        self.tlv.set("Tag", "Msg_Data")
        self.tlv.set("Length", 4)
        self.tlv.set("Value", b"\x00\x00\x00\x00")

        self.assertTrue(self.tlv.valid_message)
        self.assertEqual(self.tlv.binary, expected)

    def test_generating_tlv_data_zero(self) -> None:
        """
        expected = b"\x40\x00"
        self.tlv_checksum.set("Tag", "Msg_Data")
        self.tlv_checksum.set("Length", 0)

        # Die Nachricht kann nicht valid werden, da Value nicht gesetzt werden
        # kann, weil Length 0 ist
        # self.tlv.set("Value", b"\x00\x00\x00\x00")

        self.assertTrue(self.tlv_checksum.valid_message)
        self.assertEqual(self.tlv_checksum.binary, expected)
        """

    def test_generating_tlv_error(self) -> None:

        self.tlv_checksum.set("Tag", "Msg_Error")
        self.assertTrue(self.tlv_checksum.valid_message)

    def test_array_parse_form_bytes(self) -> None:

        self.array_test_nested_msg.parse_from_bytes(b"\x02\x05\x06")
        self.assertEqual(self.array_test_nested_msg.binary, b"\x02\x05\x06")
        self.array_test_typeval.parse_from_bytes(b"\x03\x05\x06\x07")
        self.assertEqual(self.array_test_typeval.binary, b"\x03\x05\x06\x07")

    def test_array_nested_messages(self) -> None:

        array_message_one = self.package_array_nested_msg["Foo"]
        array_message_two = self.package_array_nested_msg["Foo"]

        array_message_one.set("Byte", 5)
        array_message_two.set("Byte", 6)

        foos = [array_message_one, array_message_two]

        self.array_test_nested_msg.set("Length", 2)
        self.array_test_nested_msg.set("Bars", foos)

        self.assertTrue(self.array_test_nested_msg.valid_message)
        self.assertEqual(b"\x02\x05\x06", self.array_test_nested_msg.binary)

    def test_array_typevalues(self) -> None:

        a = IntegerValue(model.ModularInteger("Test_Array_TypeValue.Byte_One", Number(256)))
        b = IntegerValue(model.ModularInteger("Test_Array_TypeValue.Byte_Two", Number(256)))
        c = IntegerValue(model.ModularInteger("Test_Array_TypeValue.Byte_Three", Number(256)))
        a.assign(5)
        b.assign(6)
        c.assign(7)

        byte_array = [a, b, c]

        self.array_test_typeval.set("Length", 3)
        self.array_test_typeval.set("Byte", byte_array)

        self.assertTrue(self.array_test_typeval.valid_message)
        self.assertEqual(self.array_test_typeval.binary, b"\x03\x05\x06\x07")
