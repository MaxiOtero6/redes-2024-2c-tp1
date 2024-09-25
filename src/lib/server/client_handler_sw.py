import queue
import time
from lib.arguments.constants import MAX_PAYLOAD_SIZE
from lib.packets.sw_packet import SWPacket


class ClientHandlerSW:
    def __init__(self, address, socket, folder_path):
        self.data_queue = queue.Queue()
        self.address = address
        self.__socket = socket
        self.__folder_path = folder_path
        self.__last_packet_received = None
        self.__last_packet_sent = None

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
        data = self.data_queue.get()
        packet = SWPacket.decode(data)
        self.__last_packet_received = packet

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
            print("Waiting for data")
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
            first_packet = True
            while len(data) > 0:
                data_packet = self.__create_new_packet(
                    False,
                    False,
                    first_packet,
                    False,
                    True,
                    data,
                )
                self.__send_packet(data_packet)
                self.__wait_for_ack()

                # sleep for a second
                time.sleep(0.1)

                data = file.read(MAX_PAYLOAD_SIZE)
                first_packet = False

    def __recieve_file_data(self, file_path):
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

        self.__recieve_file_data(file_path)

    def __handle_dwl(self, file_name):
        """Handle a download packet."""
        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Sending file: {file_name}")

        self.__send_file_data(file_path)
        self.__send_fin()

    def __handle_fin(self):
        """Handle the final FIN packet."""
        self.__send_ack()

    def __handle_file_name(self):
        """Receive and handle the file name."""
        file_name = self.__last_packet_received.payload.decode()
        return file_name

    def handle_request(self):
        """Handle the client request."""

        self.__get_packet()

        # Handle the initial SYN packet

        if self.__last_packet_received.syn:
            self.__handle_syn()
        else:
            raise Exception("Invalid request")

        # Get the file name

        self.__get_packet()
        file_name: str = ""

        if self.__last_packet_received.upl or self.__last_packet_received.dwl:
            file_name = self.__handle_file_name()
        else:
            raise Exception("Invalid request")

        # Handle the file data
        if self.__last_packet_received.upl:
            self.__send_ack()
            self.__handle_upl(file_name)
        elif self.__last_packet_received.dwl:
            # Automatically start the download process
            self.__handle_dwl(file_name)
