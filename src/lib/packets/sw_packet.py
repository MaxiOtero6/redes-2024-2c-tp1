from struct import pack, unpack


class SWPacket:
    """
    +------------------------+------------------------+------------------------+------------------------+ # noqa
    |  Sequence Number (1B)  |     ACK Number (1B)    |        SYN (1B)        |        FIN (1B)        | # noqa
    +------------------------+------------------------+------------------------+------------------------+ # noqa
    |        ACK (1B)        |        UPL (1B)        |        DWL (1B)        |      Padding (1B)      | # noqa
    +------------------------+------------------------+------------------------+------------------------+ # noqa
    |                                                                                                   | # noqa
    |                                            Data (5KB)                                            | # noqa
    |                                                                                                   | # noqa
    +------------------------+------------------------+------------------------+------------------------+ # noqa
    """

    seq_number: int
    ack_number: int
    syn: bool
    fin: bool
    ack: bool
    upl: bool
    dwl: bool
    payload: bytes

    def __init__(
        self,
        seq_number: int,
        ack_number: int,
        syn: bool,
        fin: bool,
        ack: bool,
        upl: bool,
        dwl: bool,
        data: bytes,
    ):
        self.seq_number = seq_number
        self.payload = data
        self.ack_number = ack_number
        self.syn = syn
        self.fin = fin
        self.ack = ack
        self.upl = upl
        self.dwl = dwl

    def encode(self) -> bytes:
        data: bytes = b""

        data += pack(
            "!BBBBBBB",
            self.seq_number,
            self.ack_number,
            self.syn,
            self.fin,
            self.ack,
            self.upl,
            self.dwl,
        )
        data += b"\x00"  # padding
        data += self.payload

        return data

    @staticmethod
    def decode(data: bytes) -> "SWPacket":
        seq_number: int
        ack_number: int
        syn: bool
        fin: bool
        ack: bool

        idx_before_padding: int = 7
        idx_after_padding: int = 8

        seq_number, ack_number, syn, fin, ack, upl, dwl = unpack(
            "!BBBBBBB", data[:idx_before_padding:]
        )

        payload: bytes = data[idx_after_padding::]

        return SWPacket(seq_number, ack_number, syn, fin, ack, upl, dwl, payload)
