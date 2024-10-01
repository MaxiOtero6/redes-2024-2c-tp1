from lib.packets.sw_packet import SWPacket
from lib.client.download_config import DownloadConfig
from lib.arguments.constants import MAX_PACKET_SIZE_SW, MAX_TIMEOUT_PER_PACKET, TIMEOUT
import socket


class DownloadClient:
    def __init__(self, config: DownloadConfig):
        self.__config = config
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__address = (self.__config.HOST, self.__config.PORT)
        self.__last_packet_sent = None
        self.__last_packet_received = None
        self.__timeout_count: int = 0

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_sent is None:
            return 0
        return 1 - self.__last_packet_sent.seq_number

    def __last_recived_seq_number(self):
        """Get the last received sequence number."""
        if self.__last_packet_received is None:
            return 0
        return self.__last_packet_received.seq_number

    def __last_packet_is_new(self):
        """Check if the last packet received is new."""
        return (
            self.__last_packet_received.seq_number != self.__last_packet_sent.ack_number
        )

    def __last_packet_sent_was_ack(self):
        """Check if the last packet sent was an acknowledgment."""
        return (
            self.__last_packet_received.ack
            and self.__last_packet_sent.seq_number
            == self.__last_packet_received.ack_number
        )

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload):
        return SWPacket(
            self.__next_seq_number(),
            self.__last_recived_seq_number(),
            syn,
            fin,
            ack,
            upl,
            dwl,
            payload,
        )

    def __get_packet(self):
        """Get the next packet from the queue."""
        self.__skt.settimeout(TIMEOUT)

        try:
            data = self.__skt.recv(MAX_PACKET_SIZE_SW)
            packet = SWPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        except socket.timeout:
            self.__timeout_count += 1
            print(f"Timeout!!: {self.__timeout_count}")

            if self.__timeout_count >= MAX_TIMEOUT_PER_PACKET:
                raise BrokenPipeError(
                    "Max timeouts reached, is client alive?. Closing connection"
                )

            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __send_packet(self, packet):
        """Send a packet to the client."""
        self.__skt.settimeout(0)
        self.__skt.sendto(packet.encode(), self.__address)
        self.__last_packet_sent = packet

    def __send_ack(self):
        """Send an acknowledgment to the client."""
        ack_packet = self.__create_new_packet(
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

        while not self.__last_packet_sent_was_ack():
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __wait_for_data(self):
        self.__get_packet()

        while not (self.__last_packet_received.dwl and self.__last_packet_is_new()):
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __send_comm_start(self):
        start_package = self.__create_new_packet(
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
        file_name_package = self.__create_new_packet(
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
            print(
                f"Received packet of size {len(self.__last_packet_received.payload)}"
            )

            self.__save_file_data(file_path)

            self.__send_ack()
            self.__wait_for_data()

        self.__send_ack()

    def run(self):
        try:
            print("Starting file download")
            self.__send_comm_start()
            self.__send_file_name_request()
            self.__recieve_file_data()
            print(f"File received: {self.__config.FILE_NAME}")
            self.__skt.close()

        except BrokenPipeError as e:
            print(str(e))
            self.__skt.close()
            exit()