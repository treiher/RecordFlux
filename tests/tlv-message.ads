package TLV.Message
  with SPARK_Mode
is

   function Is_Contained (Buffer : Bytes) return Boolean
     with
       Ghost,
       Import;

   procedure Initialize (Buffer : Bytes)
     with
       Post => Is_Contained (Buffer);

   function Valid_Tag_0 (Buffer : Bytes) return Boolean is
      (((Buffer'Length >= 1 and then Buffer'First <= (Natural'Last / 2)) and then Valid_Tag_Type (Buffer (Buffer'First .. Buffer'First), 6)))
     with
       Pre => Is_Contained (Buffer);

   function Get_Tag_0 (Buffer : Bytes) return Tag_Type is
      (Convert_To_Tag_Type (Buffer (Buffer'First .. Buffer'First), 6))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Tag_0 (Buffer));

   function Valid_Tag (Buffer : Bytes) return Boolean is
      ((Valid_Tag_0 (Buffer) and then (Get_Tag_0 (Buffer) = Msg_Error or Get_Tag_0 (Buffer) = Msg_Data)))
     with
       Pre => Is_Contained (Buffer);

   function Get_Tag (Buffer : Bytes) return Tag_Type is
      ((if Valid_Tag_0 (Buffer) then Get_Tag_0 (Buffer) else Unreachable_Tag_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Tag (Buffer));

   function Valid_Length_00 (Buffer : Bytes) return Boolean is
      ((Valid_Tag_0 (Buffer) and then ((Buffer'Length >= 2 and then Buffer'First <= (Natural'Last / 2)) and then Get_Tag_0 (Buffer) = Msg_Data)))
     with
       Pre => Is_Contained (Buffer);

   function Get_Length_00 (Buffer : Bytes) return Length_Type is
      (Convert_To_Length_Type (Buffer (Buffer'First .. (Buffer'First + 1)), 0))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Length_00 (Buffer));

   function Valid_Length (Buffer : Bytes) return Boolean is
      (Valid_Length_00 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Get_Length (Buffer : Bytes) return Length_Type is
      ((if Valid_Length_00 (Buffer) then Get_Length_00 (Buffer) else Unreachable_Length_Type))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Length (Buffer));

   function Valid_Value_000 (Buffer : Bytes) return Boolean is
      ((Valid_Length_00 (Buffer) and then (Buffer'Length >= (Natural (Get_Length_00 (Buffer)) + 2) and then Buffer'First <= (Natural'Last / 2))))
     with
       Pre => Is_Contained (Buffer);

   function Get_Value_000_First (Buffer : Bytes) return Natural is
      ((Buffer'First + 2))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Value_000 (Buffer));

   function Get_Value_000_Last (Buffer : Bytes) return Natural is
      ((Natural (Get_Length_00 (Buffer)) + Buffer'First + 1))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Value_000 (Buffer));

   function Valid_Value (Buffer : Bytes) return Boolean is
      (Valid_Value_000 (Buffer))
     with
       Pre => Is_Contained (Buffer);

   function Get_Value_First (Buffer : Bytes) return Natural is
      ((if Valid_Value_000 (Buffer) then Get_Value_000_First (Buffer) else Unreachable_Natural))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Value (Buffer));

   function Get_Value_Last (Buffer : Bytes) return Natural is
      ((if Valid_Value_000 (Buffer) then Get_Value_000_Last (Buffer) else Unreachable_Natural))
     with
       Pre => (Is_Contained (Buffer) and then Valid_Value (Buffer));

   procedure Get_Value (Buffer : Bytes; First : out Natural; Last : out Natural)
     with
       Pre => (Is_Contained (Buffer) and then Valid_Value (Buffer)),
       Post => (First = Get_Value_First (Buffer) and then Last = Get_Value_Last (Buffer));

   function Is_Valid (Buffer : Bytes) return Boolean is
      ((Valid_Value_000 (Buffer) or (Valid_Tag_0 (Buffer) and then Get_Tag_0 (Buffer) = Msg_Error)))
     with
       Pre => Is_Contained (Buffer);

   function Message_Length (Buffer : Bytes) return Natural is
      ((if Valid_Value_000 (Buffer) then (Natural (Get_Length_00 (Buffer)) + 2) elsif (Valid_Tag_0 (Buffer) and then Get_Tag_0 (Buffer) = Msg_Error) then 0 else Unreachable_Natural))
     with
       Pre => (Is_Contained (Buffer) and then Is_Valid (Buffer));

end TLV.Message;
