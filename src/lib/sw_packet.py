from struct import pack, unpack


class SWPacket:
    """
        +--------------------+---------------+--------+----------+
        |  Sequence Number 1B | ACK Number 1B | SYN 1B | FIN 1B  |
        +--------------------+---------------+--------+----------+
        |               ACK 1B      |       Padding 3B           |
        +---------------------+---------------------+------------+
        |                                                        |
        |                      Data 512B                         |
        |                                                        |
        +---------------------+---------------------+------------+
    """

    seq_number: int
    ack_number: int
    syn: bool
    fin: bool
    ack: bool
    payload: bytes

    def __init__(self, seq_number: int, ack_number: int, syn: bool, fin: bool, ack: bool, data: bytes):
        self.seq_number = seq_number
        self.payload = data
        self.ack_number = ack_number
        self.syn = syn
        self.fin = fin
        self.ack = ack
        # seq_number == 1 ? 0 : 1

    def encode(self) -> bytes:
        data: bytes = b""

        data += pack(
            "!BBBBB", self.seq_number, self.ack_number,
            self.syn, self.fin, self.ack
        )
        data += b"\x00\x00\x00"  # padding
        data += self.payload

        return data

    @staticmethod
    def decode(data: bytes) -> "SWPacket":
        seq_number: int
        ack_number: int
        syn: bool
        fin: bool
        ack: bool

        idx_before_padding: int = 5
        idx_after_padding: int = 8

        seq_number, ack_number, syn, fin, ack = unpack(
            "!BBBBB", data[:idx_before_padding:]
        )

        payload: bytes = data[idx_after_padding::]

        return SWPacket(seq_number, ack_number, syn, fin, ack, payload)
