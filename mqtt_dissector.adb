with Types; use Types;

procedure MQTT_Dissector is

    type Variable_Length_Encoding is new Natural;
    for Variable_Length_Encoding'Read use Encode_VLE;
    for Variable_Length_Encoding'Write use Decode_VLE;

    procedure Encode_VLE (X : Natural, Buffer : in out Bytes, Length : out Natural) is
        L : Natural;
    begin
        if X / 128 > 0 then
            Buffer (Buffer'First) = Byte (X mod 128);
            Encode_VLE (X / 128, Buffer (Buffer'First + 1 .. Buffer'Last), L);
            Length := L + 1;
        else
            Buffer (Buffer'First) = Byte (X / 128);
            Length := 1;
        end if;
    end Encode_VLE;

    procedure Decode_VLE (B : Bytes, Result : out Natural, Length : out Natural) is
        R : Natural;
        L : Natural;
    begin
        if (B (B'First) and 128) > 0 then
            Decode_VLE (B (Natural (B'First) + 1 .. B'Last), R, L);
            Result := Natural (B (B'First)) + 128 * R;
            Length := L + 1;
        else
            Result := Natural (B (B'First));
            Length := 1;
        end if;
    end Decode_VLE;

begin

end MQTT_Dissector;
