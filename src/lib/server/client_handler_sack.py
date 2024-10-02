import queue
from collections import deque
import time
from lib.arguments.constants import MAX_PAYLOAD_SIZE, MAX_TIMEOUT_PER_PACKET
from lib.packets.sack_packet import SACKPacket

SEQUENCE_NUMBER_LIMIT = 2**32
RWND = 512

# import debugpy
# debugpy.debug_this_thread()


class ClientHandlerSACK:
    def __init__(self, address, socket, folder_path):
        self.data_queue = queue.Queue()
        self.address = address
        self.__socket = socket
        self.__folder_path = folder_path
        self.__last_packet_sent = None
        self.__timeout_count: int = 0

        # Reciever
        self.__in_order_packets = deque()  # [packets]
        self.__out_of_order_packets = {}  # {seq_number: packets}
        self.__received_blocks_edges = []  # [(start, end)]
        self.__last_ordered_packet_received = None

    def __start_of_next_seq(self, packet):
        """Get the start of the next sequence number."""
        return (packet.seq_number + packet.length()) % SEQUENCE_NUMBER_LIMIT

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_sent is None:
            return 0
        return self.__start_of_next_seq(self.__last_packet_sent)

    def __next_expected_seq_number(self):
        """Get the next expected sequence number."""
        if self.__last_ordered_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_ordered_packet_received)

    def __last_packet_is_ordered(self):
        """Check if the last packet received is in order."""
        if self.__last_ordered_packet_received is None:
            return True

        # print(f"Last ordered: {self.__last_ordered_packet_received.seq_number}")
        # print(f"Next expected: {self.__next_expected_seq_number()}")
        # print(f"Last received: {self.__last_packet_received.seq_number}")

        return (
            self.__last_packet_received.seq_number == self.__next_expected_seq_number()
        )

    def __reorder_packets(self):
        while self.__next_expected_seq_number() in self.__out_of_order_packets:
            self.__last_ordered_packet_received = self.__out_of_order_packets.pop(
                self.__next_expected_seq_number()
            )
            self.__in_order_packets.append(self.__last_ordered_packet_received)

            _, first_block_end = self.__received_blocks_edges[0]

            if first_block_end == self.__start_of_next_seq(
                self.__last_ordered_packet_received
            ):
                self.__received_blocks_edges.pop(0)
            else:
                self.__received_blocks_edges[0] = (
                    self.__last_ordered_packet_received.seq_number,
                    first_block_end,
                )

    def __add_in_order_packet(self):
        """Add the in order packet to the queue."""
        self.__last_ordered_packet_received = self.__last_packet_received
        self.__in_order_packets.append(self.__last_ordered_packet_received)

        # Try to reorder the buffered packets
        self.__reorder_packets()

    def __add_out_of_order_packet(self):
        """Add the out of order packet to the queue."""
        start = self.__last_packet_received.seq_number
        end = start + len(self.__last_packet_received.payload)

        self.__out_of_order_packets[start] = self.__last_ordered_packet_received

        for block_index in range(len(self.__received_blocks_edges)):
            block_start, block_end = self.__received_blocks_edges[block_index]

            if end == block_start:
                self.__received_blocks_edges[block_index] = (start, block_end)
                return

            if start == block_end:
                self.__received_blocks_edges[block_index] = (block_start, end)

                if block_index + 1 < len(self.__received_blocks_edges):
                    next_block_start, _ = self.__received_blocks_edges[block_index + 1]
                    if next_block_start == end:
                        _, next_block_end = self.__received_blocks_edges[
                            block_index + 1
                        ]
                        self.__received_blocks_edges[block_index] = (
                            start,
                            next_block_end,
                        )

            if end < block_start:
                self.__received_blocks_edges.insert(block_index, (start, end))
                return

        self.__received_blocks_edges.append((start, end))

    def __end_of_last_ordered_packet(self):
        """Get the last received sequence number."""
        if self.__last_ordered_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_ordered_packet_received)

    # def __last_packet_is_new(self):
    #     """Check if the last packet received is new."""
    #     return True  # Implement this

    # def __last_packet_sent_was_ack(self):
    #     """Check if the last packet sent was an acknowledgment."""
    #     return (
    #         self.__last_packet_received.ack
    #         and self.__last_packet_sent.seq_number
    #         == self.__last_packet_received.ack_number
    #     )

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload):
        return SACKPacket(
            self.__next_seq_number(),
            self.__end_of_last_ordered_packet(),
            RWND,
            upl,
            dwl,
            ack,
            syn,
            fin,
            self.__received_blocks_edges,
            payload,
        )

    def __get_packet(self):
        """Get the next packet from the queue."""
        try:
            # data = self.data_queue.get(timeout=TIMEOUT)
            data = self.data_queue.get()
            packet = SACKPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        except (queue.Empty, Exception):
            self.__timeout_count += 1
            print(f"Timeout number: {self.__timeout_count}")

            if self.__timeout_count >= MAX_TIMEOUT_PER_PACKET:
                raise BrokenPipeError(
                    f"Max timeouts reached, is client {self.address} alive?. Closing connection"
                )

            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __send_packet(self, packet: SACKPacket):
        """Send a packet to the client."""
        self.__socket.sendto(packet.encode(), self.address)
        self.__last_packet_sent = packet

    def __send_ack(self):
        """Send an acknowledgment to the client."""

        ack_packet = self.__create_new_packet(
            self.__last_ordered_packet_received.syn,
            self.__last_ordered_packet_received.fin,
            True,
            self.__last_ordered_packet_received.upl,
            self.__last_ordered_packet_received.dwl,
            b"",
        )

        self.__send_packet(ack_packet)

    def __send_sack(self):
        """Send a SACK packet to the client."""
        sack_packet = self.__create_new_packet(
            False,
            False,
            True,
            self.__last_packet_received.upl,
            self.__last_packet_received.dwl,
            b"",
        )
        self.__send_packet(sack_packet)

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

    def __wait_for_ack(self):
        """Wait for an appropriate acknowledgment from the client."""
        self.__get_packet()

        while not self.__last_packet_sent_was_ack():
            self.__send_packet(self.__last_packet_sent)
            self.__get_packet()

    def __wait_for_data(self):
        """Wait for data from the client."""
        while True:
            print("Waiting for data")

            self.__get_packet()

            if self.__last_packet_received.upl and self.__last_packet_is_ordered():
                break

            self.__add_out_of_order_packet()
            self.__send_sack()

        # The last packet received is ordered
        self.__add_in_order_packet()

    def __save_file_data(self, file_path):
        """Save file data received from the client."""
        with open(file_path, "ab") as file:
            while self.__in_order_packets:
                packet = self.__in_order_packets.popleft()
                file.write(packet.payload)

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

        self.__in_order_packets.clear()  # TODO: prolijo

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
        try:
            self.__get_packet()
            if self.__last_packet_is_ordered():
                self.__add_in_order_packet()
            else:
                raise Exception("Invalid request")  # TODO: Handle this

            # Handle the initial SYN packet
            if self.__last_packet_received.syn:
                self.__handle_syn()
            else:
                raise Exception("Invalid request")

            # Get the file name
            self.__get_packet()
            if self.__last_packet_is_ordered():
                self.__add_in_order_packet()
            else:
                raise Exception("Invalid request")  # TODO: Handle this

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

        except BrokenPipeError as e:
            print(str(e))

        except Exception as e:
            print(str(e))
