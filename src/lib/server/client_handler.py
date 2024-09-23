import queue
from lib.arguments.constants import MAX_PACKET_SIZE_SW, MAX_PAYLOAD_SIZE
from lib.packets.sw_packet import SWPacket


class ClientHandler:
    def __init__(self, address, socket, folder_path):
        self.address = address
        self.socket = socket
        self.folder_path = folder_path
        self.packet_queue = queue.Queue()
        self.last_ack = 0
        self.is_active = True
        self.file_name = ""
        self.is_ready = False

    def handle_syn(self, packet):
        """Handle the initial SYN packet."""

        response = SWPacket(
            packet.ack_number,
            packet.seq_number,
            True,
            False,
            True,
            packet.upl,
            packet.dwl,
            b"",
        )
        self.socket.sendto(response.encode(), self.address)

    def handle_upl(self, packet):
        """Handle an upload packet."""
        if self.file_name == "":
            self.file_name = self.__recv_file_name(packet)
        else:
            self.__save_file_data(packet)

    def handle_dwl(self, packet):
        """Handle a download packet."""
        if self.file_name == "":
            self.file_name = self.__recv_file_name(packet)
        elif not self.is_ready:
            self.wait_for_ready()
            self.__send_file_data()

    def handle_fin(self, packet):
        """Handle the final FIN packet."""
        self.is_active = False

    def __recv_file_name(self, packet):
        """Receive and handle the file name."""
        file_name = packet.payload.decode()

        # Send acknowledgment
        response = SWPacket(
            packet.ack_number,
            packet.seq_number,
            False,
            False,
            True,
            packet.upl,
            packet.dwl,
            b"",
        )

        self.socket.sendto(response.encode(), self.address)

        if packet.upl:
            print(f"Receiving file: {file_name}")

            file_path = f"{self.folder_path}/{file_name}"
            with open(file_path, "wb") as file:
                pass

        elif packet.dwl:
            print(f"Sending file: {file_name}")

        return file_name

    def __save_file_data(self, packet):
        """Save file data received from the client."""
        file_path = f"{self.folder_path}/{self.file_name}"

        with open(file_path, "ab") as file:
            file.write(packet.payload)

        response = SWPacket(
            packet.ack_number,
            packet.seq_number,
            False,
            False,
            True,
            packet.upl,
            packet.dwl,
            b"",
        )
        self.socket.sendto(response.encode(), self.address)

    def __send_file_data(self):
        """Send file data to the client."""
        # TODO: Implement this
