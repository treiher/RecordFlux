with Types;
use type Types.Bytes, Types.Index_Type, Types.Length_Type, Types.Bit_Index_Type, Types.Bit_Length_Type;

package TLV with
  SPARK_Mode
is

   type Tag_Type_Base is mod (2**2);

   type Tag_Type is (Msg_Data, Msg_Error) with Size => 2;
   for Tag_Type use (Msg_Data => 1, Msg_Error => 3);

   pragma Warnings (Off, "precondition is statically false");

   function Unreachable_Tag_Type return Tag_Type is
     (Tag_Type'First)
    with
     Pre => False;

   pragma Warnings (On, "precondition is statically false");

   function Convert_To_Tag_Type_Base is new Types.Convert_To_Mod (Tag_Type_Base);

   function Valid_Tag_Type (Buffer : Types.Bytes; Offset : Types.Offset_Type) return Boolean is
     (case Convert_To_Tag_Type_Base (Buffer, Offset) is when 1 | 3 => True, when others => False)
    with
     Pre => Buffer'Length = Types.Byte_Index ((Tag_Type_Base'Size + Types.Bit_Length_Type (Offset)));

   function Convert_To_Tag_Type (Buffer : Types.Bytes; Offset : Types.Offset_Type) return Tag_Type is
     (case Convert_To_Tag_Type_Base (Buffer, Offset) is when 1 => Msg_Data, when 3 => Msg_Error, when others => Unreachable_Tag_Type)
    with
     Pre => (Buffer'Length = Types.Byte_Index ((Tag_Type_Base'Size + Types.Bit_Length_Type (Offset))) and then Valid_Tag_Type (Buffer, Offset));

   function Convert_To_Tag_Type_Base (Enum : Tag_Type) return Tag_Type_Base is
     (case Enum is when Msg_Data => 1, when Msg_Error => 3);

   type Length_Type is mod (2**14);

   pragma Warnings (Off, "precondition is statically false");

   function Unreachable_Length_Type return Length_Type is
     (Length_Type'First)
    with
     Pre => False;

   pragma Warnings (On, "precondition is statically false");

   function Convert_To_Length_Type is new Types.Convert_To_Mod (Length_Type);

   function Valid_Length_Type (Buffer : Types.Bytes; Offset : Types.Offset_Type) return Boolean is
     (True)
    with
     Pre => Buffer'Length = Types.Byte_Index ((Length_Type'Size + Types.Bit_Length_Type (Offset)));

   pragma Warnings (Off, "precondition is statically false");

   function Unreachable_Types_Index_Type return Types.Index_Type is
     (Types.Index_Type'First)
    with
     Pre => False;

   pragma Warnings (On, "precondition is statically false");

   pragma Warnings (Off, "precondition is statically false");

   function Unreachable_Types_Length_Type return Types.Length_Type is
     (Types.Length_Type'First)
    with
     Pre => False;

   pragma Warnings (On, "precondition is statically false");

end TLV;