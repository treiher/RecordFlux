package body Ethernet.IEEE_802_3 is

   function Valid_Destination (Buffer : Bytes) return Boolean is
   begin
      return Buffer'Length >= 6;
   end Valid_Destination;

   function Destination (Buffer : Bytes) return U48 is
   begin
      return Convert_To_U48 (Buffer (Buffer'First + 0 .. Buffer'First + 5));
   end Destination;

   function Valid_Source (Buffer : Bytes) return Boolean is
   begin
      return Buffer'Length >= 12;
   end Valid_Source;

   function Source (Buffer : Bytes) return U48 is
   begin
      return Convert_To_U48 (Buffer (Buffer'First + 6 .. Buffer'First + 11));
   end Source;

   function Valid_EtherType (Buffer : Bytes) return Boolean is
   begin
      return (Buffer'Length >= 14 and then Convert_To_U16 (Buffer (Buffer'First + 12 .. Buffer'First + 13)) <= 1500);
   end Valid_EtherType;

   function EtherType (Buffer : Bytes) return U16 is
   begin
      return Convert_To_U16 (Buffer (Buffer'First + 12 .. Buffer'First + 13));
   end EtherType;

   function Valid_Payload (Buffer : Bytes) return Boolean is
   begin
      return (Buffer'Length >= 14 and then ((Buffer'Length >= 60 and then Buffer'Length <= 1514) and then (EtherType (Buffer) <= 1500 and then Buffer'Length = EtherType (Buffer) + 14)));
   end Valid_Payload;

   function Payload (Buffer : Bytes) return Payload_Type is
   begin
      return Payload_Type (Buffer (Buffer'First + 14 .. Buffer'Last));
   end Payload;

   function Is_Valid (Buffer : Bytes) return Boolean is
   begin
      return (Buffer'Length >= 14 and then ((Buffer'Length >= 60 and then Buffer'Length <= 1514) and then (EtherType (Buffer) <= 1500 and then Buffer'Length = EtherType (Buffer) + 14)));
   end Is_Valid;

end Ethernet.IEEE_802_3;
