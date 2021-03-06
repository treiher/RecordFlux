with SPARK; use SPARK;
with SPARK.Assertions; use SPARK.Assertions;

with RFLX.RFLX_Builtin_Types; use type RFLX.RFLX_Builtin_Types.Length, RFLX.RFLX_Builtin_Types.Bit_Length;
with RFLX.RFLX_Types;

with RFLX.Derivation.Message;
with RFLX.Arrays.Modular_Vector;
with RFLX.Arrays.Range_Vector;
with RFLX.Arrays.Enumeration_Vector;
with RFLX.Arrays.AV_Enumeration_Vector;

package body RFLX.Derivation.Tests is

   overriding
   function Name (T : Test) return AUnit.Message_String is
      pragma Unreferenced (T);
   begin
      return AUnit.Format ("Derivation");
   end Name;

   procedure Test_Parsing_Derivation_Modular_Sequential (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.Modular_Vector.Context;
      Element          : Arrays.Modular_Integer;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_Modular_Vector) then
            Derivation.Message.Switch_To_Modular_Vector (Context, Sequence_Context);

            if Arrays.Modular_Vector.Valid_Element (Sequence_Context) then
               Element := Arrays.Modular_Vector.Get_Element (Sequence_Context);
               Assert (Element'Image, Arrays.Modular_Integer'Image (1), "Invalid value of element 1");

               Arrays.Modular_Vector.Next (Sequence_Context);
               if Arrays.Modular_Vector.Valid_Element (Sequence_Context) then
                  Element := Arrays.Modular_Vector.Get_Element (Sequence_Context);
                  Assert (Element'Image, Arrays.Modular_Integer'Image (2), "Invalid value of element 2");

                  Arrays.Modular_Vector.Next (Sequence_Context);
                  Assert (not Arrays.Modular_Vector.Valid_Element (Sequence_Context),
                          "Invalid acceptance of further element");

                  Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
                          "Valid Modular_Vector before context update");
                  Derivation.Message.Update_Modular_Vector (Context, Sequence_Context);
                  Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
                          "Invalid Modular_Vector after context update");
               else
                  Assert (False, "Invalid element 2");
               end if;
            else
               Assert (False, "Invalid element 1");
            end if;

         else
            Assert (False, "Invalid Modular_Vector");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (Derivation.Message.Has_Buffer (Context) and then not Derivation.Message.Valid_Message (Context),
              "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      else
         Arrays.Modular_Vector.Take_Buffer (Sequence_Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (40)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Derivation_Modular_Sequential;

   procedure Test_Parsing_Derivation_Modular_Loop (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.Modular_Vector.Context;
      Element          : Arrays.Modular_Integer;
      I                : Natural := 1;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_Modular_Vector) then
            Derivation.Message.Switch_To_Modular_Vector (Context, Sequence_Context);

            while I <= 10 and then Arrays.Modular_Vector.Valid_Element (Sequence_Context) loop
               pragma Loop_Invariant (Arrays.Modular_Vector.Has_Buffer (Sequence_Context));
               pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
               pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
               pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
               pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

               Element := Arrays.Modular_Vector.Get_Element (Sequence_Context);
               Assert (Element'Image, Natural'Image (I), "Invalid value of element " & I'Image);

               Arrays.Modular_Vector.Next (Sequence_Context);
               I := I + 1;
            end loop;

            Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

            Assert (Arrays.Modular_Vector.Valid (Sequence_Context), "Invalid Modular_Vector after parsing");

            Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
                    "Valid Modular_Vector before context update");
            Derivation.Message.Update_Modular_Vector (Context, Sequence_Context);
            Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
                    "Invalid Modular_Vector after context update");
         else
            Assert (False, "Invalid Modular_Vector or Buffer");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (40)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Derivation_Modular_Loop;

   procedure Test_Parsing_Derivation_Range_Sequential (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 0, 0, 0, 1, 2, 0, 0, 0, 0);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.Range_Vector.Context;
      Element          : Arrays.Range_Integer;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_Range_Vector) then
            Derivation.Message.Switch_To_Range_Vector (Context, Sequence_Context);

            if Arrays.Range_Vector.Valid_Element (Sequence_Context) then
               Element := Arrays.Range_Vector.Get_Element (Sequence_Context);
               Assert (Element'Image, Arrays.Range_Integer'Image (1), "Invalid value of element 1");

               Arrays.Range_Vector.Next (Sequence_Context);
               if Arrays.Range_Vector.Valid_Element (Sequence_Context) then
                  Element := Arrays.Range_Vector.Get_Element (Sequence_Context);
                  Assert (Element'Image, Arrays.Range_Integer'Image (2), "Invalid value of element 2");

                  Arrays.Range_Vector.Next (Sequence_Context);

                  Assert (not Arrays.Range_Vector.Valid_Element (Sequence_Context),
                          "Invalid acceptance of further element");

                  Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
                          "Valid Range_Vector before context update");
                  Derivation.Message.Update_Range_Vector (Context, Sequence_Context);
                  Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
                          "Invalid Range_Vector after context update");
               else
                  Assert (False, "Invalid element 2");
               end if;
            else
               Assert (False, "Invalid element 1");
            end if;

         else
            Assert (False, "Invalid Range_Vector or Buffer");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (Derivation.Message.Has_Buffer (Context) and then not Derivation.Message.Valid_Message (Context),
              "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      else
         Arrays.Range_Vector.Take_Buffer (Sequence_Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (56)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Derivation_Range_Sequential;

   procedure Test_Parsing_Derivation_Range_Loop (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 0, 0, 0, 1, 2, 0, 0, 0, 0);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.Range_Vector.Context;
      Element          : Arrays.Range_Integer;
      I                : Natural := 1;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_Range_Vector) then
            Derivation.Message.Switch_To_Range_Vector (Context, Sequence_Context);

            while I <= 10 and then Arrays.Range_Vector.Valid_Element (Sequence_Context) loop
               pragma Loop_Invariant (Arrays.Range_Vector.Has_Buffer (Sequence_Context));
               pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
               pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
               pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
               pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

               Element := Arrays.Range_Vector.Get_Element (Sequence_Context);
               Assert (Element'Image, Natural'Image (I), "Invalid value of element " & I'Image);

               Arrays.Range_Vector.Next (Sequence_Context);
               I := I + 1;
            end loop;

            Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

            Assert (Arrays.Range_Vector.Valid (Sequence_Context), "Invalid Range_Vector after parsing");

            Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
                    "Valid Range_Vector before context update");
            Derivation.Message.Update_Range_Vector (Context, Sequence_Context);
            Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
                    "Invalid Range_Vector after context update");
         else
            Assert (False, "Invalid Range_Vector or Buffer");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (56)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Derivation_Range_Loop;

   procedure Test_Parsing_Derivation_Enumeration_Sequential (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.Enumeration_Vector.Context;
      Element          : Arrays.Enumeration;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_Enumeration_Vector) then
            Derivation.Message.Switch_To_Enumeration_Vector (Context, Sequence_Context);

            if Arrays.Enumeration_Vector.Valid_Element (Sequence_Context) then
               Element := Arrays.Enumeration_Vector.Get_Element (Sequence_Context);
               Assert (Element'Image, Arrays.Enumeration'Image (Arrays.ONE), "Invalid value of element 1");

               Arrays.Enumeration_Vector.Next (Sequence_Context);
               if Arrays.Enumeration_Vector.Valid_Element (Sequence_Context) then
                  Element := Arrays.Enumeration_Vector.Get_Element (Sequence_Context);
                  Assert (Element'Image, Arrays.Enumeration'Image (Arrays.TWO), "Invalid value of element 2");

                  Arrays.Enumeration_Vector.Next (Sequence_Context);

                  Assert (not Arrays.Enumeration_Vector.Valid_Element (Sequence_Context),
                          "Invalid acceptance of further element");

                  Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
                          "Valid Enumeration_Vector before context update");
                  Derivation.Message.Update_Enumeration_Vector (Context, Sequence_Context);
                  Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
                          "Invalid Enumeration_Vector after context update");
               else
                  Assert (False, "Invalid element 2");
               end if;
            else
               Assert (False, "Invalid element 1");
            end if;

         else
            Assert (False, "Invalid Enumeration_Vector or Buffer");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (Derivation.Message.Has_Buffer (Context) and then not Derivation.Message.Valid_Message (Context),
              "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      else
         Arrays.Enumeration_Vector.Take_Buffer (Sequence_Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (72)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Derivation_Enumeration_Sequential;

   procedure Test_Parsing_Derivation_Enumeration_Loop (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.Enumeration_Vector.Context;
      Element          : Arrays.Enumeration;
      I                : Natural := 1;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_Enumeration_Vector) then
            Derivation.Message.Switch_To_Enumeration_Vector (Context, Sequence_Context);

            while I <= 10 and then Arrays.Enumeration_Vector.Valid_Element (Sequence_Context) loop
               pragma Loop_Invariant (Arrays.Enumeration_Vector.Has_Buffer (Sequence_Context));
               pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
               pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
               pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
               pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

               Element := Arrays.Enumeration_Vector.Get_Element (Sequence_Context);
               Assert (Arrays.Enumeration'Pos (Element)'Image, Natural'Image (I),
                       "Invalid value of element " & I'Image);

               Arrays.Enumeration_Vector.Next (Sequence_Context);
               I := I + 1;
            end loop;

            Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

            Assert (Arrays.Enumeration_Vector.Valid (Sequence_Context), "Invalid Enumeration_Vector after parsing");

            Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
                    "Valid Enumeration_Vector before context update");
            Derivation.Message.Update_Enumeration_Vector (Context, Sequence_Context);
            Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
                    "Invalid Enumeration_Vector after context update");
         else
            Assert (False, "Invalid Enumeration_Vector or Buffer");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (72)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Derivation_Enumeration_Loop;

   procedure Test_Parsing_Arrays_AV_Enumeration_Sequential (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.AV_Enumeration_Vector.Context;
      Element          : Arrays.AV_Enumeration;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_AV_Enumeration_Vector) then
            Derivation.Message.Switch_To_AV_Enumeration_Vector (Context, Sequence_Context);

            if Arrays.AV_Enumeration_Vector.Valid_Element (Sequence_Context) then
               Element := Arrays.AV_Enumeration_Vector.Get_Element (Sequence_Context);
               if Element.Known then
                  Assert (Element.Enum'Image, Arrays.AV_ONE'Image, "Invalid value of element 1");
               else
                  Assert (False, "Unknown value of element 1");
               end if;

               Arrays.AV_Enumeration_Vector.Next (Sequence_Context);
               if Arrays.AV_Enumeration_Vector.Valid_Element (Sequence_Context) then
                  Element := Arrays.AV_Enumeration_Vector.Get_Element (Sequence_Context);
                  if Element.Known then
                     Assert (Element.Enum'Image, Arrays.AV_TWO'Image, "Invalid value of element 2");
                  else
                     Assert (False, "Unknown value of element 2");
                  end if;

                  Arrays.AV_Enumeration_Vector.Next (Sequence_Context);

                  Assert (not Arrays.AV_Enumeration_Vector.Valid_Element (Sequence_Context),
                          "Invalid acceptance of further element");

                  Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
                          "Valid AV_Enumeration_Vector before context update");
                  Derivation.Message.Update_AV_Enumeration_Vector (Context, Sequence_Context);
                  Assert (Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
                          "Invalid AV_Enumeration_Vector after context update");
               else
                  Assert (False, "Invalid element 2");
               end if;
            else
               Assert (False, "Invalid element 1");
            end if;

         else
            Assert (False, "Invalid AV_Enumeration_Vector or Buffer");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (Derivation.Message.Has_Buffer (Context) and then not Derivation.Message.Valid_Message (Context),
              "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      else
         Arrays.AV_Enumeration_Vector.Take_Buffer (Sequence_Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Arrays_AV_Enumeration_Sequential;

   procedure Test_Parsing_Arrays_AV_Enumeration_Loop (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer           : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2);
      Context          : Derivation.Message.Context;
      Length           : Arrays.Length;
      Sequence_Context : Arrays.AV_Enumeration_Vector.Context;
      Element          : Arrays.AV_Enumeration;
      I                : Natural := 1;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         if Derivation.Message.Present (Context, Derivation.Message.F_AV_Enumeration_Vector) then
            Derivation.Message.Switch_To_AV_Enumeration_Vector (Context, Sequence_Context);

            while I <= 10 and then Arrays.AV_Enumeration_Vector.Valid_Element (Sequence_Context) loop
               pragma Loop_Invariant (Arrays.AV_Enumeration_Vector.Has_Buffer (Sequence_Context));
               pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
               pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
               pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
               pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

               Element := Arrays.AV_Enumeration_Vector.Get_Element (Sequence_Context);
               if Element.Known then
                  Assert (Arrays.AV_Enumeration_Enum'Pos (Element.Enum)'Image, Natural'Image (I),
                          "Invalid value of element " & I'Image);
               else
                  Assert (False, "Unknown value of element " & I'Image);
               end if;

               Arrays.AV_Enumeration_Vector.Next (Sequence_Context);
               I := I + 1;
            end loop;

            Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

            Assert (Arrays.AV_Enumeration_Vector.Valid (Sequence_Context),
                    "Invalid AV_Enumeration_Vector after parsing");

            Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
                    "Valid AV_Enumeration_Vector before context update");
            Derivation.Message.Update_AV_Enumeration_Vector (Context, Sequence_Context);
            Assert (Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
                    "Invalid AV_Enumeration_Vector after context update");
         else
            Assert (False, "Invalid AV_Enumeration_Vector or Buffer");
         end if;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

      if Derivation.Message.Has_Buffer (Context) then
         Derivation.Message.Take_Buffer (Context, Buffer);
      end if;
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
      Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Sequence_Context.Last");
   end Test_Parsing_Arrays_AV_Enumeration_Loop;

   procedure Test_Parsing_Derivation_Message (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Buffer  : RFLX_Builtin_Types.Bytes_Ptr := new RFLX_Builtin_Types.Bytes'(4, 0, 1, 0, 2, 1, 2, 1, 2, 1, 2);
      Context : Derivation.Message.Context;
      Length  : Arrays.Length;
   begin
      Derivation.Message.Initialize (Context, Buffer);

      Derivation.Message.Verify_Message (Context);
      if Derivation.Message.Valid (Context, Derivation.Message.F_Length) then
         Length := Derivation.Message.Get_Length (Context);
         Assert (Length'Image, Arrays.Length'Image (4), "Unexpected Length");

         Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

         declare
            Sequence_Context : Arrays.Modular_Vector.Context;
            Element          : Arrays.Modular_Integer;
            I                : Natural := 1;
         begin
            if Derivation.Message.Present (Context, Derivation.Message.F_Modular_Vector) then
               Derivation.Message.Switch_To_Modular_Vector (Context, Sequence_Context);

               while I <= 10 and then Arrays.Modular_Vector.Valid_Element (Sequence_Context) loop
                  pragma Loop_Invariant (Arrays.Modular_Vector.Has_Buffer (Sequence_Context));
                  pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
                  pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
                  pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
                  pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

                  Element := Arrays.Modular_Vector.Get_Element (Sequence_Context);
                  Assert (Element'Image, Natural'Image (I), "Invalid value of element " & I'Image);

                  Arrays.Modular_Vector.Next (Sequence_Context);
                  I := I + 1;
               end loop;

               Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

               Assert (Arrays.Modular_Vector.Valid (Sequence_Context), "Invalid Modular_Vector after parsing");

               Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
                       "Valid Modular_Vector before context update");
               Derivation.Message.Update_Modular_Vector (Context, Sequence_Context);
               Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
                       "Invalid Modular_Vector after context update");

               Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (40)'Image,
                       "Invalid Sequence_Context.Last");
            else
               Assert (False, "Invalid Modular_Vector or Buffer");
            end if;
         end;

         Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

         declare
            Sequence_Context : Arrays.Range_Vector.Context;
            Element          : Arrays.Range_Integer;
            I                : Natural := 1;
         begin
            if Derivation.Message.Present (Context, Derivation.Message.F_Range_Vector) then
               Derivation.Message.Switch_To_Range_Vector (Context, Sequence_Context);

               while I <= 10 and then Arrays.Range_Vector.Valid_Element (Sequence_Context) loop
                  pragma Loop_Invariant (Arrays.Range_Vector.Has_Buffer (Sequence_Context));
                  pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
                  pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
                  pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
                  pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

                  Element := Arrays.Range_Vector.Get_Element (Sequence_Context);
                  Assert (Element'Image, Natural'Image (I), "Invalid value of element " & I'Image);

                  Arrays.Range_Vector.Next (Sequence_Context);
                  I := I + 1;
               end loop;

               Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

               Assert (Arrays.Range_Vector.Valid (Sequence_Context), "Invalid Range_Vector after parsing");

               Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
                       "Valid Range_Vector before context update");
               Derivation.Message.Update_Range_Vector (Context, Sequence_Context);
               Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
                       "Invalid Range_Vector after context update");

               Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (56)'Image,
                       "Invalid Sequence_Context.Last");
            else
               Assert (False, "Invalid Range_Vector or Buffer");
            end if;
         end;

         Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

         declare
            Sequence_Context : Arrays.Enumeration_Vector.Context;
            Element          : Arrays.Enumeration;
            I                : Natural := 1;
         begin
            if Derivation.Message.Present (Context, Derivation.Message.F_Enumeration_Vector) then
               Derivation.Message.Switch_To_Enumeration_Vector (Context, Sequence_Context);

               while I <= 10 and then Arrays.Enumeration_Vector.Valid_Element (Sequence_Context) loop
                  pragma Loop_Invariant (Arrays.Enumeration_Vector.Has_Buffer (Sequence_Context));
                  pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
                  pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
                  pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
                  pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

                  Element := Arrays.Enumeration_Vector.Get_Element (Sequence_Context);
                  Assert (Arrays.Enumeration'Pos (Element)'Image, Natural'Image (I),
                          "Invalid value of element " & I'Image);

                  Arrays.Enumeration_Vector.Next (Sequence_Context);
                  I := I + 1;
               end loop;

               Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

               Assert (Arrays.Enumeration_Vector.Valid (Sequence_Context), "Invalid Enumeration_Vector after parsing");

               Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
                       "Valid Enumeration_Vector before context update");
               Derivation.Message.Update_Enumeration_Vector (Context, Sequence_Context);
               Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
                       "Invalid Enumeration_Vector after context update");

               Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (72)'Image,
                       "Invalid Sequence_Context.Last");
            else
               Assert (False, "Invalid Enumeration_Vector or Buffer");
            end if;
         end;

         Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete parsing");

         declare
            Sequence_Context : Arrays.AV_Enumeration_Vector.Context;
            Element          : Arrays.AV_Enumeration;
            I                : Natural := 1;
         begin
            if Derivation.Message.Present (Context, Derivation.Message.F_AV_Enumeration_Vector) then
               Derivation.Message.Switch_To_AV_Enumeration_Vector (Context, Sequence_Context);

               while I <= 10 and then Arrays.AV_Enumeration_Vector.Valid_Element (Sequence_Context) loop
                  pragma Loop_Invariant (Arrays.AV_Enumeration_Vector.Has_Buffer (Sequence_Context));
                  pragma Loop_Invariant (Context.Buffer_First = Sequence_Context.Buffer_First);
                  pragma Loop_Invariant (Context.Buffer_Last = Sequence_Context.Buffer_Last);
                  pragma Loop_Invariant (Sequence_Context.First = Sequence_Context.First'Loop_Entry);
                  pragma Loop_Invariant (Sequence_Context.Last = Sequence_Context.Last'Loop_Entry);

                  Element := Arrays.AV_Enumeration_Vector.Get_Element (Sequence_Context);
                  if Element.Known then
                     Assert (Arrays.AV_Enumeration_Enum'Pos (Element.Enum)'Image, Natural'Image (I),
                             "Invalid value of element " & I'Image);
                  else
                     Assert (False, "Unknown value of element " & I'Image);
                  end if;

                  Arrays.AV_Enumeration_Vector.Next (Sequence_Context);
                  I := I + 1;
               end loop;

               Assert (I'Image, Natural'Image (3), "Unexpected number of elements");

               Assert (Arrays.AV_Enumeration_Vector.Valid (Sequence_Context),
                       "Invalid AV_Enumeration_Vector after parsing");

               Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
                       "Valid AV_Enumeration_Vector before context update");
               Derivation.Message.Update_AV_Enumeration_Vector (Context, Sequence_Context);
               Assert (Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
                       "Invalid AV_Enumeration_Vector after context update");

               Assert (Sequence_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image,
                       "Invalid Sequence_Context.Last");
            else
               Assert (False, "Invalid AV_Enumeration_Vector or Buffer");
            end if;
         end;
      else
         Assert (False, "Invalid Length");
      end if;

      Assert (Derivation.Message.Valid_Message (Context), "Invalid Message after complete parsing");

      Derivation.Message.Take_Buffer (Context, Buffer);
      Free_Bytes_Ptr (Buffer);

      Assert (Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image, "Invalid Context.Last");
   end Test_Parsing_Derivation_Message;

   procedure Test_Generating_Derivation_Message (T : in out AUnit.Test_Cases.Test_Case'Class) with
     SPARK_Mode, Pre => True
   is
      pragma Unreferenced (T);
      Expected                      : RFLX_Builtin_Types.Bytes_Ptr :=
        new RFLX_Builtin_Types.Bytes'(4, 0, 1, 0, 2, 1, 2, 1, 2, 1, 2);
      Buffer                        : RFLX_Builtin_Types.Bytes_Ptr :=
        new RFLX_Builtin_Types.Bytes'(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
      Context                       : Derivation.Message.Context;
      Modular_Vector_Context        : Arrays.Modular_Vector.Context;
      Range_Vector_Context          : Arrays.Range_Vector.Context;
      Enumeration_Vector_Context    : Arrays.Enumeration_Vector.Context;
      AV_Enumeration_Vector_Context : Arrays.AV_Enumeration_Vector.Context;
   begin
      Derivation.Message.Initialize (Context, Buffer);
      Derivation.Message.Set_Length (Context, 4);

      Derivation.Message.Switch_To_Modular_Vector (Context, Modular_Vector_Context);
      Arrays.Modular_Vector.Append_Element (Modular_Vector_Context, 1);
      Arrays.Modular_Vector.Append_Element (Modular_Vector_Context, 2);
      Assert (not Arrays.Modular_Vector.Valid_Element (Modular_Vector_Context),
              "Invalid acceptance of further element");
      Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
              "Valid Modular_Vector before context update");
      Derivation.Message.Update_Modular_Vector (Context, Modular_Vector_Context);
      Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Modular_Vector),
              "Invalid Modular_Vector after context update");
      Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete generating");

      Derivation.Message.Switch_To_Range_Vector (Context, Range_Vector_Context);
      Arrays.Range_Vector.Append_Element (Range_Vector_Context, 1);
      Arrays.Range_Vector.Append_Element (Range_Vector_Context, 2);
      Assert (not Arrays.Range_Vector.Valid_Element (Range_Vector_Context), "Invalid acceptance of further element");
      Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
              "Valid Range_Vector before context update");
      Derivation.Message.Update_Range_Vector (Context, Range_Vector_Context);
      Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Range_Vector),
              "Invalid Range_Vector after context update");
      Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete generating");

      Derivation.Message.Switch_To_Enumeration_Vector (Context, Enumeration_Vector_Context);
      Arrays.Enumeration_Vector.Append_Element (Enumeration_Vector_Context, Arrays.ONE);
      Arrays.Enumeration_Vector.Append_Element (Enumeration_Vector_Context, Arrays.TWO);
      Assert (not Arrays.Enumeration_Vector.Valid_Element (Enumeration_Vector_Context),
              "Invalid acceptance of further element");
      Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
              "Valid Enumeration_Vector before context update");
      Derivation.Message.Update_Enumeration_Vector (Context, Enumeration_Vector_Context);
      Assert (Derivation.Message.Valid (Context, Derivation.Message.F_Enumeration_Vector),
              "Invalid Enumeration_Vector after context update");
      Assert (not Derivation.Message.Valid_Message (Context), "Valid Message before complete generating");

      Derivation.Message.Switch_To_AV_Enumeration_Vector (Context, AV_Enumeration_Vector_Context);
      Arrays.AV_Enumeration_Vector.Append_Element (AV_Enumeration_Vector_Context, Arrays.To_Actual (Arrays.AV_ONE));
      Arrays.AV_Enumeration_Vector.Append_Element (AV_Enumeration_Vector_Context, Arrays.To_Actual (Arrays.AV_TWO));
      Assert (not Arrays.AV_Enumeration_Vector.Valid_Element (AV_Enumeration_Vector_Context),
              "Invalid acceptance of further element");
      Assert (not Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
              "Valid AV_Enumeration_Vector before context update");
      Derivation.Message.Update_AV_Enumeration_Vector (Context, AV_Enumeration_Vector_Context);
      Assert (Derivation.Message.Valid (Context, Derivation.Message.F_AV_Enumeration_Vector),
              "Invalid AV_Enumeration_Vector after context update");
      Assert (Derivation.Message.Valid_Message (Context), "Invalid Message after complete generating");

      Derivation.Message.Take_Buffer (Context, Buffer);
      Assert (RFLX_Builtin_Types.Length'Image (RFLX_Types.Byte_Index (Context.Last)
              - RFLX_Types.Byte_Index (Context.First) + 1), Expected'Length'Img,
              "Invalid buffer length");
      Assert (Buffer.all (RFLX_Types.Byte_Index (Context.First) .. RFLX_Types.Byte_Index (Context.Last)), Expected.all,
              "Invalid binary representation");

      Free_Bytes_Ptr (Expected);
      Free_Bytes_Ptr (Buffer);

      Assert (Modular_Vector_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (40)'Image,
              "Invalid Modular_Vector_Context.Last");
      Assert (Range_Vector_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (56)'Image,
              "Invalid Range_Vector_Context.Last");
      Assert (Enumeration_Vector_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (72)'Image,
              "Invalid Enumeration_Vector_Context.Last");
      Assert (AV_Enumeration_Vector_Context.Last'Image, RFLX_Builtin_Types.Bit_Length (88)'Image,
              "Invalid AV_Enumeration_Vector_Context.Last");
   end Test_Generating_Derivation_Message;

   overriding
   procedure Register_Tests (T : in out Test) is
      use AUnit.Test_Cases.Registration;
   begin
      Register_Routine (T, Test_Parsing_Derivation_Modular_Sequential'Access, "Parsing Modular Sequential");
      Register_Routine (T, Test_Parsing_Derivation_Modular_Loop'Access, "Parsing Modular Loop");
      Register_Routine (T, Test_Parsing_Derivation_Range_Sequential'Access, "Parsing Range Sequential");
      Register_Routine (T, Test_Parsing_Derivation_Range_Loop'Access, "Parsing Range Loop");
      Register_Routine (T, Test_Parsing_Derivation_Enumeration_Sequential'Access, "Parsing Enumeration Sequential");
      Register_Routine (T, Test_Parsing_Derivation_Enumeration_Loop'Access, "Parsing Enumeration Loop");
      Register_Routine (T, Test_Parsing_Arrays_AV_Enumeration_Sequential'Access, "Parsing AV_Enumeration Sequential");
      Register_Routine (T, Test_Parsing_Arrays_AV_Enumeration_Loop'Access, "Parsing AV_Enumeration Loop");
      Register_Routine (T, Test_Parsing_Derivation_Message'Access, "Parsing Message");
      Register_Routine (T, Test_Generating_Derivation_Message'Access, "Generating Message");
   end Register_Tests;

end RFLX.Derivation.Tests;
