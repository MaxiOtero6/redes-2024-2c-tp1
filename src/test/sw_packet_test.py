import unittest
from lib.sw_packet import SWPacket


class SWPacketTest(unittest.TestCase):
    def test_encode_sw_packet(self):
        seq_number: int = 1
        ack_number: int = 0
        syn: bool = False
        fin: bool = False
        ack: bool = False
        payload: bytes = b"\xFF\xEF"
        packet: SWPacket = SWPacket(
            seq_number, ack_number, syn, fin, ack, payload)

        expected_bytes: bytes = b"\x01\x00\x00\x00\x00\x00\x00\x00\xff\xef"

        res: bytes = packet.encode()

        self.assertEqual(expected_bytes, res)

    def test_decode_sw_packet(self):
        expected_seq_number: int = 1
        expected_ack_number: int = 0
        expected_syn: bool = False
        expected_fin: bool = False
        expected_ack: bool = False
        expected_payload: bytes = b"\xFF\xEF"
        data: bytes = b"\x01\x00\x00\x00\x00\x00\x00\x00\xff\xef"

        res: SWPacket = SWPacket.decode(data)

        self.assertEqual(expected_seq_number, res.seq_number)
        self.assertEqual(expected_ack_number, res.ack_number)
        self.assertEqual(expected_syn, res.syn)
        self.assertEqual(expected_fin, res.fin)
        self.assertEqual(expected_ack, res.ack)
        self.assertEqual(expected_payload, res.payload)
