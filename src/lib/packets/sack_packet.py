from struct import pack, unpack

HEADER_MIN_LENGTH_BYTES: int = 16
BOTH_EDGE_SIZES: int = 8
LEFT_EDGE: int = 0
RIGHT_EDGE: int = 1


class SACKPacket:
    """
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                            Sequence Number (4B)                                           | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                         Acknowledgment Number (4B)                                        | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                 Receiver Window (2B)                |         UPL (1B)         |         DWL (1B)         | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |         ACK (1B)         |          SYN (1B)        |         FIN (1B)         |       Blocks (1B)        | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                         Left Edge of Block 1 (4B)                                         | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                        Right Edge of Block 1 (4B)                                         | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                   ....................................                                    | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                         Left Edge of Block N (4B)                                         | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                        Right Edge of Block N (4B)                                         | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    |                                                                                                           | # noqa
    |                                                Data (5KB)                                                 | # noqa
    |                                                                                                           | # noqa
    +--------------------------+--------------------------+--------------------------+--------------------------+ # noqa
    """

    seq_number: int
    ack_number: int
    rwnd: int
    upl: bool
    dwl: bool
    ack: bool
    syn: bool
    fin: bool
    block_edges: list[tuple[int]]
    payload: bytes

    def __init__(
        self,
        seq_number: int,
        ack_number: int,
        rwnd: int,
        upl: bool,
        dwl: bool,
        ack: bool,
        syn: bool,
        fin: bool,
        block_edges: list[tuple[int]],
        data: bytes,
    ):
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.payload = data
        self.rwnd = rwnd
        self.upl = upl
        self.dwl = dwl
        self.ack = ack
        self.syn = syn
        self.fin = fin
        self.block_edges = block_edges

    def encode(self) -> bytes:
        data: bytes = b""

        data += pack(
            "!II",
            self.seq_number,
            self.ack_number,
        )

        data += pack("!HBB", self.rwnd, self.upl, self.dwl)

        data += pack("!BBBB", self.ack, self.syn, self.fin, len(self.block_edges))

        for edges in self.block_edges:
            data += pack("!II", edges[LEFT_EDGE], edges[RIGHT_EDGE])

        data += self.payload

        return data

    def length(self) -> int:
        return len(self.encode())

    @staticmethod
    def decode(data: bytes) -> "SACKPacket":
        seq_number: int
        ack_number: int
        rwnd: int
        upl: bool
        dwl: bool
        ack: bool
        syn: bool
        fin: bool
        blocks: int
        payload: bytes
        block_edges: list[tuple[int]] = list()

        seq_number, ack_number = unpack("!II", data[:8:])

        rwnd, upl, dwl = unpack("!HBB", data[8:12:])

        ack, syn, fin, blocks = unpack("!BBBB", data[12:16:])

        for i in range(blocks):
            block_edges.append(unpack("!II", data[16 + 8 * i : 24 + 8 * i :]))

        header_length: int = HEADER_MIN_LENGTH_BYTES + blocks * BOTH_EDGE_SIZES
        payload: bytes = data[header_length::]

        return SACKPacket(
            seq_number,
            ack_number,
            rwnd,
            upl,
            dwl,
            ack,
            syn,
            fin,
            block_edges,
            payload,
        )

    def debug(self):
        print(f"seq: {self.seq_number}")
        print(f"ack: {self.ack_number}")
        print(f"rwnd: {self.rwnd}")
        print(f"upl: {self.upl}")
        print(f"dwl: {self.dwl}")
        print(f"ack: {self.ack}")
        print(f"syn: {self.syn}")
        print(f"fin: {self.fin}")
        print(f"blocks: {self.block_edges}")
        print(f"payload: {self.payload}")
