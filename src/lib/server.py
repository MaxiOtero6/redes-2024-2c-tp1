from lib.sack_packet import SACKPacket
from lib.config import ServerConfig
from lib.constants import MAX_PACKET_SIZE_SACK, MAX_PAYLOAD_SIZE
import socket


class Server:
    def __init__(self, config: ServerConfig):
        self.config = config

        self.__skt: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__skt.bind((config.HOST, config.PORT))

        self.__received_blocks = []

    def __recv_request(self):
        (data, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SACK)
        packet = SACKPacket.decode(data)
        print(f"Received request from {address}")
        response = SACKPacket(
            packet.seq_number,
            packet.ack_number,
            packet.rwnd,
            packet.upl,
            packet.dwl,
            ack=True,
            syn=False,
            fin=False,
            block_edges=[],
            data=b""
        )
        self.__skt.sendto(response.encode(), address)
        return (packet.upl, packet.dwl)

    def __send_sack(self, address, packet):
        response = SACKPacket(
            packet.seq_number,
            packet.ack_number,
            packet.rwnd,
            packet.upl,
            packet.dwl,
            ack=True,
            syn=False,
            fin=False,
            block_edges=self.__received_blocks,
            data=b""
        )
        self.__skt.sendto(response.encode(), address)

    def __recv_file_name(self):
        (data, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SACK)
        packet = SACKPacket.decode(data)
        self.__send_sack(address, packet)
        file_name = packet.payload.decode()
        print(f"File name received: {file_name}")
        return file_name

    def __recv_file_data(self, file_path: str):
        while True:
            (data, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SACK)
            packet = SACKPacket.decode(data)

            self.__received_blocks.append((packet.seq_number, packet.seq_number + len(packet.payload)))
            
            with open(file_path, "ab") as file:
                file.write(packet.payload)

            self.__send_sack(address, packet)

            if packet.fin:
                print("File transfer completed")
                break

    def __run_upload(self):
        file_name = self.__recv_file_name()
        file_path = f"{self.config.STORAGE_DIR_PATH}/{file_name}"
        self.__recv_file_data(file_path)
        print(f"File received: {file_name}")
        self.__skt.close()

    def __send_file_data(self, file_path: str):
        (response_packet, address) = self.__recv_ready()

        with open(file_path, "rb") as file:
            data = file.read(MAX_PAYLOAD_SIZE)
            seq_number = 0

            while data:
                packet = SACKPacket(
                    seq_number,
                    response_packet.ack_number,
                    response_packet.rwnd,
                    response_packet.upl,
                    response_packet.dwl,
                    ack=False,
                    syn=False,
                    fin=False,
                    block_edges=[],  
                    data=data,
                )
                self.__skt.sendto(packet.encode(), address)

                response_data, address = self.__skt.recvfrom(MAX_PACKET_SIZE_SACK)
                response_packet = SACKPacket.decode(response_data)

                for block in response_packet.block_edges:
                    print(f"Block acknowledged: {block}")

                seq_number += len(data)
                data = file.read(MAX_PAYLOAD_SIZE)

        fin_packet = SACKPacket(
            seq_number,
            response_packet.ack_number,
            response_packet.rwnd,
            response_packet.upl,
            response_packet.dwl,
            ack=False,
            syn=False,
            fin=True,
            block_edges=[],
            data=b"",
        )
        self.__skt.sendto(fin_packet.encode(), address)
        print("File sent")

    def __run_download(self):
        file_name = self.__recv_file_name()
        file_path = f"{self.config.STORAGE_DIR_PATH}/{file_name}"
        self.__send_file_data(file_path)
        print(f"File sent: {file_name}")
        self.__skt.close()

    def run(self):
        print("Server started")

        # waits for a request
        upl, dwl = self.__recv_request()

        if upl:
            self.__run_upload()
        elif dwl:
            self.__run_download()

        print("Server stopped")

""" 
    def __recv_file_name(self):
        (data, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SACK)
        packet = SACKPacket.decode(data)
        response_packet = self.__wait_for_ack(address, packet)
        file_name = response_packet.payload.decode()
        print(f"File name received: {file_name}")
        response = SACKPacket(
            packet.ack_number,
            response_packet.seq_number,
            True,
            False,
            True,
            packet.upl,
            packet.dwl,
            b"",
        )
        self.__skt.sendto(response.encode(), address)
        self.__last_ack = packet.seq_number
        return file_name

    def __recv_ready(self):
        (data, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SW)
        packet = SACKPacket.decode(data)
        response_packet = self.__wait_for_ack(address, packet)
        print("Ready for file received")
        return (response_packet, address)

    def __recv_file_data(self, file_path: str):
        (data, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SW)
        packet = SACKPacket.decode(data)
        last_seq_number = packet.seq_number
        file_data = packet.payload
        while not packet.fin:
            if last_seq_number != packet.seq_number:
                file_data += packet.payload
                last_seq_number = packet.seq_number
            response = SACKPacket(
                packet.ack_number,
                packet.seq_number,
                False,
                False,
                True,
                packet.upl,
                packet.dwl,
                b"",
            )
            self.__skt.sendto(response.encode(), address)
            (data, address) = self.__skt.recvfrom(MAX_PACKET_SIZE_SW)
            packet = SACKPacket.decode(data)

        with open(file_path, "wb") as file:
            file.write(file_data)

    def __run_upload(self):
        file_name = self.__recv_file_name()
        file_path = f"{self.config.STORAGE_DIR_PATH}/{file_name}"
        self.__recv_file_data(file_path)
        print(f"File received: {file_name}")
        self.__skt.close()

    def __send_file_data(self, file_path: str):
        (response_packet, address) = self.__recv_ready()
        with open(file_path, "rb") as file:
            data = file.read(MAX_PAYLOAD_SIZE)
            while len(data) != 0:
                packet = SACKPacket(
                    response_packet.ack_number,
                    response_packet.seq_number,
                    False,
                    False,
                    True,
                    response_packet.upl,
                    response_packet.dwl,
                    data,
                )
                self.__skt.sendto(packet.encode(), address)
                self.__last_ack = response_packet.seq_number
                response_packet_raw = self.__skt.recv(MAX_PACKET_SIZE_SW)
                response_packet = SACKPacket.decode(response_packet_raw)
                while (
                    not response_packet.ack
                    or self.__last_ack == response_packet.seq_number
                ):
                    self.__skt.sendto(packet.encode(), address)
                    response_packet_raw = self.__skt.recv(MAX_PACKET_SIZE_SW)
                    response_packet = SACKPacket.decode(response_packet_raw)
                data = file.read(MAX_PAYLOAD_SIZE)
        end_comm_packet = SACKPacket(
            response_packet.ack_number,
            response_packet.seq_number,
            False,
            True,
            True,
            response_packet.upl,
            response_packet.dwl,
            b"",
        )
        self.__skt.sendto(end_comm_packet.encode(), address)
        print("File sent")

    def __run_download(self):
        file_name = self.__recv_file_name()
        file_path = f"{self.config.STORAGE_DIR_PATH}/{file_name}"
        self.__send_file_data(file_path)
        print(f"File sent: {file_name}")
        self.__skt.close()

    def run(self):
        print("Server started")

        # waits for a request
        upl, dwl = self.__recv_request()

        if upl:
            self.__run_upload()
        elif dwl:
            self.__run_download()

        print("Server stopped")
 """