import os
from collections import deque, stack
import time
from lib.packets.sack_packet import SACKPacket
from lib.packets.sw_packet import SWPacket
from lib.client.upload_config import UploadConfig
from lib.arguments.constants import (
    MAX_PACKET_SIZE_SW,
    MAX_PAYLOAD_SIZE,
    MAX_TIMEOUT_PER_PACKET,
    TIMEOUT,
)
import socket

SEQUENCE_NUMBER_LIMIT = 2**32
WINDOW_SIZE = 512


class UploadClient:
    def __init__(self, config: UploadConfig):
        self.__config = config
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = (self.__config.HOST, self.__config.PORT)
        self.__timeout_count: int = 0

        # Sender
        self.__unacked_packets = deque()  # list of unacked packets (packet, time)
        self.__last_packet_sent = None
        self.__last_packet_received = None

    def __start_of_next_seq(self, packet):
        """Get the start of the next sequence number."""
        return (packet.seq_number + packet.length()) % SEQUENCE_NUMBER_LIMIT

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_sent is None:
            return 0
        return self.__start_of_next_seq(self.__last_packet_sent)

    def __last_recived_seq_number(self):
        """Get the last received sequence number."""
        if self.__last_Fpacket_received is None:
            return 0
        return self.__last_packet_received.seq_number

    def __time_to_first_unacked_packed_timeout(self):
        """Get the time to the first unacked packet timeout."""
        if len(self.__unacked_packets) == 0:
            return 0

        elapsed_time = time.time() - self.__unacked_packets[0][1]

        if elapsed_time > TIMEOUT:
            return 0

        return TIMEOUT - elapsed_time

    # def __first_unacked_packed_is_timeout(self):
    #     """Check if the first unacked packet is timeout."""
    #     return self.__time_to_first_unacked_packed_timeout() == 0

    def __in_order_ack_received(self):
        """Check if the received packet acked the first unacked packet."""
        if not self.__unacked_packets:
            return False

        first_packet = self.__unacked_packets[0][0].ack

        return (
            self.__last_packet_received.ack
            and first_packet.seq_number == self.__last_packet_received.ack_number
        )

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload):
        return SACKPacket(
            self.__next_seq_number(),
            self.__last_recived_seq_number(),
            syn,
            fin,
            ack,
            upl,
            dwl,
            payload,
        )

    def __resend_window(self):
        """Resend all packets in the window."""

        # Maybe shrink the window size here

        while self.__unacked_packets:
            packet, _ = self.__unacked_packets.popleft()
            self.__send_packet(packet)

    def __get_packet(self):
        """Get the next packet from the queue."""
        self.__skt.settimeout(self.__time_to_first_unacked_packed_timeout())

        try:
            data = self.__skt.recv(MAX_PACKET_SIZE_SW)
            packet = SWPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        # Cuando el tiempo de espera es 0 y no había nada en el socket o se excede el tiempo de espera
        except (socket.timeout, BlockingIOError):
            self.__timeout_count += 1
            print(f"Timeout!!: {self.__timeout_count}")

            if self.__timeout_count >= MAX_TIMEOUT_PER_PACKET:
                raise BrokenPipeError(
                    "Max timeouts reached, is client alive?. Closing connection"
                )

            self.__resend_window()
            self.__get_packet()

    def __send_packet(self, packet):
        """Send a packet to the client."""
        self.__skt.settimeout(TIMEOUT)
        self.__skt.sendto(packet.encode(), self.__address)
        self.__last_packet_sent = packet
        self.__unacked_packets.append((packet, time.time()))

    def __out_of_order_ack_received(self):
        """
        Handle the case when an out of order ack is received.
        If it has a block edge, check if there is an unacked packet waiting for that block edge,
        if so, remove it from the unacked packets.
        """

        # Use an stack to store the queue order
        unacked_packets = stack()

        for start, end in self.__last_packet_received.block_edges:
            while self.__unacked_packets:
                packet, time = self.__unacked_packets.popleft()

                if packet.seq_number < start:
                    # packet not in any block edge
                    unacked_packets.append((packet, time))

                elif self.__start_of_next_seq(packet) > end:
                    # packet not in this block edge, add it back and try the next one
                    self.__unacked_packets.appendleft((packet, time))
                    break

                # packet was acked, no need to resend

        for packet, time in self.__unacked_packets:
            self.__unacked_packets.appendleft((packet, time))

    def __wait_for_ack(self):
        self.__get_packet()

        while not self.__in_order_ack_received():
            self.__out_of_order_ack_received()
            self.__get_packet()
            # TODO: follow a cumulative ack policy

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
        file_length = os.path.getsize(self.__config.SOURCE_PATH)

        # falta que mande toda la ventana

        with open(self.__config.SOURCE_PATH, "rb") as file:
            data_sent = 0
            data = file.read(MAX_PAYLOAD_SIZE)
            while len(data) != 0:
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
                print(
                    f"Sent packet of size {round(data_sent / file_length * 100, 2)}% {data_sent}/{file_length}"
                )
                self.__wait_for_ack()
                print("Ack received for packet")

                # sleep for a second
                time.sleep(0.1)

                data = file.read(MAX_PAYLOAD_SIZE)

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
        print("Fin packet sent")
        self.__wait_for_ack()
        print("Fin ack received")

    def run(self):
        try:
            print("Starting file upload")
            self.__send_comm_start()
            self.__send_file_name()
            self.__send_file_data()
            self.__send_comm_fin()
            print(f"File sent: {self.__config.FILE_NAME}")
            self.__skt.close()

        except BrokenPipeError as e:
            print(str(e))
            self.__skt.close()
            exit()
