import queue
from lib.packets.sw_packet import SWPacket


class ClientHandler:
    def __init__(self, address, socket, folder_path):
        self.data_queue = queue.Queue()
        self.is_active = True
        self.address = address
        self.__socket = socket
        self.__folder_path = folder_path
        # self.__is_ready = False
        # self.__last_ack = 0  # For further timeout implementation

    def __get_packet(self):
        """Get the next packet from the queue."""
        # For further timeout implementation
        data = self.data_queue.get()
        return SWPacket.decode(data)

    def handle_request(self):
        """Handle the client request."""

        packet = self.__get_packet()

        # Handle the initial SYN packet

        if packet.syn:
            self.__handle_syn(packet)
        else:
            raise Exception("Invalid request")

        # Get the file name

        packet = self.__get_packet()
        file_name: str = ""

        if packet.upl or packet.dwl:
            file_name = self.__handle_file_name(packet)
        else:
            raise Exception("Invalid request")

        # Handle the file data
        if packet.upl:
            self.handle_upl(file_name)
        elif packet.dwl:
            self.__handle_dwl(file_name)

    def __handle_syn(self, packet):
        """Handle the initial SYN packet."""
        self.__send_ack(packet)

    def handle_upl(self, file_name):
        """Handle an upload packet."""

        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Receiving file: {file_name}")

        # To create / overwrite the file
        with open(file_path, "wb") as _:
            pass

        while self.is_active:
            packet = self.__get_packet()

            if packet.fin:
                self.__handle_fin(packet)
                continue

            self.__save_file_data(packet, file_path)
            self.__send_ack(packet)

    def __handle_dwl(self, file_name):
        """Handle a download packet."""

        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Sending file: {file_name}")

        packet = self.__get_packet()

        self.__send_file_data()

    def __handle_fin(self, packet):
        """Handle the final FIN packet."""
        self.is_active = False

    def __handle_file_name(self, packet):
        """Receive and handle the file name."""
        file_name = packet.payload.decode()
        self.__send_ack(packet)
        return file_name

    def __send_ack(self, packet):
        """Send an acknowledgment to the client."""
        response = SWPacket(
            packet.ack_number,
            packet.seq_number,
            packet.syn,
            packet.fin,
            True,
            packet.upl,
            packet.dwl,
            b"",
        )
        self.__socket.sendto(response.encode(), self.address)

    def __wait_for_ack(self, packet):
        ack_packet = self.__get_packet()

        while not ack_packet.ack or ack_packet.ack_number != packet.seq_number:
            self.__send_ack(packet)
            ack_packet = self.__get_packet()

    def __save_file_data(self, packet, file_path):
        """Save file data received from the client."""
        with open(file_path, "ab") as file:
            file.write(packet.payload)

    def __send_file_data(self):
        """Send file data to the client."""
        # TODO: Implement this
