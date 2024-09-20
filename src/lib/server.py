from lib.sw_packet import SWPacket
from lib.config import ServerConfig
import socket


class Server:
    def __init__(self, config: ServerConfig):
        self.__verbose : bool = config.VERBOSE
        self.__storage_dir : str = config.STORAGE_DIR_PATH
        self.__skt : socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__skt.bind((config.HOST, config.PORT))

    def __recv_request(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        print(f"Received request from {address}")
        response = SWPacket(packet.ack_number, packet.seq_number, True, False, True, b"")
        self.__skt.sendto(response.encode(), address)
        return packet.payload

    def __recv_file_name(self):
        (data, address) = self.__skt.recvfrom(520)
        packet = SWPacket.decode(data)
        file_name = packet.payload.decode()
        print(f"File name received: {file_name}")
        response = SWPacket(packet.ack_number, packet.seq_number, True, False, True, b"")
        self.__skt.sendto(response.encode(), address)
        return (file_name, address, packet.ack_number)

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
        (file_name, address, last_seq_number) = self.__recv_file_name()
        file_path = f"{self.__storage_dir}/{file_name}"
        self.__recv_file_data(file_path)
        print(f"File received: {file_name}")
        self.__skt.close()

    def __send_file_data(self, file_path : str, address : (str, int), last_seq_number : int):
        with open(file_path, "rb") as file:
            data = file.read(512)
            last_seq_number = 0 if last_seq_number == 1 else 1
            while len(data) != 0:
                packet = SWPacket(last_seq_number,
                                  1 if last_seq_number == 0 else 0,
                                  False, False, False, data)
                self.__skt.sendto(packet.encode(), address)
                response = self.__skt.recv(520)
                response_packet = SWPacket.decode(response)
                while not response_packet.ack or response_packet.seq_number == last_seq_number:
                    self.__skt.sendto(packet.encode(), address)
                    response = self.__skt.recv(520)
                    response_packet = SWPacket.decode(response)
                last_seq_number = 0 if last_seq_number == 1 else 1
                data = file.read(512)
        end_comm_packet = SWPacket(last_seq_number,
                            1 if last_seq_number == 0 else 0,
                            False, True, True, b"")
        self.__skt.sendto(end_comm_packet.encode(), address)
        print("File sent")


    def __run_download(self):
        (file_name, address, last_seq_number) = self.__recv_file_name()
        file_path = f"{self.__storage_dir}/{file_name}"
        self.__send_file_data(file_path, address, last_seq_number)
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
