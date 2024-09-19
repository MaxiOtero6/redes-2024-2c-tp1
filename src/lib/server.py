from lib.sw_packet import SWPacket
from lib.config import ServerConfig
import socket


class Server:
    def __init__(self, config: ServerConfig):
        self.__verbose : bool = config.VERBOSE
        self.__storage_dir : str = config.STORAGE_DIR_PATH
        self.__skt : socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__skt.bind((config.HOST, config.PORT))

    def __recv_file_name(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        print(f"Received packet from {address}")
        file_name = packet.payload.decode()
        print(f"File name received: {file_name}")
        response = SWPacket(packet.ack_number, packet.seq_number, True, False, True, b"")
        self.__skt.sendto(response.encode(), address)
        return file_name

    def __ack_file_received(self, address : (str, int)):
        response = SWPacket(0, 1, True, False, True, b"")
        self.__skt.sendto(response.encode(), address)

    def __recv_file_data(self, file_path: str):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        last_seq_number = packet.seq_number
        while not packet.fin:
            if last_seq_number != packet.seq_number:
                with open(file_path, "wb") as file:
                    file.write(packet.payload)
                    last_seq_number = packet.seq_number
            response = SWPacket(packet.ack_number, packet.seq_number, False, False, True, b"")
            self.__skt.sendto(response.encode(), address)
            (data, address) = self.__skt.recvfrom(520)
            packet = SWPacket.decode(data)
        self.__ack_file_received(address)


    def run(self):
        file_name = self.__recv_file_name()
        file_path = f"{self.__storage_dir}/{file_name}"
        self.__recv_file_data(file_path)
        print(f"File received: {file_name}")
        self.__skt.close()
