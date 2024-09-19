from lib.sw_packet import SWPacket
from lib.config import UploadConfig
import socket
import os

class UploadClient:
    def __init__(self, config : UploadConfig):
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__verbose : bool = config.VERBOSE
        self.__destination_address : (str, int) = (config.HOST, config.PORT)
        self.__source_path : str = config.SOURCE_PATH
        self.__file_name : str = config.FILE_NAME

        self.__sequence_number = 0

    def __swap_sequence_number(self):
        self.__sequence_number = 1 if self.__sequence_number == 0 else 0

    def __send_file_name(self):
        file_name_package = SWPacket(self.__sequence_number,
                                     1 if self.__sequence_number == 0 else 0,
                                     True, False, False, self.__file_name.encode())
        self.__skt.sendto(file_name_package.encode(), self.__destination_address)
        self.__swap_sequence_number()
        print(f"File name sent: {self.__file_name}")
        (response, address) = self.__skt.recvfrom(520)
        response_packet = SWPacket.decode(response)
        while not response_packet.ack or response_packet.ack_number == self.__sequence_number:
            self.__skt.sendto(file_name_package.encode(), self.__destination_address)
            response = self.__skt.recv(520)
            response_packet = SWPacket.decode(response)
        print(f"File name ack received")

    def __send_file_data(self):
        with open(self.__source_path, "rb") as file:
            data = file.read(512)
            while len(data) != 0:
                packet = SWPacket(self.__sequence_number,
                                  1 if self.__sequence_number == 0 else 0,
                                  False, False, False, data)
                self.__skt.sendto(packet.encode(), self.__destination_address)
                response = self.__skt.recv(520)
                response_packet = SWPacket.decode(response)

                if response_packet.ack and self.__sequence_number == response_packet.ack_number:
                    print(f"Packet of size {len(data)} sent")
                    data = file.read(512)
                    self.__swap_sequence_number()
                else:
                    continue

    def __send_comm_fin(self):
        fin_packet = SWPacket(self.__sequence_number,
                              1 if self.__sequence_number == 0 else 0,
                              False, True, False, b"")
        self.__skt.sendto(fin_packet.encode(), self.__destination_address)
        print("Fin packet sent")

    def run(self):
        print("Starting file upload")
        self.__send_file_name()
        self.__send_file_data()
        self.__send_comm_fin()
        self.__skt.close()
        print("File sent")
