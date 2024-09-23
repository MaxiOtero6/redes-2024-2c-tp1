import queue
from lib.arguments.constants import MAX_PAYLOAD_SIZE
from lib.packets.sw_packet import SWPacket


class ClientHandlerSW:
    def __init__(self, address, socket, folder_path):
        self.data_queue = queue.Queue()
        self.address = address
        self.__is_active = True
        self.__socket = socket
        self.__folder_path = folder_path
        self.__last_server_ack = 0

    def __get_packet(self):
        """Get the next packet from the queue."""
        # For further timeout implementation
        data = self.data_queue.get()
        return SWPacket.decode(data)

    def __handle_syn(self, packet):
        """Handle the initial SYN packet."""
        self.__send_ack(packet)

    def __handle_upl(self, file_name):
        """Handle an upload packet."""

        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Receiving file: {file_name}")

        # To create / overwrite the file
        with open(file_path, "wb") as _:
            pass

        while self.__is_active:
            packet = self.__get_packet()

            if packet.fin:
                self.__handle_fin(packet)
                continue

            if packet.seq_number != self.__last_server_ack:
                self.__save_file_data(packet, file_path)
            self.__send_ack(packet)

    def __handle_dwl(self, file_name):
        """Handle a download packet."""
        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Sending file: {file_name}")

        packet = self.__send_file_data(file_path)

        self.__send_fin(packet)

    def __handle_fin(self, packet):
        """Handle the final FIN packet."""
        self.__is_active = False
        self.__send_ack(packet)

    def __handle_file_name(self, packet):
        """Receive and handle the file name."""
        file_name = packet.payload.decode()
        return file_name

    def __send_fin(self, packet):
        """Send the final FIN packet."""
        fin_packet = SWPacket(
            packet.ack_number,
            packet.seq_number,
            False,
            True,
            False,
            False,
            False,
            b"",
        )
        self.__socket.sendto(fin_packet.encode(), self.address)
        self.__last_server_ack = fin_packet.seq_number
        self.__wait_for_ack(fin_packet)

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
        self.__last_server_ack = response.seq_number

    def __wait_for_ack(self, packet):
        ack_packet = self.__get_packet()

        while not ack_packet.ack or packet.seq_number != ack_packet.ack_number:
            self.__send_ack(packet)
            ack_packet = self.__get_packet()

        self.__last_server_ack = ack_packet.seq_number

    def __save_file_data(self, packet, file_path):
        """Save file data received from the client."""
        with open(file_path, "ab") as file:
            file.write(packet.payload)

    def __send_file_data(self, file_path):
        """Send file data to the client."""

        print(f"Sending file data {file_path}")

        packet: SWPacket
        with open(file_path, "rb") as file:
            print("Sending file data")
            data = file.read(MAX_PAYLOAD_SIZE)
            while len(data) > 0:
                packet = SWPacket(
                    self.__last_server_ack,
                    self.__seq_number,
                    False,
                    False,
                    False,
                    False,
                    True,
                    data,
                )
                self.__socket.sendto(packet.encode(), self.address)
                self.__wait_for_ack(packet)
                data = file.read(MAX_PAYLOAD_SIZE)

        return packet

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
            self.__send_ack(packet)
            self.__handle_upl(file_name)
        elif packet.dwl:
            self.__handle_dwl(file_name)
