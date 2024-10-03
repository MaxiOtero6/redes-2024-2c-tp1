import unittest
from lib.client.download_client_sack import SEQUENCE_NUMBER_LIMIT
from lib.packets.sack_packet import SACKPacket


class SACKPacketTest(unittest.TestCase):
    def test_decode_sack_packet(self):
        expected_seq_number: int = 0
        expected_ack_number: int = 0
        expected_rwnd: int = 0
        expected_upl: bool = True
        expected_dwl: bool = False
        expected_ack: bool = True
        expected_syn: bool = False
        expected_fin: bool = True
        # blocks: int = 2
        expected_block_edges: list[tuple[int]] = [(1, 0), (0, 1)]
        expected_payload: bytes = b"\xFF"

        data: bytes = (
            b"\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00"
            + b"\x00\x00"
            + b"\x01"
            + b"\x00"
            + b"\x01"
            + b"\x00"
            + b"\x01"
            + b"\x02"
            + b"\x00\x00\x00\x01\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x01"
            + b"\xFF"
        )

        res: SACKPacket = SACKPacket.decode(data)

        self.assertEqual(expected_seq_number, res.seq_number)
        self.assertEqual(expected_ack_number, res.ack_number)
        self.assertEqual(expected_rwnd, res.rwnd)
        self.assertEqual(expected_upl, res.upl)
        self.assertEqual(expected_dwl, res.dwl)
        self.assertEqual(expected_ack, res.ack)
        self.assertEqual(expected_syn, res.syn)
        self.assertEqual(expected_fin, res.fin)
        self.assertEqual(expected_block_edges, res.block_edges)
        self.assertEqual(expected_payload, res.payload)

    def test_encode_sack_packet(self):
        seq_number: int = 0
        ack_number: int = 0
        rwnd: int = 0
        upl: bool = True
        dwl: bool = False
        ack: bool = True
        syn: bool = False
        fin: bool = True
        # blocks: int = 2
        block_edges: list[tuple[int]] = [(1, 0), (0, 1)]
        payload: bytes = b"\xFF"

        packet: SACKPacket = SACKPacket(
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

        expected_bytes: bytes = (
            b"\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00"
            + b"\x00\x00"
            + b"\x01"
            + b"\x00"
            + b"\x01"
            + b"\x00"
            + b"\x01"
            + b"\x02"
            + b"\x00\x00\x00\x01\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x01"
            + b"\xFF"
        )

        res: bytes = packet.encode()

        self.assertEqual(expected_bytes, res)

    def test_max_seq(self):

        # ack_number = self.__last_packet_received.ack_number
        # end_of_packet = self.__start_of_next_seq(packet)

        ack_number = 10
        end_of_packet = 4294967290

        diference = abs(end_of_packet - ack_number)
        if diference > SEQUENCE_NUMBER_LIMIT / 2:
            if ack_number < end_of_packet:
                ack_number += SEQUENCE_NUMBER_LIMIT
            else:
                end_of_packet += SEQUENCE_NUMBER_LIMIT

        self.assertEqual(True, end_of_packet <= ack_number)

    def test_max_seq2(self):

        # ack_number = self.__last_packet_received.ack_number
        # end_of_packet = self.__start_of_next_seq(packet)

        ack_number = 4294967280
        end_of_packet = 4294967290

        diference = abs(end_of_packet - ack_number)
        if diference > SEQUENCE_NUMBER_LIMIT / 2:
            if ack_number < end_of_packet:
                ack_number += SEQUENCE_NUMBER_LIMIT
            else:
                end_of_packet += SEQUENCE_NUMBER_LIMIT

        self.assertEqual(False, end_of_packet <= ack_number)

    def test_max_seq3(self):

        # ack_number = self.__last_packet_received.ack_number
        # end_of_packet = self.__start_of_next_seq(packet)

        ack_number = 10
        end_of_packet = SEQUENCE_NUMBER_LIMIT

        diference = abs(end_of_packet - ack_number)
        if diference > SEQUENCE_NUMBER_LIMIT / 2:
            if ack_number < end_of_packet:
                ack_number += SEQUENCE_NUMBER_LIMIT
            else:
                end_of_packet += SEQUENCE_NUMBER_LIMIT

        self.assertEqual(True, end_of_packet <= ack_number)

    def test_max_seq4(self):

        # ack_number = self.__last_packet_received.ack_number
        # end_of_packet = self.__start_of_next_seq(packet)

        ack_number = (SEQUENCE_NUMBER_LIMIT / 2) + 1
        end_of_packet = SEQUENCE_NUMBER_LIMIT

        diference = abs(end_of_packet - ack_number)
        if diference > SEQUENCE_NUMBER_LIMIT / 2:
            if ack_number < end_of_packet:
                ack_number += SEQUENCE_NUMBER_LIMIT
            else:
                end_of_packet += SEQUENCE_NUMBER_LIMIT

        self.assertEqual(False, end_of_packet <= ack_number)

    def test_max_seq5(self):

        # ack_number = self.__last_packet_received.ack_number
        # end_of_packet = self.__start_of_next_seq(packet)

        ack_number = SEQUENCE_NUMBER_LIMIT
        end_of_packet = 10

        diference = abs(end_of_packet - ack_number)
        if diference > SEQUENCE_NUMBER_LIMIT / 2:
            if ack_number < end_of_packet:
                ack_number += SEQUENCE_NUMBER_LIMIT
            else:
                end_of_packet += SEQUENCE_NUMBER_LIMIT

        self.assertEqual(False, end_of_packet <= ack_number)
