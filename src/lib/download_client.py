from lib.sw_packet import SWPacket
from lib.config import DownloadConfig
import socket


class DownloadClient():
    def __init__(self, config : DownloadConfig):
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__verbose : bool = config.VERBOSE
        self.__server_address : (str, int) = (config.HOST, config.PORT)
        self.__destination_path : str = config.DESTINATION_PATH
        self.__file_name : str = config.FILE_NAME

        self.__sequence_number = 0

    def __swap_sequence_number(self):
        self.__sequence_number = 1 if self.__sequence_number == 0 else 0

    def __send_comm_start(self):
        start_package = SWPacket(self.__sequence_number,
                                 1 if self.__sequence_number == 0 else 0,
                                 True, False, False, b"download")
        self.__skt.sendto(start_package.encode(), self.__server_address)
        self.__swap_sequence_number()
        print("Download start packet sent")
        (response, address) = self.__skt.recvfrom(520)
        response_packet = SWPacket.decode(response)
        while not response_packet.ack or response_packet.ack_number == self.__sequence_number:
            self.__skt.sendto(start_package.encode(), self.__server_address)
            response = self.__skt.recv(520)
            response_packet = SWPacket.decode(response)
        print("Start ack received")

    def __send_file_name_request(self):
        file_name_package = SWPacket(self.__sequence_number,
                                     1 if self.__sequence_number == 0 else 0,
                                     True, False, False, self.__file_name.encode())
        self.__skt.sendto(file_name_package.encode(), self.__server_address)
        self.__swap_sequence_number()
        print(f"File name request sent: {self.__file_name}")
        (response, address) = self.__skt.recvfrom(520)
        response_packet = SWPacket.decode(response)
        while not response_packet.ack or response_packet.ack_number == self.__sequence_number:
            self.__skt.sendto(file_name_package.encode(), self.__server_address)
            response = self.__skt.recv(520)
            response_packet = SWPacket.decode(response)
        print(f"File name ack received")

    def __recv_file_data(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        last_seq_number = packet.seq_number
        file_buff = [packet.payload]
        print("Receiving file data")
        while not packet.fin:
            if last_seq_number != packet.seq_number:
                file_buff.append(packet.payload)
                print(f"Received packet of size {len(packet.payload)}")
                last_seq_number = packet.seq_number
            response = SWPacket(packet.ack_number, packet.seq_number, False, False, True, b"")
            self.__skt.sendto(response.encode(), address)
            (data, address) = self.__skt.recvfrom(520)
            packet = SWPacket.decode(data)
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