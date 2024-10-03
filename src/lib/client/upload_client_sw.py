import os
from lib.packets.sw_packet import SWPacket
from lib.client.upload_config import UploadConfig
from lib.arguments.constants import (
    MAX_PACKET_SIZE_SW,
    MAX_PAYLOAD_SIZE,
    MAX_TIMEOUT_COUNT,
)
import socket


class UploadClientSW:
    def __init__(self, config: UploadConfig):
        self.__config = config
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = (self.__config.HOST, self.__config.PORT)
        self.__last_packet_sent = None
        self.__last_packet_received = None
        self.__timeout_count: int = 0
        self.__timeout = self.__config.TIMEOUT / 1000

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_sent is None:
            return 0
        return 1 - self.__last_packet_sent.seq_number

    def __last_received_seq_number(self):
        """Get the last received sequence number."""
        if self.__last_packet_received is None:
            return 0
        return self.__last_packet_received.seq_number

    def __last_packet_sent_was_ack(self):
        """Check if the last packet sent was an acknowledgment."""
        return (
            self.__last_packet_received.ack
            and self.__last_packet_sent.seq_number
            == self.__last_packet_received.ack_number
        )

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload):
        return SWPacket(
            self.__next_seq_number(),
            self.__last_received_seq_number(),
            syn,
            fin,
            ack,
            upl,
            dwl,
            payload,
        )

    def __get_packet(self):
        """Get the next packet from the queue."""
        self.__socket.settimeout(self.__timeout)

        try:
            data = self.__socket.recv(MAX_PACKET_SIZE_SW)
            packet = SWPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        except socket.timeout:
            self.__timeout_count += 1
            if self.__timeout_count >= MAX_TIMEOUT_COUNT:
                raise BrokenPipeError(
                    "Max timeouts reached. Closing connection"  # noqa
                )

            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __send_packet(self, packet):
        """Send a packet to the client."""
        self.__socket.sendto(packet.encode(), self.__address)
        self.__last_packet_sent = packet

    def __wait_for_ack(self):
        self.__get_packet()

        while not self.__last_packet_sent_was_ack():
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

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
        file_path = self.__config.SOURCE_PATH
        file_length = os.path.getsize(file_path)

        with open(file_path, "rb") as file:
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
                    f"Sent packet of size {round(data_sent / file_length * 100, 2)}% {data_sent}/{file_length}"  # noqa
                )
                self.__wait_for_ack()
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
        except BrokenPipeError as e:
            print(str(e))
            self.__socket.close()
            exit()
        except FileNotFoundError as e:
            print("Error: ", e)
            print(
                "File not found or path is incorrect, please check the path and try again"
            )
            print("Closing connection")
            self.__skt.close()
