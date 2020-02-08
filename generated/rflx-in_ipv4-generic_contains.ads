with RFLX.Generic_Types;
with RFLX.IPv4;
use RFLX.IPv4;
with RFLX.IPv4.Generic_Packet;
with RFLX.UDP.Generic_Datagram;

generic
   with package Types is new RFLX.Generic_Types (<>);
   with package IPv4_Packet is new RFLX.IPv4.Generic_Packet (Types, others => <>);
   with package UDP_Datagram is new RFLX.UDP.Generic_Datagram (Types, others => <>);
package RFLX.In_IPv4.Generic_Contains with
  SPARK_Mode
is

   pragma Annotate (GNATprove, Terminating, Generic_Contains);

   use type Types.Bytes, Types.Bytes_Ptr, Types.Index, Types.Length, Types.Bit_Index, Types.Bit_Length, IPv4_Packet.Field_Cursors;

   function UDP_Datagram_In_IPv4_Packet_Payload (Ctx : IPv4_Packet.Context) return Boolean is
     (IPv4_Packet.Has_Buffer (Ctx)
      and then IPv4_Packet.Present (Ctx, IPv4_Packet.F_Payload)
      and then IPv4_Packet.Valid (Ctx, IPv4_Packet.F_Protocol)
      and then IPv4_Packet.Get_Protocol (Ctx).Known
      and then IPv4_Packet.Get_Protocol (Ctx).Enum = PROTOCOL_UDP);

   procedure Switch_To_Payload (IPv4_Packet_Context : in out IPv4_Packet.Context; UDP_Datagram_Context : out UDP_Datagram.Context) with
     Pre =>
       not IPv4_Packet_Context'Constrained
          and not UDP_Datagram_Context'Constrained
          and IPv4_Packet.Has_Buffer (IPv4_Packet_Context)
          and IPv4_Packet.Present (IPv4_Packet_Context, IPv4_Packet.F_Payload)
          and IPv4_Packet.Valid (IPv4_Packet_Context, IPv4_Packet.F_Protocol)
          and UDP_Datagram_In_IPv4_Packet_Payload (IPv4_Packet_Context),
     Post =>
       not IPv4_Packet.Has_Buffer (IPv4_Packet_Context)
          and UDP_Datagram.Has_Buffer (UDP_Datagram_Context)
          and IPv4_Packet_Context.Buffer_First = UDP_Datagram_Context.Buffer_First
          and IPv4_Packet_Context.Buffer_Last = UDP_Datagram_Context.Buffer_Last
          and UDP_Datagram_Context.First = IPv4_Packet.Field_First (IPv4_Packet_Context, IPv4_Packet.F_Payload)
          and UDP_Datagram_Context.Last = IPv4_Packet.Field_Last (IPv4_Packet_Context, IPv4_Packet.F_Payload)
          and UDP_Datagram.Initialized (UDP_Datagram_Context)
          and IPv4_Packet_Context.Buffer_First = IPv4_Packet_Context.Buffer_First'Old
          and IPv4_Packet_Context.Buffer_Last = IPv4_Packet_Context.Buffer_Last'Old
          and IPv4_Packet_Context.First = IPv4_Packet_Context.First'Old
          and IPv4_Packet.Cursors (IPv4_Packet_Context) = IPv4_Packet.Cursors (IPv4_Packet_Context)'Old;

end RFLX.In_IPv4.Generic_Contains;