import os
import queue
from collections import deque
import time
from lib.arguments.constants import (
    MAX_PAYLOAD_SIZE,
    MAX_TIMEOUT_COUNT,
)
from lib.packets.sack_packet import SACKPacket
from lib.errors.invalid_file_name import InvalidFileName

SEQUENCE_NUMBER_LIMIT = 2**32

RWND = MAX_PAYLOAD_SIZE * 2


class ClientHandlerSACK:
    def __init__(self, address, socket, folder_path, timeout):
        self.data_queue = queue.Queue()
        self.address = address
        self.__socket = socket
        self.__folder_path = folder_path
        self.__last_packet_created = None
        self.__timeout_count: int = 0
        self.__timeout = timeout / 1000

        # Reciever
        self.__in_order_packets = deque()  # [packets]
        self.__out_of_order_packets = {}  # {seq_number: packets}
        self.__received_blocks_edges = []  # [(start, end)]
        self.__last_ordered_packet_received = None

        # Sender
        self.__unacked_packets = (
            deque()
        )  # list of unacked packets (packet, time) # noqa
        self.__last_packet_received = None
        self.__in_flight_bytes = 0

    def __start_of_next_seq(self, packet):
        """Get the start of the next sequence number."""
        return (packet.seq_number + packet.length()) % SEQUENCE_NUMBER_LIMIT

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_created is None:
            return 0
        return self.__start_of_next_seq(self.__last_packet_created)

    def __last_received_seq_number(self):
        """Get the last received sequence number."""
        if self.__last_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_packet_received)

    def __next_expected_seq_number(self):
        """Get the next expected sequence number."""
        if self.__last_ordered_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_ordered_packet_received)

    def __last_packet_is_ordered(self):
        """Check if the last packet received is in order."""
        if self.__last_ordered_packet_received is None:
            return True

        return (
            self.__last_packet_received.seq_number == self.__next_expected_seq_number()
        )

    def __time_to_first_unacked_packed_timeout(self):
        """Get the time to the first unacked packet timeout."""
        if len(self.__unacked_packets) == 0:
            return 0

        elapsed_time = time.time() - self.__unacked_packets[0][1]

        if elapsed_time > self.__timeout:
            return 0

        return self.__timeout - elapsed_time

    def __packet_was_acked(self, packet):
        """Check if the packet was acked."""
        ack_number = self.__last_packet_received.ack_number
        end_of_packet = self.__start_of_next_seq(packet)

        difference = abs(end_of_packet - ack_number)
        if difference > SEQUENCE_NUMBER_LIMIT / 2:
            if ack_number < end_of_packet:
                ack_number += SEQUENCE_NUMBER_LIMIT
            else:
                end_of_packet += SEQUENCE_NUMBER_LIMIT

        return end_of_packet <= ack_number

    def __new_ack_received(self):
        """Check if the received packet acked the first unacked packet."""
        if not self.__unacked_packets:
            return False

        first_packet = self.__unacked_packets[0][0]

        return self.__packet_was_acked(first_packet)

    def __sack_received(self):
        return (
            self.__last_packet_received.ack and self.__last_packet_received.block_edges
        )

    def __reorder_blocks(self):
        while self.__next_expected_seq_number() in self.__out_of_order_packets:
            self.__last_ordered_packet_received = self.__out_of_order_packets.pop(
                self.__next_expected_seq_number()
            )
            self.__in_order_packets.append(self.__last_ordered_packet_received)

            _, first_block_end = self.__received_blocks_edges[0]

            if first_block_end == self.__next_expected_seq_number():
                self.__received_blocks_edges.pop(0)
            else:
                self.__received_blocks_edges[0] = (
                    self.__next_expected_seq_number(),
                    first_block_end,
                )

    def __add_in_order_packet(self):
        """Add the in order packet to the queue."""
        self.__last_ordered_packet_received = self.__last_packet_received
        self.__in_order_packets.append(self.__last_ordered_packet_received)

        # Try to reorder the buffered packets
        self.__reorder_blocks()

    def __add_out_of_order_packet(self):
        """Add the out of order packet to the queue."""
        start = self.__last_packet_received.seq_number
        end = start + self.__last_packet_received.length()

        self.__out_of_order_packets[start] = self.__last_packet_received

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
                        _, next_block_end = self.__received_blocks_edges.pop(
                            block_index + 1
                        )
                        self.__received_blocks_edges[block_index] = (
                            block_start,
                            next_block_end,
                        )
                return

            if end < block_start:
                self.__received_blocks_edges.insert(block_index, (start, end))
                return

        if (start, end) not in self.__received_blocks_edges:
            self.__received_blocks_edges.append((start, end))

    def __end_of_last_ordered_packet(self):
        """Get the last received sequence number."""
        if self.__last_ordered_packet_received is None:
            return 0
        return self.__start_of_next_seq(self.__last_ordered_packet_received)

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload):
        ack_num = (
            self.__last_received_seq_number()
            if (dwl and not syn)
            else self.__end_of_last_ordered_packet()
        )  # TODO: Check if this is correct

        packet = SACKPacket(
            self.__next_seq_number(),
            ack_num,
            RWND,
            upl,
            dwl,
            ack,
            syn,
            fin,
            self.__received_blocks_edges,
            payload,
        )

        self.__last_packet_created = packet
        return packet

    def __resend_window(self):
        """Resend all packets in the window."""

        # Maybe shrink the window size here
        size: int = len(self.__unacked_packets)
        for _ in range(size):
            packet, _ = self.__unacked_packets.popleft()
            self.__in_flight_bytes -= packet.length()

            self.__send_packet(packet)

    def __get_packet(self):
        """Get the next packet from the queue."""

        timeout: float
        if self.__last_packet_received is None or self.__last_packet_received.upl:
            timeout = self.__timeout
        elif self.__last_packet_received.dwl:
            timeout = self.__time_to_first_unacked_packed_timeout()

        try:
            data = self.data_queue.get(timeout=timeout)
            packet = SACKPacket.decode(data)
            self.__last_packet_received = packet
            self.__timeout_count = 0

        except (queue.Empty, Exception):
            self.__timeout_count += 1
            if self.__timeout_count >= MAX_TIMEOUT_COUNT:
                raise BrokenPipeError(
                    f"Max timeouts reached. Closing connection {self.address}"  # noqa
                )

            if self.__last_packet_received is None or self.__last_packet_received.upl:
                self.__send_packet(self.__last_packet_created)
            elif self.__last_packet_received.dwl:
                self.__resend_window()

            self.__get_packet()

    def __send_packet(self, packet: SACKPacket):
        """Send a packet to the client."""
        self.__socket.sendto(packet.encode(), self.address)

        if self.__last_packet_received.dwl:
            self.__unacked_packets.append((packet, time.time()))
            self.__in_flight_bytes += packet.length()

    def __handle_sack(self):
        """
        Handle the case when an out of order ack is received. # noqa
        If it has a block edge, check if there is an unacked packet waiting for that block edge, # noqa
        if so, remove it from the unacked packets. # noqa
        """

        # Use an stack to store the queue order
        unacked_packets = []

        for start, end in self.__last_packet_received.block_edges:
            while self.__unacked_packets:
                packet, time = self.__unacked_packets.popleft()

                if packet.seq_number < start:
                    # packet not in any block edge
                    unacked_packets.append((packet, time))
                    continue

                elif self.__start_of_next_seq(packet) > end:
                    # packet not in this block edge, add it back and try the next one # noqa
                    self.__unacked_packets.appendleft((packet, time))
                    break

                # packet was acked, no need to resend
                self.__in_flight_bytes -= packet.length()

        while unacked_packets:
            self.__unacked_packets.appendleft(unacked_packets.pop())

    def __wait_for_ack(self):
        while True:
            # TODO: follow a cumulative ack policy
            self.__get_packet()

            if self.__sack_received():
                self.__handle_sack()

            if self.__new_ack_received():
                break

            else:
                pass
                # TODO: Repeated ACK

        # At least one packet was acked, remove all acked packets from the unacked packets # noqa
        while self.__unacked_packets:
            packet, time = self.__unacked_packets.popleft()

            if not self.__packet_was_acked(packet):
                self.__unacked_packets.appendleft((packet, time))
                break

            self.__in_flight_bytes -= packet.length()

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

    def __wait_for_data(self):
        """Wait for data from the client."""
        while True:
            self.__get_packet()

            if self.__last_packet_received.upl and self.__last_packet_is_ordered():
                break

            if (
                self.__last_packet_received.seq_number
                >= self.__next_expected_seq_number()
            ):
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
        file_length = os.path.getsize(file_path)

        with open(file_path, "rb") as file:
            data_sent = 0
            data = file.read(MAX_PAYLOAD_SIZE)
            is_first_packet = True
            while len(data) > 0 or len(self.__unacked_packets) > 0:
                while (
                    len(data) > 0 and self.__in_flight_bytes < RWND
                ):  # TODO: prevent to send more than the window size
                    packet = self.__create_new_packet(
                        False,
                        False,
                        is_first_packet,
                        False,
                        True,
                        data,
                    )

                    self.__send_packet(packet)
                    data_sent += len(data)

                    print_sent_progress(data_sent, file_length)

                    data = file.read(MAX_PAYLOAD_SIZE)
                    is_first_packet = False

                self.__wait_for_ack()

    def __receive_file_data(self, file_path):
        # To create / overwrite the file
        with open(file_path, "wb") as _:
            pass

        self.__wait_for_data()

        while not self.__last_ordered_packet_received.fin:
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

        self.__in_order_packets.popleft()  # TODO: Check if this is correct
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
        file_name = self.__in_order_packets.popleft().payload.decode()
        return file_name

    def __wait_for_file_name(self):
        """Wait for the file name from the client."""
        while True:
            self.__get_packet()
            if self.__last_packet_is_ordered() and (
                self.__last_packet_received.upl or self.__last_packet_received.dwl
            ):
                self.__add_in_order_packet()
                file_name = self.__handle_file_name()
                if self.__last_ordered_packet_received.upl:
                    self.__send_ack()

                return file_name
            else:
                pass
                # TODO: Should sum a timeout here

    def __wait_for_syn(self):
        """Wait for the initial SYN packet."""
        while True:
            self.__get_packet()
            if self.__last_packet_is_ordered() and self.__last_packet_received.syn:
                self.__add_in_order_packet()
                self.__handle_syn()
                break
            else:
                # TODO: Should sum a timeout here
                pass

    def handle_request(self):
        """Handle the client request."""
        try:
            self.__wait_for_syn()
            file_name = self.__wait_for_file_name()

            # Handle the file data
            if self.__last_ordered_packet_received.upl:
                self.__handle_upl(file_name)
            elif self.__last_ordered_packet_received.dwl:
                self.__handle_dwl(file_name)

        except BrokenPipeError as e:
            print(str(e))

        except Exception as e:
            print(str(e))


def print_sent_progress(data_sent, file_length):
    print(f"Sent packet of size {round(data_sent / file_length * 100, 2)}%")  # noqa
