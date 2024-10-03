from collections import deque
import random
from lib.packets.sack_packet import SACKPacket
from lib.client.download_config import DownloadConfig
from lib.arguments.constants import (
    MAX_PACKET_SIZE_SACK,
    MAX_PAYLOAD_SIZE,
    MAX_TIMEOUT_PER_PACKET,
    TIMEOUT,
)
import socket

SEQUENCE_NUMBER_LIMIT = 2**32
RWND = MAX_PAYLOAD_SIZE * 10


class DownloadClientSACK:
    def __init__(self, config: DownloadConfig):
        self.__config = config
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = (self.__config.HOST, self.__config.PORT)
        self.__last_packet_created = None
        self.__last_packet_received = None
        self.__timeout_count: int = 0

        # Reciever
        self.__in_order_packets = deque()  # [packets]
        self.__out_of_order_packets = {}  # {seq_number: packets}
        self.__received_blocks_edges = []  # [(start, end)]
        self.__last_ordered_packet_received = None

    def __start_of_next_seq(self, packet):
        """Get the start of the next sequence number."""
        return (packet.seq_number + packet.length()) % SEQUENCE_NUMBER_LIMIT

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_created is None:
            return 0
        return self.__start_of_next_seq(self.__last_packet_created)

    def __next_expected_seq_number(self):
        """Get the next expected sequence number."""
        if self.__last_ordered_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_ordered_packet_received)

    def __last_packet_is_ordered(self):
        """Check if the last packet received is in order."""
        if self.__last_ordered_packet_received is None:
            return True

        return (
            self.__last_packet_received.seq_number == self.__next_expected_seq_number()
        )

    # def __packet_was_acked(self, packet):
    #     """Check if the packet was acked."""
    #     ack_number = self.__last_packet_received.ack_number
    #     end_of_packet = self.__start_of_next_seq(packet)

    #     diference = abs(end_of_packet - ack_number)
    #     if diference > SEQUENCE_NUMBER_LIMIT / 2:
    #         ack_number += SEQUENCE_NUMBER_LIMIT

    #     return end_of_packet <= ack_number

    # def __new_ack_received(self):
    #     """Check if the received packet acked the first unacked packet."""
    #     if not self.__unacked_packets:
    #         return False

    #     first_packet = self.__unacked_packets[0][0]

    #     return self.__packet_was_acked(first_packet)

    # def __sack_received(self):
    #     return (
    #         self.__last_packet_received.ack and self.__last_packet_received.block_edges
    #     )

    def __reorder_blocks(self):
        while self.__next_expected_seq_number() in self.__out_of_order_packets:
            self.__last_ordered_packet_received = self.__out_of_order_packets.pop(
                self.__next_expected_seq_number()
            )
            self.__in_order_packets.append(self.__last_ordered_packet_received)

            _, first_block_end = self.__received_blocks_edges[0]

            if first_block_end == self.__next_expected_seq_number():
                self.__received_blocks_edges.pop(0)
            else:
                self.__received_blocks_edges[0] = (
                    self.__next_expected_seq_number(),
                    first_block_end,
                )

    def __add_in_order_packet(self):
        """Add the in order packet to the queue."""
        self.__last_ordered_packet_received = self.__last_packet_received
        self.__in_order_packets.append(self.__last_ordered_packet_received)

        # Try to reorder the buffered packets
        self.__reorder_blocks()

    def __add_out_of_order_packet(self):
        """Add the out of order packet to the queue."""
        start = self.__last_packet_received.seq_number
        end = start + self.__last_packet_received.length()

        self.__out_of_order_packets[start] = self.__last_packet_received

        for block_index in range(len(self.__received_blocks_edges)):
            block_start, block_end = self.__received_blocks_edges[block_index]

            if end == block_start:
                self.__received_blocks_edges[block_index] = (start, block_end)
                return

            if start == block_end:
                self.__received_blocks_edges[block_index] = (block_start, end)

                if block_index + 1 < len(self.__received_blocks_edges):
                    next_block_start, _ = self.__received_blocks_edges[block_index + 1]
                    if next_block_start == end:
                        _, next_block_end = self.__received_blocks_edges.pop(
                            block_index + 1
                        )
                        self.__received_blocks_edges[block_index] = (
                            block_start,
                            next_block_end,
                        )
                return

            if end < block_start:
                self.__received_blocks_edges.insert(block_index, (start, end))
                return

        if (start, end) not in self.__received_blocks_edges:
            self.__received_blocks_edges.append((start, end))

    def __end_of_last_ordered_packet(self):
        """Get the last received sequence number."""
        if self.__last_ordered_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_ordered_packet_received)

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload):
        packet = SACKPacket(
            self.__next_seq_number(),
            self.__end_of_last_ordered_packet(),
            RWND,
            upl,
            dwl,
            ack,
            syn,
            fin,
            self.__received_blocks_edges,
            payload,
        )

        self.__last_packet_created = packet
        return packet

    def __get_packet(self):
        """Get the next packet from the queue."""
        try:
            self.__socket.settimeout(TIMEOUT)
            data = self.__socket.recv(MAX_PACKET_SIZE_SACK)
            packet = SACKPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        # socket timeout
        except (socket.timeout, Exception):
            self.__timeout_count += 1
            print(f"Timeout number: {self.__timeout_count}")

            if self.__timeout_count >= MAX_TIMEOUT_PER_PACKET:
                raise BrokenPipeError(
                    f"Max timeouts reached, is client {self.__address} alive?. Closing connection"  # noqa
                )

            self.__send_packet(self.__last_packet_created)
            self.__get_packet()

    def __send_packet(self, packet: SACKPacket):
        """Send a packet to the client."""
        self.__socket.settimeout(0)
        self.__socket.sendto(packet.encode(), self.__address)

        self.__last_packet_created = packet

    def __send_ack(self):
        """Send an acknowledgment to the client."""
        ack_packet = self.__create_new_packet(
            self.__last_ordered_packet_received.syn,
            self.__last_ordered_packet_received.fin,
            True,
            self.__last_ordered_packet_received.upl,
            self.__last_ordered_packet_received.dwl,
            b"",
        )

        self.__send_packet(ack_packet)

    def __send_sack(self):
        """Send a SACK packet to the client."""
        sack_packet = self.__create_new_packet(
            False,
            False,
            True,
            self.__last_packet_received.upl,
            self.__last_packet_received.dwl,
            b"",
        )
        self.__send_packet(sack_packet)

    # def __send_fin(self):
    #     """Send the final FIN packet."""
    #     fin_packet = self.__create_new_packet(
    #         False,
    #         True,
    #         False,
    #         self.__last_packet_received.upl,
    #         self.__last_packet_received.dwl,
    #         b"",
    #     )
    #     self.__send_packet(fin_packet)
    #     self.__wait_for_ack()

    # def __wait_for_ack(self):
    #     while True:
    #         # TODO: follow a cumulative ack policy
    #         self.__get_packet()

    #         if self.__sack_received():
    #             self.__handle_sack()

    #         if self.__new_ack_received():
    #             break

    #     # At least one packet was acked, remove all acked packets from the unacked packets # noqa
    #     while self.__unacked_packets:
    #         packet, time = self.__unacked_packets.popleft()

    #         if not self.__packet_was_acked(packet):
    #             self.__unacked_packets.appendleft((packet, time))
    #             break

    #         self.__in_flight_bytes -= packet.length()

    def __last_packet_sent_was_ack(self):
        """Check if the last packet sent was an acknowledgment."""
        return (
            self.__last_packet_received.ack
            and self.__start_of_next_seq(self.__last_packet_created)
            == self.__last_packet_received.ack_number
        )

    def __wait_for_ack(self):  # TODO: Acomodar esto
        self.__get_packet()

        while not self.__last_packet_sent_was_ack():
            self.__send_packet(self.__last_packet_created)
            self.__get_packet()

    def __wait_for_data(self):
        """Wait for data from the client."""
        while True:
            print("Waiting for data")

            self.__get_packet()

            if self.__last_packet_received.dwl and self.__last_packet_is_ordered():
                break

            if (
                self.__last_packet_received.seq_number
                >= self.__next_expected_seq_number()
            ):
                self.__add_out_of_order_packet()
                self.__send_sack()

        # The last packet received is ordered
        self.__add_in_order_packet()

    def __send_comm_start(self):
        start_package = self.__create_new_packet(
            True,
            False,
            False,
            False,
            True,
            b"",
        )

        self.__send_packet(start_package)
        print("Download start packet sent")

        self.__wait_for_ack()
        print("Start ack received")

    def __send_file_name_request(self):
        file_name_package = self.__create_new_packet(
            True,
            False,
            False,
            False,
            True,
            self.__config.FILE_NAME.encode(),
        )
        self.__send_packet(file_name_package)
        print(f"File name request sent: {self.__config.FILE_NAME}")

        self.__wait_for_ack()
        print("File name ack received")

        self.__add_in_order_packet()

        file_path = f"{self.__config.DESTINATION_PATH}/{self.__config.FILE_NAME}"

        # Create an empty file or clear the existing file
        with open(file_path, "wb") as _:
            pass

    def __save_file_data(self, file_path):
        """Save file data received from the client."""
        with open(file_path, "ab") as file:
            while self.__in_order_packets:
                packet = self.__in_order_packets.popleft()
                file.write(packet.payload)

    def __recieve_file_data(self):
        print("Receiving file data")
        file_path = f"{self.__config.DESTINATION_PATH}/{self.__config.FILE_NAME}"

        # To create / overwrite the file
        with open(file_path, "wb") as _:
            pass

        # self.__in_order_packets.clear()
        # self.__wait_for_data()

        while not self.__last_ordered_packet_received.fin:
            self.__save_file_data(file_path)
            self.__send_ack()
            self.__wait_for_data()

        self.__send_ack()

    def run(self):
        try:
            print("Starting file download")
            self.__send_comm_start()
            self.__send_file_name_request()
            self.__recieve_file_data()
            print(f"File received: {self.__config.FILE_NAME}")
            self.__socket.close()

        except BrokenPipeError as e:
            print(str(e))
            self.__socket.close()
            exit()
