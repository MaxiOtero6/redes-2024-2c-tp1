from lib.sw_packet import SWPacket
from lib.config import ServerConfig
import socket


class Server:
    def __init__(self, config: ServerConfig):
        self.__verbose : bool = config.VERBOSE
        self.__storage_dir : str = config.STORAGE_DIR_PATH
        self.__skt : socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__skt.bind((config.HOST, config.PORT))

    def run(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        print(f"Packet sequence N°: {packet.seq_number}")
        print(f"Packet ACK N°: {packet.ack_number}")
        print(f"Packet SYN: {packet.syn}")
        print(f"Packet FIN: {packet.fin}")
        print(f"Packet payload: {packet.payload}")
        response_data = SWPacket(1, 1, False, True, True, b"ACK").encode()
        self.__skt.sendto(response_data, address)
        self.__skt.close()
        print("Connection closed")