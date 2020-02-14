# Session Language

## Memory Model

- Assignment of `Result := Message` leads to a copy of `Message`
- Static reservation of memory for declared message variables
    - Static size determined by default value
    - Optimizations:
        - Determine maximum length of message type from specification, use default value for unbounded messages
        - Introduce scoped variables which are reused (static allocation of pointers to scope)
- Potential issues:
    - References may be desirable if large data would be copied in assignment

## Channels

### Properties

- Reliable
- Order-preserving
- Interface:
    - Synchronous/blocking
    - Variable-sized packets

### Interface

- `Message := Read (Channel)`

copy next message from `Channel` into target buffer

- `Success := Write (Channel, Message)`

copy `Message` into `Channel`,
return `True` if successful

- `Result_Message := Call (Channel, Message)`

call `Write (Channel, Message)` and `Result_Message := Read (Channel)` consecutively,
`Result_Message'Valid` yields True if successful and `Result_Message` is valid according to its type

- `Success := Data_Available (Channel)`

return `True` if message is available in `Channel`
