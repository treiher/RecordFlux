with SPARK.Assertions; use SPARK.Assertions;
with SPARK.File_IO; use SPARK.File_IO;

with TLV.Message;

package body TLV.Tests is

   function Name (T : Test) return AUnit.Message_String is
      pragma Unreferenced (T);
   begin
      return AUnit.Format ("TLV");
   end Name;

   procedure Test_TLV_Data (T : in out Aunit.Test_Cases.Test_Case'Class)
     with SPARK_Mode, Global => null
   is
      pragma Unreferenced (T);
      Buffer : Bytes := Bytes'(64, 4, 0, 0, 0, 0);
      Tag    : TLV.Tag_Type;
      Length : TLV.Length_Type;
      First  : Natural;
      Last   : Natural;
   begin
      TLV.Message.Initialize (Buffer);
      Assert (TLV.Message.Valid_Tag (Buffer), "Invalid Tag");
      if TLV.Message.Valid_Tag (Buffer) then
         Tag := TLV.Message.Tag (Buffer);
         Assert (Tag'Image, TLV.Tag_Type'Image (TLV.Msg_Data), "Unexpected Tag");
         Assert (TLV.Message.Valid_Length (Buffer), "Invalid Length");
         if TLV.Message.Valid_Length (Buffer) then
            Length := TLV.Message.Length (Buffer);
            Assert (Length'Image, TLV.Length_Type'Image (4), "Unexpected Length");
            Assert (TLV.Message.Valid_Value (Buffer), "Invalid Value");
            if TLV.Message.Valid_Value (Buffer) then
               TLV.Message.Value (Buffer, First, Last);
               Assert (First'Image, Natural'Image (3), "Unexpected Value'First");
               Assert (Last'Image, Natural'Image (6), "Unexpected Value'Last");
            end if;
         end if;
      end if;
      Assert (TLV.Message.Is_Valid (Buffer), "Invalid Message");
   end Test_TLV_Data;

   procedure Test_TLV_Data_Zero (T : in out Aunit.Test_Cases.Test_Case'Class)
     with SPARK_Mode, Global => null
   is
      pragma Unreferenced (T);
      Buffer : Bytes := Bytes'(64, 0);
      Tag    : TLV.Tag_Type;
      Length : TLV.Length_Type;
      First  : Natural;
      Last   : Natural;
   begin
      TLV.Message.Initialize (Buffer);
      Assert (TLV.Message.Valid_Tag (Buffer), "Invalid Tag");
      if TLV.Message.Valid_Tag (Buffer) then
         Tag := TLV.Message.Tag (Buffer);
         Assert (Tag'Image, TLV.Tag_Type'Image (TLV.Msg_Data), "Unexpected Tag");
         Assert (TLV.Message.Valid_Length (Buffer), "Invalid Length");
         if TLV.Message.Valid_Length (Buffer) then
            Length := TLV.Message.Length (Buffer);
            Assert (Length'Image, TLV.Length_Type'Image (0), "Unexpected Length");
            Assert (TLV.Message.Valid_Value (Buffer), "Invalid Value");
            if TLV.Message.Valid_Value (Buffer) then
               TLV.Message.Value (Buffer, First, Last);
               Assert (First'Image, Natural'Image (3), "Unexpected Value'First");
               Assert (Last'Image, Natural'Image (2), "Unexpected Value'Last");
            end if;
         end if;
      end if;
      Assert (TLV.Message.Is_Valid (Buffer), "Invalid Message");
   end Test_TLV_Data_Zero;

   procedure Test_TLV_Error (T : in out Aunit.Test_Cases.Test_Case'Class)
     with SPARK_Mode, Global => null
   is
      pragma Unreferenced (T);
      Buffer : Bytes := (1 => 192);
      Tag    : TLV.Tag_Type;
   begin
      TLV.Message.Initialize (Buffer);
      Assert (TLV.Message.Valid_Tag (Buffer), "Invalid Tag");
      if TLV.Message.Valid_Tag (Buffer) then
         Tag := TLV.Message.Tag (Buffer);
         Assert (Tag'Image, TLV.Tag_Type'Image (TLV.Msg_Error), "Unexpected Tag");
      end if;
      Assert (TLV.Message.Is_Valid (Buffer), "Invalid Message");
   end Test_TLV_Error;

   procedure Test_Invalid_TLV_Invalid_Tag (T : in out Aunit.Test_Cases.Test_Case'Class)
     with SPARK_Mode, Global => null
   is
      pragma Unreferenced (T);
      Buffer : Bytes := Bytes'(0, 0);
   begin
      TLV.Message.Initialize (Buffer);
      Assert (Not TLV.Message.Is_Valid (Buffer), "False positive");
   end Test_Invalid_TLV_Invalid_Tag;

   procedure Register_Tests (T : in out Test) is
      use AUnit.Test_Cases.Registration;
   begin
      Register_Routine (T, Test_TLV_Data'Access, "TLV Data Message");
      Register_Routine (T, Test_TLV_Data_Zero'Access, "TLV Data Message (length zero)");
      Register_Routine (T, Test_TLV_Error'Access, "TLV Error Message");
      Register_Routine (T, Test_Invalid_TLV_Invalid_Tag'Access, "Invalid TLV (invalid tag)");
   end Register_Tests;

end TLV.Tests;