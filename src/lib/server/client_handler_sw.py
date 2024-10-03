import queue
import time
import os
from lib.arguments.constants import MAX_PAYLOAD_SIZE
from lib.arguments.constants import (
    MAX_PAYLOAD_SIZE,
    MAX_TIMEOUT_COUNT,
)
from lib.packets.sw_packet import SWPacket
from lib.errors.invalid_file_name import InvalidFileName


class ClientHandlerSW:
    def __init__(self, address, socket, folder_path, timeout):
        self.data_queue = queue.Queue()
        self.address = address
        self.__socket = socket
        self.__folder_path = folder_path
        self.__last_packet_received = None
        self.__last_packet_sent = None
        self.__timeout_count: int = 0
        self.__timeout = timeout / 1000

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_sent is None:
            return 0
        return 1 - self.__last_packet_sent.seq_number

    def __last_received_seq_number(self):
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
            self.__last_received_seq_number(),
            syn,
            fin,
            ack,
            upl,
            dwl,
            payload,
        )

    def __get_packet(self):
        """Get the next packet from the queue."""
        try:
            data = self.data_queue.get(timeout=self.__timeout)
            packet = SWPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        except (queue.Empty, Exception):
            self.__timeout_count += 1
            if self.__timeout_count >= MAX_TIMEOUT_COUNT:
                raise BrokenPipeError(
                    f"Max timeouts reached. Closing connection {self.address}"  # noqa
                )

            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __send_packet(self, packet):
        """Send a packet to the client."""
        self.__socket.sendto(packet.encode(), self.address)
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
        """Wait for an appropriate acknowledgment from the client."""
        self.__get_packet()

        while not self.__last_packet_sent_was_ack():
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __wait_for_data(self):
        """Wait for data from the client."""
        self.__get_packet()

        while not (self.__last_packet_received.upl and self.__last_packet_is_new()):
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __send_fin(self):
        """Send the final FIN packet."""
        fin_packet = self.__create_new_packet(
            False,
            True,
            False,
            self.__last_packet_received.upl,
            self.__last_packet_received.dwl,
            b"",
        )
        self.__send_packet(fin_packet)
        self.__wait_for_ack()

    def __save_file_data(self, file_path):
        """Save file data received from the client."""
        with open(file_path, "ab") as file:
            file.write(self.__last_packet_received.payload)

    def __send_file_data(self, file_path):
        """Send file data to the client."""
        with open(file_path, "rb") as file:
            data = file.read(MAX_PAYLOAD_SIZE)
            is_first_packet = True
            while len(data) > 0:
                data_packet = self.__create_new_packet(
                    False,
                    False,
                    is_first_packet,
                    False,
                    True,
                    data,
                )
                self.__send_packet(data_packet)
                self.__wait_for_ack()

                data = file.read(MAX_PAYLOAD_SIZE)
                is_first_packet = False

    def __receive_file_data(self, file_path):
        # To create / overwrite the file
        with open(file_path, "wb") as _:
            pass

        self.__wait_for_data()

        while not self.__last_packet_received.fin:
            self.__save_file_data(file_path)
            self.__send_ack()
            self.__wait_for_data()

        self.__handle_fin()

    def __handle_syn(self):
        """Handle the initial SYN packet."""
        syn_ack_packet = self.__create_new_packet(
            True,
            False,
            True,
            self.__last_packet_received.upl,
            self.__last_packet_received.dwl,
            b"",
        )

        self.__send_packet(syn_ack_packet)

    def __handle_upl(self, file_name):
        """Handle an upload packet."""

        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Receiving file: {file_name}")

        self.__receive_file_data(file_path)

    def __check_file_in_fs(self, file_name):
        """Check if the file exists in the file system."""
        file_path = f"{self.__folder_path}/{file_name}"
        if not os.path.exists(file_path):
            raise InvalidFileName("File does not exist")
        return file_path

    def __handle_dwl(self, file_name):
        """Handle a download packet."""
        try:
            file_path = self.__check_file_in_fs(file_name)
            print(f"Sending file: {file_name}")
            self.__send_file_data(file_path)
            self.__send_fin()
        except InvalidFileName as e:
            print("Failed with error:", e)
            print("No file found with the name:", file_name)
            print("Sending comm fin to client")
            self.__send_fin()

    def __handle_fin(self):
        """Handle the final FIN packet."""
        self.__send_ack()

    def __handle_file_name(self):
        """Receive and handle the file name."""
        file_name = self.__last_packet_received.payload.decode()
        return file_name

    def __wait_for_syn(self):
        while True:
            self.__get_packet()
            # Handle the initial SYN packet
            if self.__last_packet_received.syn:
                self.__handle_syn()
                break

            else:
                # TODO: Should add a timeout here
                pass

    def __wait_for_file_name(self):
        while True:
            self.__get_packet()

            if self.__last_packet_is_new() and (
                self.__last_packet_received.upl or self.__last_packet_received.dwl
            ):
                file_name = self.__handle_file_name()
                if self.__last_packet_received.upl:
                    self.__send_ack()

                return file_name
            else:
                # TODO: Should add a timeout here
                pass

    def handle_request(self):
        """Handle the client request."""
        try:
            self.__wait_for_syn()
            file_name = self.__wait_for_file_name()

            # Handle the file data
            if self.__last_packet_received.upl:
                self.__handle_upl(file_name)
            elif self.__last_packet_received.dwl:
                self.__handle_dwl(file_name)

        except BrokenPipeError as e:
            print(str(e))
