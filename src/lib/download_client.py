from lib.sw_packet import SWPacket
from lib.config import DownloadConfig
import socket

class DownloadClient:
    def __init__(self, config : DownloadConfig):
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__verbose : bool = config.VERBOSE
        self.__server_address : (str, int) = (config.HOST, config.PORT)
        self.__destination_path : str = config.DESTINATION_PATH
        self.__file_name : str = config.FILE_NAME
        self.__sequence_number = 0

    def __swap_sequence_number(self):
        self.__sequence_number = 1 if self.__sequence_number == 0 else 0

    def __wait_for_ack(self, previous_packet : SWPacket):
        (response, address) = self.__skt.recvfrom(520)
        response_packet = SWPacket.decode(response)
        while not response_packet.ack or response_packet.ack_number != self.__sequence_number:
            self.__skt.sendto(previous_packet.encode(), self.__server_address)
            response = self.__skt.recv(520)
            response_packet = SWPacket.decode(response)
        return response_packet

    def __send_comm_start(self):
        start_package = SWPacket(self.__sequence_number,
                                 1 if self.__sequence_number == 0 else 0,
                                 True, False, False, b"download")
        self.__skt.sendto(start_package.encode(), self.__server_address)
        print("Download start packet sent")
        self.__wait_for_ack(start_package)
        self.__swap_sequence_number()
        print("Start ack received")

    def __send_file_name_request(self):
        file_name_package = SWPacket(self.__sequence_number,
                                     1 if self.__sequence_number == 0 else 0,
                                     True, False, False, self.__file_name.encode())
        self.__skt.sendto(file_name_package.encode(), self.__server_address)
        print(f"File name request sent: {self.__file_name}")
        self.__wait_for_ack(file_name_package)
        self.__swap_sequence_number()
        print(f"File name ack received")

    def __recv_file_data(self):
        ready_for_file_package = SWPacket(self.__sequence_number,
                                          1 if self.__sequence_number == 0 else 0,
                                          False, False, True, b"Ready")
        self.__skt.sendto(ready_for_file_package.encode(), self.__server_address)
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
            response = SWPacket(self.__sequence_number, 1 if self.__sequence_number == 0 else 0,
                                False, False, True, b"")
            self.__skt.sendto(response.encode(), self.__server_address)
            packet = self.__wait_for_ack(response)
        with open(f"{self.__destination_path}/{self.__file_name}", "wb") as file:
            for data in file_buff:
                file.write(data)

    def run(self):
        print("Starting file download")
        self.__send_comm_start()
        self.__send_file_name_request()
        self.__recv_file_data()
        print(f"File received: {self.__file_name}")
        self.__skt.close()