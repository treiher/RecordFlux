def checksum_icmp(msg: MessageValue) -> int:
    def add_ones_complement(num1, num2) -> int:
        MOD = 1 << 16
        result = num1 + num2
        return result if result < MOD else (result + 1) % MOD

    msg.set("Checksum", 0)
    message_in_sixteen_bit_chunks = [
        int.from_bytes(msg.bytestring[i : i + 2], "big") for i in range(0, len(msg.bytestring), 2)
    ]
    intermediary_result = message_in_sixteen_bit_chunks[0]
    for i in range(1, len(message_in_sixteen_bit_chunks)):
        intermediary_result = add_ones_complement(
            intermediary_result, message_in_sixteen_bit_chunks[i]
        )

    return intermediary_result ^ 0xFFFF
