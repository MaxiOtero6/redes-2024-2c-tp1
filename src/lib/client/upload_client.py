import os
import time
from lib.packets.sw_packet import SWPacket
from lib.client.upload_config import UploadConfig
from lib.arguments.constants import MAX_PACKET_SIZE_SW, MAX_PAYLOAD_SIZE
import socket


class UploadClient:
    def __init__(self, config: UploadConfig):
        self.__config = config

        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sequence_number = 0

    def __swap_sequence_number(self):
        self.__sequence_number = 1 if self.__sequence_number == 0 else 0

    def __wait_for_ack(self, previous_packet: SWPacket):
        (response, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SW)
        response_packet = SWPacket.decode(response)
        while (
            not response_packet.ack
            or response_packet.ack_number != self.__sequence_number
        ):
            self.__skt.sendto(
                previous_packet.encode(), (self.__config.HOST, self.__config.PORT)
            )
            response = self.__skt.recv(MAX_PACKET_SIZE_SW)
            response_packet = SWPacket.decode(response)

    def __send_comm_start(self):
        start_packet = SWPacket(
            self.__sequence_number,
            1 if self.__sequence_number == 0 else 0,
            True,
            False,
            False,
            True,
            False,
            b"",
        )
        self.__skt.sendto(
            start_packet.encode(), (self.__config.HOST, self.__config.PORT)
        )
        print("Upload communication start packet sent")
        self.__wait_for_ack(start_packet)
        print("Start ack received")
        self.__swap_sequence_number()

    def __send_file_name(self):
        file_name_package = SWPacket(
            self.__sequence_number,
            1 if self.__sequence_number == 0 else 0,
            False,
            False,
            False,
            True,
            False,
            self.__config.FILE_NAME.encode(),
        )
        self.__skt.sendto(
            file_name_package.encode(), (self.__config.HOST, self.__config.PORT)
        )
        print(f"File name sent: {self.__config.FILE_NAME}")
        self.__wait_for_ack(file_name_package)
        print("File name ack received")
        self.__swap_sequence_number()

    def __send_file_data(self):
        file_length = os.path.getsize(self.__config.SOURCE_PATH)

        with open(self.__config.SOURCE_PATH, "rb") as file:
            data_sent = 0
            data = file.read(MAX_PAYLOAD_SIZE)
            while len(data) != 0:
                packet = SWPacket(
                    self.__sequence_number,
                    1 if self.__sequence_number == 0 else 0,
                    False,
                    False,
                    False,
                    True,
                    False,
                    data,
                )
                self.__skt.sendto(
                    packet.encode(), (self.__config.HOST, self.__config.PORT)
                )
                data_sent += len(data)
                print(
                    f"Sent packet of size {round(data_sent / file_length * 100, 2)}% {data_sent}/{file_length}"
                )
                self.__wait_for_ack(packet)
                print("Ack received for packet")

                # sleep for a second
                time.sleep(0.1)

                self.__swap_sequence_number()
                data = file.read(MAX_PAYLOAD_SIZE)

    def __send_comm_fin(self):
        fin_packet = SWPacket(
            self.__sequence_number,
            1 if self.__sequence_number == 0 else 0,
            False,
            True,
            False,
            True,
            False,
            b"",
        )
        self.__skt.sendto(fin_packet.encode(), (self.__config.HOST, self.__config.PORT))
        print("Fin packet sent")

    def run(self):
        print("Starting file upload")
        self.__send_comm_start()
        self.__send_file_name()
        self.__send_file_data()
        self.__send_comm_fin()
        self.__skt.close()
        print("File sent")
