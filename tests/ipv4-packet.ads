package IPv4.Packet
  with SPARK_Mode
is

   pragma Warnings (Off, "precondition is statically false");

   function Unreachable_Version_Type return Version_Type is
      (Version_Type'First)
     with
       Pre => False;

   function Unreachable_IHL_Type return IHL_Type is
      (IHL_Type'First)
     with
       Pre => False;

   function Unreachable_DCSP_Type return DCSP_Type is
      (DCSP_Type'First)
     with
       Pre => False;

   function Unreachable_ECN_Type return ECN_Type is
      (ECN_Type'First)
     with
       Pre => False;

   function Unreachable_Total_Length_Type return Total_Length_Type is
      (Total_Length_Type'First)
     with
       Pre => False;

   function Unreachable_Identification_Type return Identification_Type is
      (Identification_Type'First)
     with
       Pre => False;

   function Unreachable_Flag_Type return Flag_Type is
      (Flag_Type'First)
     with
       Pre => False;

   function Unreachable_Fragment_Offset_Type return Fragment_Offset_Type is
      (Fragment_Offset_Type'First)
     with
       Pre => False;

   function Unreachable_TTL_Type return TTL_Type is
      (TTL_Type'First)
     with
       Pre => False;

   function Unreachable_Protocol_Type return Protocol_Type is
      (Protocol_Type'First)
     with
       Pre => False;

   function Unreachable_Header_Checksum_Type return Header_Checksum_Type is
      (Header_Checksum_Type'First)
     with
       Pre => False;

   function Unreachable_Address_Type return Address_Type is
      (Address_Type'First)
     with
       Pre => False;

   function Unreachable_Natural return Natural is
      (Natural'First)
     with
       Pre => False;

   pragma Warnings (On, "precondition is statically false");

   function Is_Contained (Buffer : Bytes) return Boolean
     with
       Ghost,
       Import;

   procedure Initialize (Buffer : Bytes)
     with
       Post => Is_Contained (Buffer);

   function Valid_Version_0 (Buffer : Bytes) return Boolean is
      (((Buffer'Length >= 1 and then Buffer'First <= (Natural'Last / 2)) and then (Convert_To_Version_Type_Base (Buffer (Buffer'First .. Buffer'First), 4) >= 4 and then Convert_To_Version_Type_Base (Buffer (Buffer'First .. Buffer'First), 4) <= 4)))
     with
       Pre => Is_Contained (Buffer);

   function Version_0 (Buffer : Bytes) return Version_Type is
      (Convert_To_Version_Type_Base (Buffer (Buffer'First .. Buffer'First), 4))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Version_0 (Buffer));

   function Valid_Version (Buffer : Bytes) return Boolean is
      (Valid_Version_0 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Version (Buffer : Bytes) return Version_Type is
      ((if Valid_Version_0 (Buffer) then Version_0 (Buffer) else Unreachable_Version_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Version (Buffer));

   function Valid_IHL_00 (Buffer : Bytes) return Boolean is
      ((Valid_Version_0 (Buffer) and then ((Buffer'Length >= 1 and then Buffer'First <= (Natural'Last / 2)) and then Convert_To_IHL_Type_Base (Buffer (Buffer'First .. Buffer'First)) >= 5)))
     with
       Pre => Is_Contained (Buffer);

   function IHL_00 (Buffer : Bytes) return IHL_Type is
      (Convert_To_IHL_Type_Base (Buffer (Buffer'First .. Buffer'First)))
     with
       Pre => (Is_Contained (Buffer) and then Valid_IHL_00 (Buffer));

   function Valid_IHL (Buffer : Bytes) return Boolean is
      (Valid_IHL_00 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function IHL (Buffer : Bytes) return IHL_Type is
      ((if Valid_IHL_00 (Buffer) then IHL_00 (Buffer) else Unreachable_IHL_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_IHL (Buffer));

   function Valid_DSCP_000 (Buffer : Bytes) return Boolean is
      ((Valid_IHL_00 (Buffer) and then (Buffer'Length >= 2 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function DSCP_000 (Buffer : Bytes) return DCSP_Type is
      (Convert_To_DCSP_Type (Buffer ((Buffer'First + 1) .. (Buffer'First + 1)), 2))
     with
       Pre => (Is_Contained (Buffer) and then Valid_DSCP_000 (Buffer));

   function Valid_DSCP (Buffer : Bytes) return Boolean is
      (Valid_DSCP_000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function DSCP (Buffer : Bytes) return DCSP_Type is
      ((if Valid_DSCP_000 (Buffer) then DSCP_000 (Buffer) else Unreachable_DCSP_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_DSCP (Buffer));

   function Valid_ECN_0000 (Buffer : Bytes) return Boolean is
      ((Valid_DSCP_000 (Buffer) and then (Buffer'Length >= 2 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function ECN_0000 (Buffer : Bytes) return ECN_Type is
      (Convert_To_ECN_Type (Buffer ((Buffer'First + 1) .. (Buffer'First + 1))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_ECN_0000 (Buffer));

   function Valid_ECN (Buffer : Bytes) return Boolean is
      (Valid_ECN_0000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function ECN (Buffer : Bytes) return ECN_Type is
      ((if Valid_ECN_0000 (Buffer) then ECN_0000 (Buffer) else Unreachable_ECN_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_ECN (Buffer));

   function Valid_Total_Length_00000 (Buffer : Bytes) return Boolean is
      ((Valid_ECN_0000 (Buffer) and then ((Buffer'Length >= 4 and then Buffer'First <= (Natural'Last / 2)) and then Convert_To_Total_Length_Type_Base (Buffer ((Buffer'First + 2) .. (Buffer'First + 3))) >= 20)))
     with
       Pre => Is_Contained (Buffer);

   function Total_Length_00000 (Buffer : Bytes) return Total_Length_Type is
      (Convert_To_Total_Length_Type_Base (Buffer ((Buffer'First + 2) .. (Buffer'First + 3))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Total_Length_00000 (Buffer));

   function Valid_Total_Length (Buffer : Bytes) return Boolean is
      (Valid_Total_Length_00000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Total_Length (Buffer : Bytes) return Total_Length_Type is
      ((if Valid_Total_Length_00000 (Buffer) then Total_Length_00000 (Buffer) else Unreachable_Total_Length_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Total_Length (Buffer));

   function Valid_Identification_000000 (Buffer : Bytes) return Boolean is
      ((Valid_Total_Length_00000 (Buffer) and then (Buffer'Length >= 6 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Identification_000000 (Buffer : Bytes) return Identification_Type is
      (Convert_To_Identification_Type (Buffer ((Buffer'First + 4) .. (Buffer'First + 5))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Identification_000000 (Buffer));

   function Valid_Identification (Buffer : Bytes) return Boolean is
      (Valid_Identification_000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Identification (Buffer : Bytes) return Identification_Type is
      ((if Valid_Identification_000000 (Buffer) then Identification_000000 (Buffer) else Unreachable_Identification_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Identification (Buffer));

   function Valid_Flag_R_0000000 (Buffer : Bytes) return Boolean is
      ((Valid_Identification_000000 (Buffer) and then (Buffer'Length >= 7 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Flag_R_0000000 (Buffer : Bytes) return Flag_Type is
      (Convert_To_Flag_Type (Buffer ((Buffer'First + 6) .. (Buffer'First + 6)), 7))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Flag_R_0000000 (Buffer));

   function Valid_Flag_R (Buffer : Bytes) return Boolean is
      ((Valid_Flag_R_0000000 (Buffer) and then Flag_R_0000000 (Buffer) = 0))
     with
       Pre => Is_Contained (Buffer);

   function Flag_R (Buffer : Bytes) return Flag_Type is
      ((if Valid_Flag_R_0000000 (Buffer) then Flag_R_0000000 (Buffer) else Unreachable_Flag_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Flag_R (Buffer));

   function Valid_Flag_DF_00000000 (Buffer : Bytes) return Boolean is
      ((Valid_Flag_R_0000000 (Buffer) and then ((Buffer'Length >= 7 and then Buffer'First <= (Natural'Last / 2)) and then Flag_R_0000000 (Buffer) = 0)))
     with
       Pre => Is_Contained (Buffer);

   function Flag_DF_00000000 (Buffer : Bytes) return Flag_Type is
      (Convert_To_Flag_Type (Buffer ((Buffer'First + 6) .. (Buffer'First + 6)), 6))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Flag_DF_00000000 (Buffer));

   function Valid_Flag_DF (Buffer : Bytes) return Boolean is
      (Valid_Flag_DF_00000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Flag_DF (Buffer : Bytes) return Flag_Type is
      ((if Valid_Flag_DF_00000000 (Buffer) then Flag_DF_00000000 (Buffer) else Unreachable_Flag_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Flag_DF (Buffer));

   function Valid_Flag_MF_000000000 (Buffer : Bytes) return Boolean is
      ((Valid_Flag_DF_00000000 (Buffer) and then (Buffer'Length >= 7 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Flag_MF_000000000 (Buffer : Bytes) return Flag_Type is
      (Convert_To_Flag_Type (Buffer ((Buffer'First + 6) .. (Buffer'First + 6)), 5))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Flag_MF_000000000 (Buffer));

   function Valid_Flag_MF (Buffer : Bytes) return Boolean is
      (Valid_Flag_MF_000000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Flag_MF (Buffer : Bytes) return Flag_Type is
      ((if Valid_Flag_MF_000000000 (Buffer) then Flag_MF_000000000 (Buffer) else Unreachable_Flag_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Flag_MF (Buffer));

   function Valid_Fragment_Offset_0000000000 (Buffer : Bytes) return Boolean is
      ((Valid_Flag_MF_000000000 (Buffer) and then (Buffer'Length >= 8 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Fragment_Offset_0000000000 (Buffer : Bytes) return Fragment_Offset_Type is
      (Convert_To_Fragment_Offset_Type (Buffer ((Buffer'First + 6) .. (Buffer'First + 7))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Fragment_Offset_0000000000 (Buffer));

   function Valid_Fragment_Offset (Buffer : Bytes) return Boolean is
      (Valid_Fragment_Offset_0000000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Fragment_Offset (Buffer : Bytes) return Fragment_Offset_Type is
      ((if Valid_Fragment_Offset_0000000000 (Buffer) then Fragment_Offset_0000000000 (Buffer) else Unreachable_Fragment_Offset_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Fragment_Offset (Buffer));

   function Valid_TTL_00000000000 (Buffer : Bytes) return Boolean is
      ((Valid_Fragment_Offset_0000000000 (Buffer) and then (Buffer'Length >= 9 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function TTL_00000000000 (Buffer : Bytes) return TTL_Type is
      (Convert_To_TTL_Type (Buffer ((Buffer'First + 8) .. (Buffer'First + 8))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_TTL_00000000000 (Buffer));

   function Valid_TTL (Buffer : Bytes) return Boolean is
      (Valid_TTL_00000000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function TTL (Buffer : Bytes) return TTL_Type is
      ((if Valid_TTL_00000000000 (Buffer) then TTL_00000000000 (Buffer) else Unreachable_TTL_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_TTL (Buffer));

   function Valid_Protocol_000000000000 (Buffer : Bytes) return Boolean is
      ((Valid_TTL_00000000000 (Buffer) and then (Buffer'Length >= 10 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Protocol_000000000000 (Buffer : Bytes) return Protocol_Type is
      (Convert_To_Protocol_Type (Buffer ((Buffer'First + 9) .. (Buffer'First + 9))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Protocol_000000000000 (Buffer));

   function Valid_Protocol (Buffer : Bytes) return Boolean is
      (Valid_Protocol_000000000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Protocol (Buffer : Bytes) return Protocol_Type is
      ((if Valid_Protocol_000000000000 (Buffer) then Protocol_000000000000 (Buffer) else Unreachable_Protocol_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Protocol (Buffer));

   function Valid_Header_Checksum_0000000000000 (Buffer : Bytes) return Boolean is
      ((Valid_Protocol_000000000000 (Buffer) and then (Buffer'Length >= 12 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Header_Checksum_0000000000000 (Buffer : Bytes) return Header_Checksum_Type is
      (Convert_To_Header_Checksum_Type (Buffer ((Buffer'First + 10) .. (Buffer'First + 11))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Header_Checksum_0000000000000 (Buffer));

   function Valid_Header_Checksum (Buffer : Bytes) return Boolean is
      (Valid_Header_Checksum_0000000000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Header_Checksum (Buffer : Bytes) return Header_Checksum_Type is
      ((if Valid_Header_Checksum_0000000000000 (Buffer) then Header_Checksum_0000000000000 (Buffer) else Unreachable_Header_Checksum_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Header_Checksum (Buffer));

   function Valid_Source_00000000000000 (Buffer : Bytes) return Boolean is
      ((Valid_Header_Checksum_0000000000000 (Buffer) and then (Buffer'Length >= 16 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Source_00000000000000 (Buffer : Bytes) return Address_Type is
      (Convert_To_Address_Type (Buffer ((Buffer'First + 12) .. (Buffer'First + 15))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Source_00000000000000 (Buffer));

   function Valid_Source (Buffer : Bytes) return Boolean is
      (Valid_Source_00000000000000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Source (Buffer : Bytes) return Address_Type is
      ((if Valid_Source_00000000000000 (Buffer) then Source_00000000000000 (Buffer) else Unreachable_Address_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Source (Buffer));

   function Valid_Destination_000000000000000 (Buffer : Bytes) return Boolean is
      ((Valid_Source_00000000000000 (Buffer) and then (Buffer'Length >= 20 and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Destination_000000000000000 (Buffer : Bytes) return Address_Type is
      (Convert_To_Address_Type (Buffer ((Buffer'First + 16) .. (Buffer'First + 19))))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Destination_000000000000000 (Buffer));

   function Valid_Destination (Buffer : Bytes) return Boolean is
      ((Valid_Destination_000000000000000 (Buffer) and then (IHL_00 (Buffer) > 5 or IHL_00 (Buffer) = 5)))
     with
       Pre => Is_Contained (Buffer);

   function Destination (Buffer : Bytes) return Address_Type is
      ((if Valid_Destination_000000000000000 (Buffer) then Destination_000000000000000 (Buffer) else Unreachable_Address_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Destination (Buffer));

   function Valid_Options_0000000000000001 (Buffer : Bytes) return Boolean is
      ((Valid_Destination_000000000000000 (Buffer) and then ((Buffer'Length >= (Natural (IHL_00 (Buffer)) * 4) and then Buffer'First <= (Natural'Last / 2)) and then IHL_00 (Buffer) > 5)))
     with
       Pre => Is_Contained (Buffer);

   function Options_0000000000000001_First (Buffer : Bytes) return Natural is
      ((Buffer'First + 20))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Options_0000000000000001 (Buffer));

   function Options_0000000000000001_Last (Buffer : Bytes) return Natural is
      ((Buffer'First + (Natural (IHL_00 (Buffer)) * 4) + (-1)))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Options_0000000000000001 (Buffer));

   function Valid_Options (Buffer : Bytes) return Boolean is
      (Valid_Options_0000000000000001 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Options_First (Buffer : Bytes) return Natural is
      ((if Valid_Options_0000000000000001 (Buffer) then Options_0000000000000001_First (Buffer) else Unreachable_Natural))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Options (Buffer));

   function Options_Last (Buffer : Bytes) return Natural is
      ((if Valid_Options_0000000000000001 (Buffer) then Options_0000000000000001_Last (Buffer) else Unreachable_Natural))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Options (Buffer));

   procedure Options (Buffer : Bytes; First : out Natural; Last : out Natural)
     with
       Pre => (Is_Contained (Buffer) and then Valid_Options (Buffer)),
       Post => (First = Options_First (Buffer) and then Last = Options_Last (Buffer));

   function Valid_Payload_0000000000000000 (Buffer : Bytes) return Boolean is
      ((Valid_Destination_000000000000000 (Buffer) and then ((Buffer'Length >= Natural (Total_Length_00000 (Buffer)) and then Buffer'First <= (Natural'Last / 2)) and then IHL_00 (Buffer) = 5)))
     with
       Pre => Is_Contained (Buffer);

   function Payload_0000000000000000_First (Buffer : Bytes) return Natural is
      ((Buffer'First + 20))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Payload_0000000000000000 (Buffer));

   function Payload_0000000000000000_Last (Buffer : Bytes) return Natural is
      ((Buffer'First + Natural (Total_Length_00000 (Buffer)) + (-1)))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Payload_0000000000000000 (Buffer));

   function Valid_Payload_00000000000000010 (Buffer : Bytes) return Boolean is
      ((Valid_Options_0000000000000001 (Buffer) and then (Buffer'Length >= Natural (Total_Length_00000 (Buffer)) and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Payload_00000000000000010_First (Buffer : Bytes) return Natural is
      ((Buffer'First + (Natural (IHL_00 (Buffer)) * 4)))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Payload_00000000000000010 (Buffer));

   function Payload_00000000000000010_Last (Buffer : Bytes) return Natural is
      ((Buffer'First + Natural (Total_Length_00000 (Buffer)) + (-1)))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Payload_00000000000000010 (Buffer));

   function Valid_Payload (Buffer : Bytes) return Boolean is
      ((Valid_Payload_00000000000000010 (Buffer) or Valid_Payload_0000000000000000 (Buffer)))
     with
       Pre => Is_Contained (Buffer);

   function Payload_First (Buffer : Bytes) return Natural is
      ((if Valid_Payload_0000000000000000 (Buffer) then Payload_0000000000000000_First (Buffer) elsif Valid_Payload_00000000000000010 (Buffer) then Payload_00000000000000010_First (Buffer) else Unreachable_Natural))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Payload (Buffer));

   function Payload_Last (Buffer : Bytes) return Natural is
      ((if Valid_Payload_0000000000000000 (Buffer) then Payload_0000000000000000_Last (Buffer) elsif Valid_Payload_00000000000000010 (Buffer) then Payload_00000000000000010_Last (Buffer) else Unreachable_Natural))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Payload (Buffer));

   procedure Payload (Buffer : Bytes; First : out Natural; Last : out Natural)
     with
       Pre => (Is_Contained (Buffer) and then Valid_Payload (Buffer)),
       Post => (First = Payload_First (Buffer) and then Last = Payload_Last (Buffer));

   function Is_Valid (Buffer : Bytes) return Boolean is
      (Valid_Payload (Buffer))
     with
       Pre => Is_Contained (Buffer);

end IPv4.Packet;