from struct import pack, unpack

HEADER_MIN_LENGTH_BYTES: int = 16
BOTH_EDGE_SIZES: int = 8
LEFT_EDGE: int = 0
RIGHT_EDGE: int = 1


class SACKPacket:
    """
    +---------------------+---------------------+------------+
    |                       Sequence Number 4B               |
    +---------------------+---------------------+------------+
    |                    Acknowledgment Number 4B            |
    +---------------------+---------------------+------------+
    |    Receive window 2B     |    UPL: 1B    |   DWL: 1B   |
    +---------------------+---------------------+------------+
    |   ACK 1B    |     Blocks 1B    |   SYN 1B   |  FIN 1B  |
    +---------------------+---------------------+------------+
    |                    Left Edge of Block 1 4B             |
    +---------------------+---------------------+------------+
    |                    Right Edge of Block 1 4B            |
    +---------------------+---------------------+------------+
    |                    ........................            |
    +---------------------+---------------------+------------+
    |                    Left Edge of Block N 4B             |
    +---------------------+---------------------+------------+
    |                    Right Edge of Block N 4B            |
    +---------------------+---------------------+------------+
    |                                                        |
    |                       Data 512B                        |
    |                                                        |
    +---------------------+---------------------+------------+

    """

    seq_number: int
    ack_number: int
    rwnd: int
    upl: bool
    dwl: bool
    ack: bool
    blocks: int
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
        self.blocks = len(block_edges)

    def encode(self) -> bytes:
        data: bytes = b""

        data += pack(
            "!II",
            self.seq_number,
            self.ack_number,
        )

        data += pack("!HBB", self.rwnd, self.upl, self.dwl)

        data += pack("!BBBB", self.ack, self.blocks, self.syn, self.fin)

        for edges in self.block_edges:
            data += pack("!II", edges[LEFT_EDGE], edges[RIGHT_EDGE])

        data += self.payload

        return data

    @staticmethod
    def decode(data: bytes) -> "SACKPacket":
        seq_number: int
        ack_number: int
        rwnd: int
        upl: bool
        dwl: bool
        ack: bool
        blocks: int
        syn: bool
        fin: bool
        payload: bytes
        block_edges: list[tuple[int]] = list()

        seq_number, ack_number = unpack("!II", data[:8:])

        rwnd, upl, dwl = unpack("!HBB", data[8:12:])

        ack, blocks, syn, fin = unpack("!BBBB", data[12:16:])

        for i in range(blocks):
            block_edges.append(unpack("!II", data[16 + 8 * i : 24 + 8 * i :]))

        header_length: int = HEADER_MIN_LENGTH_BYTES + blocks * BOTH_EDGE_SIZES
        payload: bytes = data[header_length::]

        return SACKPacket(
            seq_number, ack_number, rwnd, upl, dwl, ack, syn, fin, block_edges, payload
        )
