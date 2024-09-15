import unittest
from lib.sack_packet import SACKPacket


class SACKPacketTest(unittest.TestCase):
    def test_encode_sack_packet(self):
        seq_number: int = 414243
        ack_number: int = 434241
        # header_length: int = 32
        rwnd: int = 15
        ack: bool = True
        # blocks: int = 2
        syn: bool = False
        fin: bool = False
        block_edges: list[tuple[int]] = [(1, 0), (25, 414243)]
        payload: bytes = b"\xFF\xEF"

        packet: SACKPacket = SACKPacket(
            seq_number, ack_number, rwnd,
            ack, syn, fin, block_edges, payload
        )

        expected_bytes: bytes = b"\x00\x06R#\x00\x06\xa0A\x00 \x00\x0f\x01\x02\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x19\x00\x06R#\xff\xef"

        res: bytes = packet.encode()

        self.assertEqual(expected_bytes, res)

    def test_decode_sack_packet(self):
        expected_seq_number: int = 414243
        expected_ack_number: int = 434241
        expected_header_length: int = 32
        expected_rwnd: int = 15
        expected_ack: bool = True
        expected_blocks: int = 2
        expected_syn: bool = False
        expected_fin: bool = False
        expected_block_edges: list[tuple[int]] = [(1, 0), (25, 414243)]
        expected_payload: bytes = b"\xFF\xEF"

        data: bytes = b"\x00\x06R#\x00\x06\xa0A\x00 \x00\x0f\x01\x02\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x19\x00\x06R#\xff\xef"

        res: SACKPacket = SACKPacket.decode(data)

        self.assertEqual(expected_seq_number, res.seq_number)
        self.assertEqual(expected_ack_number, res.ack_number)
        self.assertEqual(expected_header_length, res.header_length)
        self.assertEqual(expected_rwnd, res.rwnd)
        self.assertEqual(expected_ack, res.ack)
        self.assertEqual(expected_blocks, res.blocks)
        self.assertEqual(expected_syn, res.syn)
        self.assertEqual(expected_fin, res.fin)
        self.assertEqual(expected_block_edges, res.block_edges)
        self.assertEqual(expected_payload, res.payload)
