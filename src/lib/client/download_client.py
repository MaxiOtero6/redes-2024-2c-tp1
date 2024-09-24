from lib.packets.sw_packet import SWPacket
from lib.client.download_config import DownloadConfig
from lib.arguments.constants import MAX_PACKET_SIZE_SW
import socket


class DownloadClient:
    def __init__(self, config: DownloadConfig):
        self.__config = config
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = (self.__config.HOST, self.__config.PORT)
        self.__last_packet_sent = None
        self.__last_packet_received = None

    def __get_packet(self):
        """Get the next packet from the queue."""
        data = self.__skt.recv(MAX_PACKET_SIZE_SW)
        packet = SWPacket.decode(data)
        self.__last_packet_received = packet

    def __send_packet(self, packet):
        """Send a packet to the client."""
        self.__skt.sendto(packet.encode(), self.__address)
        self.__last_packet_sent = packet

    def __send_ack(self):
        """Send an acknowledgment to the client."""
        ack_packet = SWPacket(
            self.__last_packet_received.ack_number,
            self.__last_packet_received.seq_number,
            self.__last_packet_received.syn,
            self.__last_packet_received.fin,
            True,
            self.__last_packet_received.upl,
            self.__last_packet_received.dwl,
            b"",
        )
        self.__send_packet(ack_packet)

    def __wait_for_ack(self):
        self.__get_packet()

        while not self.__last_packet_received.ack or (
            self.__last_packet_sent.seq_number != self.__last_packet_received.ack_number
        ):
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __wait_for_data(self):
        self.__get_packet()

        while not self.__last_packet_received.dwl or (
            self.__last_packet_sent.seq_number != self.__last_packet_received.ack_number
        ):
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __send_comm_start(self):
        start_package = SWPacket(
            0,
            1,
            True,
            False,
            False,
            False,
            True,
            b"",
        )
        self.__send_packet(start_package)
        print("Download start packet sent")

        self.__wait_for_ack()
        print("Start ack received")

    def __send_file_name_request(self):
        file_name_package = SWPacket(
            self.__last_packet_received.ack_number,
            self.__last_packet_received.seq_number,
            True,
            False,
            False,
            False,
            True,
            self.__config.FILE_NAME.encode(),
        )
        self.__send_packet(file_name_package)
        print(f"File name request sent: {self.__config.FILE_NAME}")

        self.__wait_for_ack()
        print("File name ack received")

        file_path = f"{self.__config.DESTINATION_PATH}/{self.__config.FILE_NAME}"

        # Create an empty file or clear the existing file
        with open(file_path, "wb") as _:
            pass

    def __save_file_data(self, file_path):
        with open(file_path, "ab") as file:
            file.write(self.__last_packet_received.payload)

    def __recieve_file_data(self):
        print("Receiving file data")
        file_path = f"{self.__config.DESTINATION_PATH}/{self.__config.FILE_NAME}"

        while not self.__last_packet_received.fin:
            print(f"Received packet of size {len(self.__last_packet_received.payload)}")

            if self.__last_packet_received.dwl and (
                self.__last_packet_received.seq_number
                == self.__last_packet_sent.ack_number
            ):
                self.__save_file_data(file_path)

            self.__send_ack()
            self.__wait_for_data()

        self.__send_ack()

    def run(self):
        print("Starting file download")
        self.__send_comm_start()
        self.__send_file_name_request()
        self.__recieve_file_data()
        print(f"File received: {self.__config.FILE_NAME}")
        self.__skt.close()
