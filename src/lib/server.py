from lib.sw_packet import SWPacket
from lib.config import ServerConfig
import socket

class Server:
    def __init__(self, config: ServerConfig):
        self.__verbose : bool = config.VERBOSE
        self.__storage_dir : str = config.STORAGE_DIR_PATH
        self.__skt : socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__skt.bind((config.HOST, config.PORT))

        self.__last_ack = 0

    def __recv_request(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        print(f"Received request from {address}")
        response = SWPacket(packet.ack_number, packet.seq_number, True, False, True, b"")
        self.__last_ack = packet.seq_number
        self.__skt.sendto(response.encode(), address)
        return packet.payload

    def __recv_file_name(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)

        while packet.seq_number == self.__last_ack:
            response = SWPacket(packet.ack_number, self.__last_ack, True, False, True, b"")
            self.__skt.sendto(response.encode(), address)
            (data, address) = self.__skt.recvfrom(520)
            packet = SWPacket.decode(data)

        file_name = packet.payload.decode()
        print(f"File name received: {file_name}")
        response = SWPacket(packet.ack_number, packet.seq_number, True, False, True, b"")
        self.__skt.sendto(response.encode(), address)
        self.__last_ack = packet.seq_number
        return (file_name, address)

    def __recv_ready(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)

        while packet.seq_number == self.__last_ack:
            response = SWPacket(packet.ack_number, self.__last_ack, True, False, True, b"")
            self.__skt.sendto(response.encode(), address)
            (data, address) = self.__skt.recvfrom(520)
            packet = SWPacket.decode(data)

        print("Ready for file received")
        return (packet, address)

    def __recv_file_data(self, file_path: str):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        last_seq_number = packet.seq_number
        file_buff = [packet.payload]
        while not packet.fin:
            if last_seq_number != packet.seq_number:
                file_buff.append(packet.payload)
                last_seq_number = packet.seq_number
            response = SWPacket(packet.ack_number, packet.seq_number, False, False, True, b"")
            self.__skt.sendto(response.encode(), address)
            (data, address) = self.__skt.recvfrom(520)
            packet = SWPacket.decode(data)

        with open(file_path, "wb") as file:
            for data in file_buff:
                file.write(data)

    def __run_upload(self):
        (file_name, address) = self.__recv_file_name()
        file_path = f"{self.__storage_dir}/{file_name}"
        self.__recv_file_data(file_path)
        print(f"File received: {file_name}")
        self.__skt.close()

    def __send_file_data(self, file_path : str):
        (response_packet, address) = self.__recv_ready()
        with open(file_path, "rb") as file:
            data = file.read(512)
            while len(data) != 0:
                packet = SWPacket(response_packet.ack_number,
                                  response_packet.seq_number,
                                  False, False, True, data)
                self.__skt.sendto(packet.encode(), address)
                self.__last_ack = response_packet.seq_number
                response_packet_raw = self.__skt.recv(520)
                response_packet = SWPacket.decode(response_packet_raw)
                while not response_packet.ack or self.__last_ack == response_packet.seq_number:
                    self.__skt.sendto(packet.encode(), address)
                    response_packet_raw = self.__skt.recv(520)
                    response_packet = SWPacket.decode(response_packet_raw)
                data = file.read(512)
        end_comm_packet = SWPacket(response_packet.ack_number,
                                    response_packet.seq_number,
                                    False, True, True, b"")
        self.__skt.sendto(end_comm_packet.encode(), address)
        print("File sent")

    def __run_download(self):
        (file_name, address) = self.__recv_file_name()
        file_path = f"{self.__storage_dir}/{file_name}"
        self.__send_file_data(file_path)
        print(f"File sent: {file_name}")
        self.__skt.close()

    def run(self):
        print("Server started")
        service_type = self.__recv_request()
        if service_type == b"upload":
            self.__run_upload()
        if service_type == b"download":
            self.__run_download()

        print("Server stopped")
