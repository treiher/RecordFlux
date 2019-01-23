package body TLV.Message is

   procedure Initialize (Buffer : Bytes) is
   begin
      pragma Assume (Is_Contained (Buffer));
   end Initialize;

   procedure Get_Value (Buffer : Bytes; First : out Natural; Last : out Natural) is
   begin
      First := Get_Value_First (Buffer);
      Last := Get_Value_Last (Buffer);
   end Get_Value;

end TLV.Message;
