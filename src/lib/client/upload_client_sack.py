import os
from collections import deque
import time
from lib.packets.sack_packet import SACKPacket
from lib.client.upload_config import UploadConfig
from lib.arguments.constants import (
    MAX_PACKET_SIZE_SACK,
    MAX_PAYLOAD_SIZE,
    MAX_TIMEOUT_COUNT,
)
import socket

SEQUENCE_NUMBER_LIMIT = 2**32
WINDOW_SIZE = MAX_PAYLOAD_SIZE * 2


class UploadClientSACK:
    def __init__(self, config: UploadConfig):
        self.__config = config
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = (self.__config.HOST, self.__config.PORT)

        # Sender
        self.__unacked_packets = (
            deque()
        )  # list of unacked packets (packet, time) # noqa
        self.__last_packet_received = None
        self.__in_flight_bytes = 0
        self.__last_packet_created = None
        self.__timeout_count = 0
        self.__timeout = self.__config.TIMEOUT / 1000

    def __start_of_next_seq(self, packet):
        """Get the start of the next sequence number."""
        return (packet.seq_number + packet.length()) % SEQUENCE_NUMBER_LIMIT

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_created is None:
            return 0
        return self.__start_of_next_seq(self.__last_packet_created)

    def __last_received_seq_number(self):
        """Get the last received sequence number."""
        if self.__last_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_packet_received)

    def __time_to_first_unacked_packed_timeout(self):
        """Get the time to the first unacked packet timeout."""
        if len(self.__unacked_packets) == 0:
            return 0

        elapsed_time = time.time() - self.__unacked_packets[0][1]

        if elapsed_time > self.__timeout:
            return 0

        return self.__timeout - elapsed_time

    def __packet_was_acked(self, packet):
        """Check if the packet was acked."""
        ack_number = self.__last_packet_received.ack_number
        end_of_packet = self.__start_of_next_seq(packet)

        diference = abs(end_of_packet - ack_number)
        if diference > SEQUENCE_NUMBER_LIMIT / 2:
            if ack_number < end_of_packet:
                ack_number += SEQUENCE_NUMBER_LIMIT
            else:
                end_of_packet += SEQUENCE_NUMBER_LIMIT

        return end_of_packet <= ack_number

    def __new_ack_received(self):
        """Check if the received packet acked the first unacked packet."""
        if not self.__unacked_packets:
            return False

        first_packet = self.__unacked_packets[0][0]

        return self.__packet_was_acked(first_packet)

    def __sack_received(self):
        return (
            self.__last_packet_received.ack and self.__last_packet_received.block_edges
        )

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload):
        packet = SACKPacket(
            self.__next_seq_number(),
            self.__last_received_seq_number(),
            WINDOW_SIZE,
            upl,
            dwl,
            ack,
            syn,
            fin,
            [],
            payload,
        )

        self.__last_packet_created = packet
        return packet

    def __resend_window(self):
        """Resend all packets in the window."""

        # Maybe shrink the window size here
        size: int = len(self.__unacked_packets)
        for _ in range(size):
            packet, _ = self.__unacked_packets.popleft()
            self.__in_flight_bytes -= packet.length()
            self.__send_packet(packet)

    def __get_packet(self):
        """Get the next packet from the queue."""
        self.__socket.settimeout(self.__time_to_first_unacked_packed_timeout())

        try:
            data = self.__socket.recv(MAX_PACKET_SIZE_SACK)
            packet = SACKPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        # Cuando el tiempo de espera es 0 y no había nada en el socket o se excede el tiempo de espera # noqa
        except (socket.timeout, BlockingIOError):
            self.__timeout_count += 1
            if self.__timeout_count >= MAX_TIMEOUT_COUNT:
                raise BrokenPipeError(
                    "Max timeouts reached. Closing connection"  # noqa
                )

            self.__resend_window()
            self.__get_packet()

    def __send_packet(self, packet: SACKPacket):
        """Send a packet to the client."""
        self.__socket.sendto(packet.encode(), self.__address)
        self.__unacked_packets.append((packet, time.time()))
        self.__in_flight_bytes += packet.length()

    def __handle_sack(self):
        """
        Handle the case when an out of order ack is received. # noqa
        If it has a block edge, check if there is an unacked packet waiting for that block edge, # noqa
        if so, remove it from the unacked packets. # noqa
        """

        # Use an stack to store the queue order
        unacked_packets = []

        for start, end in self.__last_packet_received.block_edges:
            while self.__unacked_packets:
                packet, time = self.__unacked_packets.popleft()

                if packet.seq_number < start:
                    # packet not in any block edge
                    unacked_packets.append((packet, time))
                    continue

                elif self.__start_of_next_seq(packet) > end:
                    # packet not in this block edge, add it back and try the next one # noqa
                    self.__unacked_packets.appendleft((packet, time))
                    break

                # packet was acked, no need to resend
                self.__in_flight_bytes -= packet.length()

        while unacked_packets:
            self.__unacked_packets.appendleft(unacked_packets.pop())

    def __wait_for_ack(self):
        while True:
            # TODO: follow a cumulative ack policy
            self.__get_packet()

            if self.__sack_received():
                self.__handle_sack()

            if self.__new_ack_received():
                break

        # At least one packet was acked, remove all acked packets from the unacked packets # noqa
        while self.__unacked_packets:
            packet, time = self.__unacked_packets.popleft()

            if not self.__packet_was_acked(packet):
                self.__unacked_packets.appendleft((packet, time))
                break

            self.__in_flight_bytes -= packet.length()

    def __send_comm_start(self):
        start_package = self.__create_new_packet(
            True,
            False,
            False,
            True,
            False,
            b"",
        )
        self.__send_packet(start_package)
        print("Download start packet sent")

        self.__wait_for_ack()
        print("Start ack received")

    def __send_file_name(self):
        file_name_package = self.__create_new_packet(
            True,
            False,
            False,
            True,
            False,
            self.__config.FILE_NAME.encode(),
        )
        self.__send_packet(file_name_package)
        print(f"File name request sent: {self.__config.FILE_NAME}")

        self.__wait_for_ack()
        print("File name ack received")

    def __send_file_data(self):
        """Send the file data to the server."""
        file_length = os.path.getsize(self.__config.SOURCE_PATH)

        with open(self.__config.SOURCE_PATH, "rb") as file:
            data_sent = 0
            data = file.read(MAX_PAYLOAD_SIZE)
            while len(data) > 0 or self.__unacked_packets:
                while (
                    len(data) > 0 and self.__in_flight_bytes < WINDOW_SIZE
                ):  # TODO: prevent to send more than the window size
                    packet = self.__create_new_packet(
                        False,
                        False,
                        False,
                        True,
                        False,
                        data,
                    )

                    self.__send_packet(packet)
                    data_sent += len(data)

                    print_sent_progress(data_sent, file_length)

                    data = file.read(MAX_PAYLOAD_SIZE)

                self.__wait_for_ack()

    def __send_comm_fin(self):
        fin_packet = self.__create_new_packet(
            False,
            True,
            False,
            True,
            False,
            b"",
        )
        self.__send_packet(fin_packet)
        print(f"Fin packet sent {fin_packet.seq_number}")
        self.__wait_for_ack()
        print("Fin ack received")

    def __check_file_in_fs(self):
        """Check if the file exists in the file system."""
        if not os.path.exists(self.__config.SOURCE_PATH):
            raise FileNotFoundError(f"File not found: {self.__config.SOURCE_PATH}")

    def run(self):
        try:
            self.__check_file_in_fs()
            print("Starting file upload")
            self.__send_comm_start()
            self.__send_file_name()
            self.__send_file_data()
            self.__send_comm_fin()
            print(f"File sent: {self.__config.FILE_NAME}")
            self.__socket.close()
        except FileNotFoundError as e:
            print("Error: ", e)
            print(
                "File not found or path is incorrect, please check the path and try again"
            )
            print("Closing connection")
            self.__socket.close()
        except BrokenPipeError as e:
            print(str(e))
            self.__socket.close()
            exit()


def print_sent_progress(data_sent, file_length):
    print(
        f"Sent packet of size {round(data_sent / file_length * 100, 2)}% {data_sent}/{file_length}"  # noqa
    )
