from lib.sw_packet import SWPacket
from lib.config import UploadConfig
import socket

class UploadClient:
    def __init__(self, config : UploadConfig):
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__verbose : bool = config.VERBOSE
        self.__destination_address : (str, int) = (config.HOST, config.PORT)
        self.__source_path : str = config.SOURCE_PATH
        self.__file_name : str = config.FILE_NAME

    def run(self):
        data_to_send = SWPacket(1, 1, False, True, False, b"Hello, world!").encode()
        self.__skt.sendto(data_to_send, self.__destination_address)
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        print(f"Packet sequence N°: {packet.seq_number}")
        print(f"Packet ACK N°: {packet.ack_number}")
        print(f"Packet SYN: {packet.syn}")
        print(f"Packet FIN: {packet.fin}")
        print(f"Packet payload: {packet.payload}")
        self.__skt.close()
        print("Connection closed")
