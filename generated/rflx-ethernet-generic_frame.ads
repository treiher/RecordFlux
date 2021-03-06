pragma Style_Checks ("N3aAbcdefhiIklnOprStux");
with RFLX.RFLX_Generic_Types;

generic
   with package Types is new RFLX.RFLX_Generic_Types (<>);
package RFLX.Ethernet.Generic_Frame with
  SPARK_Mode,
  Annotate =>
    (GNATprove, Terminating)
is

   use type Types.Bytes, Types.Bytes_Ptr, Types.Index, Types.Bit_Index;

   type Virtual_Field is (F_Initial, F_Destination, F_Source, F_Type_Length_TPID, F_TPID, F_TCI, F_Type_Length, F_Payload, F_Final);

   subtype Field is Virtual_Field range F_Destination .. F_Payload;

   type Field_Cursor is private with
     Default_Initial_Condition =>
       False;

   type Field_Cursors is private with
     Default_Initial_Condition =>
       False;

   type Context (Buffer_First, Buffer_Last : Types.Index := Types.Index'First; First, Last : Types.Bit_Index := Types.Bit_Index'First) is private with
     Default_Initial_Condition =>
       Types.Byte_Index (First) >= Buffer_First
       and Types.Byte_Index (Last) <= Buffer_Last
       and First <= Last
       and Last <= Types.Bit_Index'Last / 2;

   type Field_Dependent_Value (Fld : Virtual_Field := F_Initial) is
      record
         case Fld is
            when F_Initial | F_Payload | F_Final =>
               null;
            when F_Destination =>
               Destination_Value : RFLX.Ethernet.Address;
            when F_Source =>
               Source_Value : RFLX.Ethernet.Address;
            when F_Type_Length_TPID =>
               Type_Length_TPID_Value : RFLX.Ethernet.Type_Length_Base;
            when F_TPID =>
               TPID_Value : RFLX.Ethernet.TPID_Base;
            when F_TCI =>
               TCI_Value : RFLX.Ethernet.TCI;
            when F_Type_Length =>
               Type_Length_Value : RFLX.Ethernet.Type_Length_Base;
         end case;
      end record;

   procedure Initialize (Ctx : out Context; Buffer : in out Types.Bytes_Ptr) with
     Pre =>
       not Ctx'Constrained
       and then Buffer /= null
       and then Buffer'Length > 0
       and then Buffer'Last <= Types.Index'Last / 2,
     Post =>
       Has_Buffer (Ctx)
       and Buffer = null
       and Ctx.Buffer_First = Buffer'First'Old
       and Ctx.Buffer_Last = Buffer'Last'Old
       and Ctx.First = Types.First_Bit_Index (Ctx.Buffer_First)
       and Initialized (Ctx),
     Depends =>
       (Ctx => Buffer, Buffer => null);

   procedure Initialize (Ctx : out Context; Buffer : in out Types.Bytes_Ptr; First, Last : Types.Bit_Index) with
     Pre =>
       not Ctx'Constrained
       and then Buffer /= null
       and then Buffer'Length > 0
       and then Types.Byte_Index (First) >= Buffer'First
       and then Types.Byte_Index (Last) <= Buffer'Last
       and then First <= Last
       and then Last <= Types.Bit_Index'Last / 2,
     Post =>
       Buffer = null
       and Has_Buffer (Ctx)
       and Ctx.Buffer_First = Buffer'First'Old
       and Ctx.Buffer_Last = Buffer'Last'Old
       and Ctx.First = First
       and Ctx.Last = Last
       and Initialized (Ctx),
     Depends =>
       (Ctx => (Buffer, First, Last), Buffer => null);

   function Initialized (Ctx : Context) return Boolean with
     Ghost;

   procedure Take_Buffer (Ctx : in out Context; Buffer : out Types.Bytes_Ptr) with
     Pre =>
       Has_Buffer (Ctx),
     Post =>
       not Has_Buffer (Ctx)
       and Buffer /= null
       and Ctx.Buffer_First = Buffer'First
       and Ctx.Buffer_Last = Buffer'Last
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Ctx.Last = Ctx.Last'Old
       and Context_Cursors (Ctx) = Context_Cursors (Ctx)'Old,
     Depends =>
       (Ctx => Ctx, Buffer => Ctx);

   function Has_Buffer (Ctx : Context) return Boolean;

   function Message_Last (Ctx : Context) return Types.Bit_Index with
     Pre =>
       Has_Buffer (Ctx)
       and then Structural_Valid_Message (Ctx);

   function Path_Condition (Ctx : Context; Fld : Field) return Boolean with
     Pre =>
       Valid_Predecessor (Ctx, Fld);

   function Field_Condition (Ctx : Context; Val : Field_Dependent_Value; Length : Types.Bit_Length := 0) return Boolean with
     Pre =>
       Has_Buffer (Ctx)
       and Val.Fld in Field'Range
       and Valid_Predecessor (Ctx, Val.Fld);

   function Field_Length (Ctx : Context; Fld : Field) return Types.Bit_Length with
     Pre =>
       Valid_Next (Ctx, Fld);

   function Field_First (Ctx : Context; Fld : Field) return Types.Bit_Index with
     Pre =>
       Valid_Next (Ctx, Fld);

   function Field_Last (Ctx : Context; Fld : Field) return Types.Bit_Index with
     Pre =>
       Valid_Next (Ctx, Fld);

   function Predecessor (Ctx : Context; Fld : Virtual_Field) return Virtual_Field;

   function Valid_Predecessor (Ctx : Context; Fld : Virtual_Field) return Boolean;

   function Valid_Next (Ctx : Context; Fld : Field) return Boolean;

   function Available_Space (Ctx : Context; Fld : Field) return Types.Bit_Length with
     Pre =>
       Valid_Next (Ctx, Fld);

   function Equal (Ctx : Context; Fld : Field; Data : Types.Bytes) return Boolean with
     Pre =>
       Has_Buffer (Ctx)
       and Valid_Next (Ctx, Fld);

   procedure Verify (Ctx : in out Context; Fld : Field) with
     Post =>
       Has_Buffer (Ctx) = Has_Buffer (Ctx)'Old
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Ctx.Last = Ctx.Last'Old;

   procedure Verify_Message (Ctx : in out Context) with
     Post =>
       Has_Buffer (Ctx) = Has_Buffer (Ctx)'Old
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Ctx.Last = Ctx.Last'Old;

   function Present (Ctx : Context; Fld : Field) return Boolean;

   function Structural_Valid (Ctx : Context; Fld : Field) return Boolean;

   function Valid (Ctx : Context; Fld : Field) return Boolean with
     Post =>
       (if
           Valid'Result
        then
           Structural_Valid (Ctx, Fld)
           and Present (Ctx, Fld));

   function Incomplete (Ctx : Context; Fld : Field) return Boolean;

   function Invalid (Ctx : Context; Fld : Field) return Boolean;

   function Structural_Valid_Message (Ctx : Context) return Boolean with
     Pre =>
       Has_Buffer (Ctx);

   function Valid_Message (Ctx : Context) return Boolean with
     Pre =>
       Has_Buffer (Ctx);

   function Incomplete_Message (Ctx : Context) return Boolean;

   function Get_Destination (Ctx : Context) return RFLX.Ethernet.Address with
     Pre =>
       Valid (Ctx, F_Destination);

   function Get_Source (Ctx : Context) return RFLX.Ethernet.Address with
     Pre =>
       Valid (Ctx, F_Source);

   function Get_Type_Length_TPID (Ctx : Context) return RFLX.Ethernet.Type_Length with
     Pre =>
       Valid (Ctx, F_Type_Length_TPID);

   function Get_TPID (Ctx : Context) return RFLX.Ethernet.TPID with
     Pre =>
       Valid (Ctx, F_TPID);

   function Get_TCI (Ctx : Context) return RFLX.Ethernet.TCI with
     Pre =>
       Valid (Ctx, F_TCI);

   function Get_Type_Length (Ctx : Context) return RFLX.Ethernet.Type_Length with
     Pre =>
       Valid (Ctx, F_Type_Length);

   generic
      with procedure Process_Payload (Payload : Types.Bytes);
   procedure Get_Payload (Ctx : Context) with
     Pre =>
       Has_Buffer (Ctx)
       and Present (Ctx, F_Payload);

   procedure Set_Destination (Ctx : in out Context; Val : RFLX.Ethernet.Address) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Destination)
       and then Field_Last (Ctx, F_Destination) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (F_Destination, Val))
       and then Valid (Val)
       and then Available_Space (Ctx, F_Destination) >= Field_Length (Ctx, F_Destination),
     Post =>
       Has_Buffer (Ctx)
       and Valid (Ctx, F_Destination)
       and Get_Destination (Ctx) = Val
       and Invalid (Ctx, F_Source)
       and Invalid (Ctx, F_Type_Length_TPID)
       and Invalid (Ctx, F_TPID)
       and Invalid (Ctx, F_TCI)
       and Invalid (Ctx, F_Type_Length)
       and Invalid (Ctx, F_Payload)
       and (Predecessor (Ctx, F_Source) = F_Destination
            and Valid_Next (Ctx, F_Source))
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Destination) = Predecessor (Ctx, F_Destination)'Old
       and Valid_Next (Ctx, F_Destination) = Valid_Next (Ctx, F_Destination)'Old;

   procedure Set_Source (Ctx : in out Context; Val : RFLX.Ethernet.Address) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Source)
       and then Field_Last (Ctx, F_Source) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (F_Source, Val))
       and then Valid (Val)
       and then Available_Space (Ctx, F_Source) >= Field_Length (Ctx, F_Source),
     Post =>
       Has_Buffer (Ctx)
       and Valid (Ctx, F_Source)
       and Get_Source (Ctx) = Val
       and Invalid (Ctx, F_Type_Length_TPID)
       and Invalid (Ctx, F_TPID)
       and Invalid (Ctx, F_TCI)
       and Invalid (Ctx, F_Type_Length)
       and Invalid (Ctx, F_Payload)
       and (Predecessor (Ctx, F_Type_Length_TPID) = F_Source
            and Valid_Next (Ctx, F_Type_Length_TPID))
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Source) = Predecessor (Ctx, F_Source)'Old
       and Valid_Next (Ctx, F_Source) = Valid_Next (Ctx, F_Source)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Context_Cursor (Ctx, F_Destination) = Context_Cursor (Ctx, F_Destination)'Old;

   procedure Set_Type_Length_TPID (Ctx : in out Context; Val : RFLX.Ethernet.Type_Length) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Type_Length_TPID)
       and then Field_Last (Ctx, F_Type_Length_TPID) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (F_Type_Length_TPID, Val))
       and then Valid (Val)
       and then Available_Space (Ctx, F_Type_Length_TPID) >= Field_Length (Ctx, F_Type_Length_TPID),
     Post =>
       Has_Buffer (Ctx)
       and Valid (Ctx, F_Type_Length_TPID)
       and Get_Type_Length_TPID (Ctx) = Val
       and Invalid (Ctx, F_TPID)
       and Invalid (Ctx, F_TCI)
       and Invalid (Ctx, F_Type_Length)
       and Invalid (Ctx, F_Payload)
       and (if
               Types.Bit_Length (Get_Type_Length_TPID (Ctx)) = 16#8100#
            then
               Predecessor (Ctx, F_TPID) = F_Type_Length_TPID
               and Valid_Next (Ctx, F_TPID))
       and (if
               Types.Bit_Length (Get_Type_Length_TPID (Ctx)) /= 16#8100#
            then
               Predecessor (Ctx, F_Type_Length) = F_Type_Length_TPID
               and Valid_Next (Ctx, F_Type_Length))
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Type_Length_TPID) = Predecessor (Ctx, F_Type_Length_TPID)'Old
       and Valid_Next (Ctx, F_Type_Length_TPID) = Valid_Next (Ctx, F_Type_Length_TPID)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Context_Cursor (Ctx, F_Destination) = Context_Cursor (Ctx, F_Destination)'Old
       and Context_Cursor (Ctx, F_Source) = Context_Cursor (Ctx, F_Source)'Old;

   procedure Set_TPID (Ctx : in out Context; Val : RFLX.Ethernet.TPID) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_TPID)
       and then Field_Last (Ctx, F_TPID) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (F_TPID, Val))
       and then Valid (Val)
       and then Available_Space (Ctx, F_TPID) >= Field_Length (Ctx, F_TPID),
     Post =>
       Has_Buffer (Ctx)
       and Valid (Ctx, F_TPID)
       and Get_TPID (Ctx) = Val
       and Invalid (Ctx, F_TCI)
       and Invalid (Ctx, F_Type_Length)
       and Invalid (Ctx, F_Payload)
       and (Predecessor (Ctx, F_TCI) = F_TPID
            and Valid_Next (Ctx, F_TCI))
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_TPID) = Predecessor (Ctx, F_TPID)'Old
       and Valid_Next (Ctx, F_TPID) = Valid_Next (Ctx, F_TPID)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Get_Type_Length_TPID (Ctx) = Get_Type_Length_TPID (Ctx)'Old
       and Context_Cursor (Ctx, F_Destination) = Context_Cursor (Ctx, F_Destination)'Old
       and Context_Cursor (Ctx, F_Source) = Context_Cursor (Ctx, F_Source)'Old
       and Context_Cursor (Ctx, F_Type_Length_TPID) = Context_Cursor (Ctx, F_Type_Length_TPID)'Old;

   procedure Set_TCI (Ctx : in out Context; Val : RFLX.Ethernet.TCI) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_TCI)
       and then Field_Last (Ctx, F_TCI) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (F_TCI, Val))
       and then Valid (Val)
       and then Available_Space (Ctx, F_TCI) >= Field_Length (Ctx, F_TCI),
     Post =>
       Has_Buffer (Ctx)
       and Valid (Ctx, F_TCI)
       and Get_TCI (Ctx) = Val
       and Invalid (Ctx, F_Type_Length)
       and Invalid (Ctx, F_Payload)
       and (Predecessor (Ctx, F_Type_Length) = F_TCI
            and Valid_Next (Ctx, F_Type_Length))
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_TCI) = Predecessor (Ctx, F_TCI)'Old
       and Valid_Next (Ctx, F_TCI) = Valid_Next (Ctx, F_TCI)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Get_Type_Length_TPID (Ctx) = Get_Type_Length_TPID (Ctx)'Old
       and Get_TPID (Ctx) = Get_TPID (Ctx)'Old
       and Context_Cursor (Ctx, F_Destination) = Context_Cursor (Ctx, F_Destination)'Old
       and Context_Cursor (Ctx, F_Source) = Context_Cursor (Ctx, F_Source)'Old
       and Context_Cursor (Ctx, F_Type_Length_TPID) = Context_Cursor (Ctx, F_Type_Length_TPID)'Old
       and Context_Cursor (Ctx, F_TPID) = Context_Cursor (Ctx, F_TPID)'Old;

   procedure Set_Type_Length (Ctx : in out Context; Val : RFLX.Ethernet.Type_Length) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Type_Length)
       and then Field_Last (Ctx, F_Type_Length) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (F_Type_Length, Val))
       and then Valid (Val)
       and then Available_Space (Ctx, F_Type_Length) >= Field_Length (Ctx, F_Type_Length),
     Post =>
       Has_Buffer (Ctx)
       and Valid (Ctx, F_Type_Length)
       and Get_Type_Length (Ctx) = Val
       and Invalid (Ctx, F_Payload)
       and (if
               Types.Bit_Length (Get_Type_Length (Ctx)) <= 1500
            then
               Predecessor (Ctx, F_Payload) = F_Type_Length
               and Valid_Next (Ctx, F_Payload))
       and (if
               Types.Bit_Length (Get_Type_Length (Ctx)) >= 1536
            then
               Predecessor (Ctx, F_Payload) = F_Type_Length
               and Valid_Next (Ctx, F_Payload))
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Type_Length) = Predecessor (Ctx, F_Type_Length)'Old
       and Valid_Next (Ctx, F_Type_Length) = Valid_Next (Ctx, F_Type_Length)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Get_Type_Length_TPID (Ctx) = Get_Type_Length_TPID (Ctx)'Old
       and Context_Cursor (Ctx, F_Destination) = Context_Cursor (Ctx, F_Destination)'Old
       and Context_Cursor (Ctx, F_Source) = Context_Cursor (Ctx, F_Source)'Old
       and Context_Cursor (Ctx, F_Type_Length_TPID) = Context_Cursor (Ctx, F_Type_Length_TPID)'Old
       and Context_Cursor (Ctx, F_TPID) = Context_Cursor (Ctx, F_TPID)'Old
       and Context_Cursor (Ctx, F_TCI) = Context_Cursor (Ctx, F_TCI)'Old;

   generic
      with procedure Process_Payload (Payload : out Types.Bytes);
   procedure Set_Payload (Ctx : in out Context) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Payload)
       and then Field_Last (Ctx, F_Payload) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (Fld => F_Payload), Field_Length (Ctx, F_Payload))
       and then Available_Space (Ctx, F_Payload) >= Field_Length (Ctx, F_Payload),
     Post =>
       Has_Buffer (Ctx)
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Payload) = Predecessor (Ctx, F_Payload)'Old
       and Valid_Next (Ctx, F_Payload) = Valid_Next (Ctx, F_Payload)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Get_Type_Length_TPID (Ctx) = Get_Type_Length_TPID (Ctx)'Old
       and Get_Type_Length (Ctx) = Get_Type_Length (Ctx)'Old
       and Structural_Valid (Ctx, F_Payload);

   generic
      with procedure Process_Payload (Payload : out Types.Bytes);
   procedure Set_Bounded_Payload (Ctx : in out Context; Length : Types.Bit_Length) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Payload)
       and then Field_Last (Ctx, F_Payload) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (Fld => F_Payload), Length)
       and then Available_Space (Ctx, F_Payload) >= Length
       and then (Field_First (Ctx, F_Payload) + Length) <= Types.Bit_Index'Last / 2
       and then ((Valid (Ctx, F_Type_Length)
                  and Get_Type_Length (Ctx) >= 1536)),
     Post =>
       Has_Buffer (Ctx)
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Payload) = Predecessor (Ctx, F_Payload)'Old
       and Valid_Next (Ctx, F_Payload) = Valid_Next (Ctx, F_Payload)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Get_Type_Length_TPID (Ctx) = Get_Type_Length_TPID (Ctx)'Old
       and Get_Type_Length (Ctx) = Get_Type_Length (Ctx)'Old
       and Structural_Valid (Ctx, F_Payload);

   procedure Initialize_Payload (Ctx : in out Context) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Payload)
       and then Field_Last (Ctx, F_Payload) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (Fld => F_Payload), Field_Length (Ctx, F_Payload))
       and then Available_Space (Ctx, F_Payload) >= Field_Length (Ctx, F_Payload),
     Post =>
       Has_Buffer (Ctx)
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Payload) = Predecessor (Ctx, F_Payload)'Old
       and Valid_Next (Ctx, F_Payload) = Valid_Next (Ctx, F_Payload)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Get_Type_Length_TPID (Ctx) = Get_Type_Length_TPID (Ctx)'Old
       and Get_Type_Length (Ctx) = Get_Type_Length (Ctx)'Old
       and Structural_Valid (Ctx, F_Payload);

   procedure Initialize_Bounded_Payload (Ctx : in out Context; Length : Types.Bit_Length) with
     Pre =>
       not Ctx'Constrained
       and then Has_Buffer (Ctx)
       and then Valid_Next (Ctx, F_Payload)
       and then Field_Last (Ctx, F_Payload) <= Types.Bit_Index'Last / 2
       and then Field_Condition (Ctx, (Fld => F_Payload), Length)
       and then Available_Space (Ctx, F_Payload) >= Length
       and then (Field_First (Ctx, F_Payload) + Length) <= Types.Bit_Index'Last / 2
       and then ((Valid (Ctx, F_Type_Length)
                  and Get_Type_Length (Ctx) >= 1536)),
     Post =>
       Has_Buffer (Ctx)
       and Ctx.Buffer_First = Ctx.Buffer_First'Old
       and Ctx.Buffer_Last = Ctx.Buffer_Last'Old
       and Ctx.First = Ctx.First'Old
       and Predecessor (Ctx, F_Payload) = Predecessor (Ctx, F_Payload)'Old
       and Valid_Next (Ctx, F_Payload) = Valid_Next (Ctx, F_Payload)'Old
       and Get_Destination (Ctx) = Get_Destination (Ctx)'Old
       and Get_Source (Ctx) = Get_Source (Ctx)'Old
       and Get_Type_Length_TPID (Ctx) = Get_Type_Length_TPID (Ctx)'Old
       and Get_Type_Length (Ctx) = Get_Type_Length (Ctx)'Old
       and Structural_Valid (Ctx, F_Payload);

   function Context_Cursor (Ctx : Context; Fld : Field) return Field_Cursor with
     Annotate =>
       (GNATprove, Inline_For_Proof),
     Ghost;

   function Context_Cursors (Ctx : Context) return Field_Cursors with
     Annotate =>
       (GNATprove, Inline_For_Proof),
     Ghost;

private

   type Cursor_State is (S_Valid, S_Structural_Valid, S_Invalid, S_Incomplete);

   function Valid_Value (Val : Field_Dependent_Value) return Boolean is
     ((case Val.Fld is
          when F_Destination =>
             Valid (Val.Destination_Value),
          when F_Source =>
             Valid (Val.Source_Value),
          when F_Type_Length_TPID =>
             Valid (Val.Type_Length_TPID_Value),
          when F_TPID =>
             Valid (Val.TPID_Value),
          when F_TCI =>
             Valid (Val.TCI_Value),
          when F_Type_Length =>
             Valid (Val.Type_Length_Value),
          when F_Payload =>
             True,
          when F_Initial | F_Final =>
             False));

   type Field_Cursor (State : Cursor_State := S_Invalid) is
      record
         Predecessor : Virtual_Field := F_Final;
         case State is
            when S_Valid | S_Structural_Valid =>
               First : Types.Bit_Index := Types.Bit_Index'First;
               Last : Types.Bit_Length := Types.Bit_Length'First;
               Value : Field_Dependent_Value := (Fld => F_Final);
            when S_Invalid | S_Incomplete =>
               null;
         end case;
      end record with
     Dynamic_Predicate =>
       (if
           State = S_Valid
           or State = S_Structural_Valid
        then
           Valid_Value (Field_Cursor.Value));

   type Field_Cursors is array (Virtual_Field) of Field_Cursor;

   function Structural_Valid (Cursor : Field_Cursor) return Boolean is
     (Cursor.State = S_Valid
      or Cursor.State = S_Structural_Valid);

   function Valid (Cursor : Field_Cursor) return Boolean is
     (Cursor.State = S_Valid);

   function Invalid (Cursor : Field_Cursor) return Boolean is
     (Cursor.State = S_Invalid
      or Cursor.State = S_Incomplete);

   function Valid_Context (Buffer_First, Buffer_Last : Types.Index; First, Last : Types.Bit_Index; Buffer : access constant Types.Bytes; Cursors : Field_Cursors) return Boolean is
     ((if
          Buffer /= null
       then
          Buffer'First = Buffer_First
          and Buffer'Last = Buffer_Last)
      and then (Types.Byte_Index (First) >= Buffer_First
                and Types.Byte_Index (Last) <= Buffer_Last
                and First <= Last
                and Last <= Types.Bit_Index'Last / 2)
      and then (for all F in Field'First .. Field'Last =>
                   (if
                       Structural_Valid (Cursors (F))
                    then
                       Cursors (F).First >= First
                       and Cursors (F).Last <= Last
                       and Cursors (F).First <= (Cursors (F).Last + 1)
                       and Cursors (F).Value.Fld = F))
      and then ((if
                    Structural_Valid (Cursors (F_Source))
                 then
                    (Valid (Cursors (F_Destination))
                     and then Cursors (F_Source).Predecessor = F_Destination))
                and then (if
                             Structural_Valid (Cursors (F_Type_Length_TPID))
                          then
                             (Valid (Cursors (F_Source))
                              and then Cursors (F_Type_Length_TPID).Predecessor = F_Source))
                and then (if
                             Structural_Valid (Cursors (F_TPID))
                          then
                             (Valid (Cursors (F_Type_Length_TPID))
                              and then Cursors (F_TPID).Predecessor = F_Type_Length_TPID
                              and then Types.Bit_Length (Cursors (F_Type_Length_TPID).Value.Type_Length_TPID_Value) = 16#8100#))
                and then (if
                             Structural_Valid (Cursors (F_TCI))
                          then
                             (Valid (Cursors (F_TPID))
                              and then Cursors (F_TCI).Predecessor = F_TPID))
                and then (if
                             Structural_Valid (Cursors (F_Type_Length))
                          then
                             (Valid (Cursors (F_Type_Length_TPID))
                              and then Cursors (F_Type_Length).Predecessor = F_Type_Length_TPID
                              and then Types.Bit_Length (Cursors (F_Type_Length_TPID).Value.Type_Length_TPID_Value) /= 16#8100#)
                             or (Valid (Cursors (F_TCI))
                                 and then Cursors (F_Type_Length).Predecessor = F_TCI))
                and then (if
                             Structural_Valid (Cursors (F_Payload))
                          then
                             (Valid (Cursors (F_Type_Length))
                              and then Cursors (F_Payload).Predecessor = F_Type_Length
                              and then Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) <= 1500)
                             or (Valid (Cursors (F_Type_Length))
                                 and then Cursors (F_Payload).Predecessor = F_Type_Length
                                 and then Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) >= 1536)))
      and then ((if
                    Invalid (Cursors (F_Destination))
                 then
                    Invalid (Cursors (F_Source)))
                and then (if
                             Invalid (Cursors (F_Source))
                          then
                             Invalid (Cursors (F_Type_Length_TPID)))
                and then (if
                             Invalid (Cursors (F_Type_Length_TPID))
                          then
                             Invalid (Cursors (F_TPID)))
                and then (if
                             Invalid (Cursors (F_TPID))
                          then
                             Invalid (Cursors (F_TCI)))
                and then (if
                             Invalid (Cursors (F_Type_Length_TPID))
                             and then Invalid (Cursors (F_TCI))
                          then
                             Invalid (Cursors (F_Type_Length)))
                and then (if
                             Invalid (Cursors (F_Type_Length))
                          then
                             Invalid (Cursors (F_Payload))))
      and then (if
                   Structural_Valid (Cursors (F_Destination))
                then
                   (Cursors (F_Destination).Last - Cursors (F_Destination).First + 1) = RFLX.Ethernet.Address'Size
                   and then Cursors (F_Destination).Predecessor = F_Initial
                   and then Cursors (F_Destination).First = First
                   and then (if
                                Structural_Valid (Cursors (F_Source))
                             then
                                (Cursors (F_Source).Last - Cursors (F_Source).First + 1) = RFLX.Ethernet.Address'Size
                                and then Cursors (F_Source).Predecessor = F_Destination
                                and then Cursors (F_Source).First = (Cursors (F_Destination).Last + 1)
                                and then (if
                                             Structural_Valid (Cursors (F_Type_Length_TPID))
                                          then
                                             (Cursors (F_Type_Length_TPID).Last - Cursors (F_Type_Length_TPID).First + 1) = RFLX.Ethernet.Type_Length_Base'Size
                                             and then Cursors (F_Type_Length_TPID).Predecessor = F_Source
                                             and then Cursors (F_Type_Length_TPID).First = (Cursors (F_Source).Last + 1)
                                             and then (if
                                                          Structural_Valid (Cursors (F_TPID))
                                                          and then Types.Bit_Length (Cursors (F_Type_Length_TPID).Value.Type_Length_TPID_Value) = 16#8100#
                                                       then
                                                          (Cursors (F_TPID).Last - Cursors (F_TPID).First + 1) = RFLX.Ethernet.TPID_Base'Size
                                                          and then Cursors (F_TPID).Predecessor = F_Type_Length_TPID
                                                          and then Cursors (F_TPID).First = Cursors (F_Type_Length_TPID).First
                                                          and then (if
                                                                       Structural_Valid (Cursors (F_TCI))
                                                                    then
                                                                       (Cursors (F_TCI).Last - Cursors (F_TCI).First + 1) = RFLX.Ethernet.TCI'Size
                                                                       and then Cursors (F_TCI).Predecessor = F_TPID
                                                                       and then Cursors (F_TCI).First = (Cursors (F_TPID).Last + 1)
                                                                       and then (if
                                                                                    Structural_Valid (Cursors (F_Type_Length))
                                                                                 then
                                                                                    (Cursors (F_Type_Length).Last - Cursors (F_Type_Length).First + 1) = RFLX.Ethernet.Type_Length_Base'Size
                                                                                    and then Cursors (F_Type_Length).Predecessor = F_TCI
                                                                                    and then Cursors (F_Type_Length).First = (Cursors (F_TCI).Last + 1)
                                                                                    and then (if
                                                                                                 Structural_Valid (Cursors (F_Payload))
                                                                                                 and then Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) <= 1500
                                                                                              then
                                                                                                 (Cursors (F_Payload).Last - Cursors (F_Payload).First + 1) = Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) * 8
                                                                                                 and then Cursors (F_Payload).Predecessor = F_Type_Length
                                                                                                 and then Cursors (F_Payload).First = (Cursors (F_Type_Length).Last + 1))
                                                                                    and then (if
                                                                                                 Structural_Valid (Cursors (F_Payload))
                                                                                                 and then Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) >= 1536
                                                                                              then
                                                                                                 (Cursors (F_Payload).Last - Cursors (F_Payload).First + 1) = (Last - Cursors (F_Type_Length).Last)
                                                                                                 and then Cursors (F_Payload).Predecessor = F_Type_Length
                                                                                                 and then Cursors (F_Payload).First = (Cursors (F_Type_Length).Last + 1)))))
                                             and then (if
                                                          Structural_Valid (Cursors (F_Type_Length))
                                                          and then Types.Bit_Length (Cursors (F_Type_Length_TPID).Value.Type_Length_TPID_Value) /= 16#8100#
                                                       then
                                                          (Cursors (F_Type_Length).Last - Cursors (F_Type_Length).First + 1) = RFLX.Ethernet.Type_Length_Base'Size
                                                          and then Cursors (F_Type_Length).Predecessor = F_Type_Length_TPID
                                                          and then Cursors (F_Type_Length).First = Cursors (F_Type_Length_TPID).First
                                                          and then (if
                                                                       Structural_Valid (Cursors (F_Payload))
                                                                       and then Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) <= 1500
                                                                    then
                                                                       (Cursors (F_Payload).Last - Cursors (F_Payload).First + 1) = Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) * 8
                                                                       and then Cursors (F_Payload).Predecessor = F_Type_Length
                                                                       and then Cursors (F_Payload).First = (Cursors (F_Type_Length).Last + 1))
                                                          and then (if
                                                                       Structural_Valid (Cursors (F_Payload))
                                                                       and then Types.Bit_Length (Cursors (F_Type_Length).Value.Type_Length_Value) >= 1536
                                                                    then
                                                                       (Cursors (F_Payload).Last - Cursors (F_Payload).First + 1) = (Last - Cursors (F_Type_Length).Last)
                                                                       and then Cursors (F_Payload).Predecessor = F_Type_Length
                                                                       and then Cursors (F_Payload).First = (Cursors (F_Type_Length).Last + 1)))))));

   type Context (Buffer_First, Buffer_Last : Types.Index := Types.Index'First; First, Last : Types.Bit_Index := Types.Bit_Index'First) is
      record
         Buffer : Types.Bytes_Ptr := null;
         Cursors : Field_Cursors := (others => (State => S_Invalid, Predecessor => F_Final));
      end record with
     Dynamic_Predicate =>
       Valid_Context (Context.Buffer_First, Context.Buffer_Last, Context.First, Context.Last, Context.Buffer, Context.Cursors);

   function Context_Cursor (Ctx : Context; Fld : Field) return Field_Cursor is
     (Ctx.Cursors (Fld));

   function Context_Cursors (Ctx : Context) return Field_Cursors is
     (Ctx.Cursors);

end RFLX.Ethernet.Generic_Frame;
