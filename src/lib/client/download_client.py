from lib.packets.sw_packet import SWPacket
from lib.client.download_config import DownloadConfig
from lib.arguments.constants import MAX_PACKET_SIZE_SW
import socket


class DownloadClient:
    def __init__(self, config: DownloadConfig):
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
        return response_packet

    def __send_comm_start(self):
        start_package = SWPacket(
            self.__sequence_number,
            1 if self.__sequence_number == 0 else 0,
            True,
            False,
            False,
            False,
            True,
            b"",
        )
        self.__skt.sendto(
            start_package.encode(), (self.__config.HOST, self.__config.PORT)
        )
        print("Download start packet sent")
        self.__wait_for_ack(start_package)
        self.__swap_sequence_number()
        print("Start ack received")

    def __send_file_name_request(self):
        file_name_package = SWPacket(
            self.__sequence_number,
            1 if self.__sequence_number == 0 else 0,
            True,
            False,
            False,
            False,
            True,
            self.__config.FILE_NAME.encode(),
        )
        self.__skt.sendto(
            file_name_package.encode(), (self.__config.HOST, self.__config.PORT)
        )
        print(f"File name request sent: {self.__config.FILE_NAME}")
        self.__wait_for_ack(file_name_package)
        self.__swap_sequence_number()
        print("File name ack received")

    def __recv_file_data(self):
        ready_for_file_package = SWPacket(
            self.__sequence_number,
            1 if self.__sequence_number == 0 else 0,
            False,
            False,
            True,
            False,
            True,
            b"",
        )
        self.__skt.sendto(
            ready_for_file_package.encode(), (self.__config.HOST, self.__config.PORT)
        )
        print("Ready for file packet sent")
        packet = self.__wait_for_ack(ready_for_file_package)
        print("Receiving file data")
        print(f"Received packet of size {len(packet.payload)}")
        file_buff = []
        while not packet.fin:
            if self.__sequence_number == packet.ack_number:
                file_buff.append(packet.payload)
                print(f"Received packet of size {len(packet.payload)}")
            self.__swap_sequence_number()
            response = SWPacket(
                self.__sequence_number,
                1 if self.__sequence_number == 0 else 0,
                False,
                False,
                True,
                False,
                True,
                b"",
            )
            self.__skt.sendto(
                response.encode(), (self.__config.HOST, self.__config.PORT)
            )
            packet = self.__wait_for_ack(response)

        file_path = f"{self.__config.DESTINATION_PATH}/{self.__config.FILE_NAME}"
        with open(file_path, "wb") as file:
            for data in file_buff:
                file.write(data)

    def run(self):
        print("Starting file download")
        self.__send_comm_start()
        self.__send_file_name_request()
        self.__recv_file_data()
        print(f"File received: {self.__config.FILE_NAME}")
        self.__skt.close()
