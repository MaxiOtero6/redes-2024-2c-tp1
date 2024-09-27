import queue
import time
from lib.arguments.constants import MAX_PAYLOAD_SIZE
from lib.packets.sack_packet import SACKPacket


class ClientHandlerSACK:
    def __init__(self, address, socket, folder_path):
        self.data_queue = queue.Queue()
        self.address = address
        self.__socket = socket
        self.__folder_path = folder_path
        self.__last_packet_received = None
        self.__last_packet_sent = None
        
        self.__received_blocks_edges = [] # list[tuple[int, int]] Si recibí los bloques 2,3 y 5,6,7, tendría [(2,3), (5,7)]
        self.out_of_order_buffer = {} # {seq_number: packet}
        self.unacknowledged_packets = {} # {seq_number: packet}
        self.next_expected_seq_number = 0
        self.rwnd = 4096

    def __next_seq_number(self):
        """Get the next sequence number."""
        if self.__last_packet_sent is None:
            return 0
        return 1 - self.__last_packet_sent.seq_number

    def __last_received_ack_number(self):
        """Get the last received acknowledgment number."""
        if self.__last_packet_received is None:
            return 0
        return self.__last_packet_received.ack_number

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

    def __create_new_packet(self, syn, fin, ack, upl, dwl, payload, block_edges):
        return SACKPacket(
            self.__next_seq_number(),
            self.__last_received_ack_number(),
            0,  # Por ahora queda en cero, EDITAR
            upl,
            dwl,
            ack,
            syn,
            fin,
            block_edges,
            payload,
        )

    def __get_packet(self):
        """Get the next packet from the queue."""
        data = self.data_queue.get()
        packet = SACKPacket.decode(data)
        self.__last_packet_received = packet

    def __send_packet(self, packet):
        """Send a packet to the client."""
        self.__socket.sendto(packet.encode(), self.address)
        self.__last_packet_sent = packet


    def __send_sack_ack(self):
        """Send a SACK acknowledgment to the client."""
        ack_packet = self.__create_ack_packet()
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
            self.__received_blocks_edges  # Send the received blocks as SACK info
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
                    []  # No block edges initially
                )
                self.__send_packet(data_packet)
                self.__wait_for_ack()

                # sleep for a second
                time.sleep(0.1)

                data = file.read(MAX_PAYLOAD_SIZE)
                first_packet = False

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
            []
        )
        self.__send_packet(syn_ack_packet)

    def __handle_upl(self, file_name):
        """Handle an upload packet."""

        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Receiving file: {file_name}")

        self.__receive_file_data(file_path)

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
    
    def __create_ack_packet(self):
        """Create an acknowledgment packet, including the list of received blocks (SACK)."""
        ack_packet = self.__create_new_packet(
            syn=False,
            fin=False,
            ack=True,
            upl=self.__last_packet_received.upl,
            dwl=self.__last_packet_received.dwl,
            payload=b"",  # No payload in ACK
            block_edges=self.__received_blocks_edges  # Send the received blocks as SACK info
        )
        return ack_packet

    def __update_received_blocks(self, packet):
        """Update the list of received blocks based on the newly received packet."""
        seq_number = packet.seq_number

        # Insert the new block or merge it with existing ones
        new_block = (seq_number, seq_number)

        # Find where to insert the new block or merge
        updated_blocks = []
        merged = False

        for block in self.__received_blocks_edges:
            if block[1] + 1 == new_block[0]:  # Extend the current block to the new one
                updated_blocks.append((block[0], new_block[1]))
                merged = True
            elif new_block[1] + 1 == block[0]:  # Extend the new block to the current one
                updated_blocks.append((new_block[0], block[1]))
                merged = True
            else:
                updated_blocks.append(block)

        if not merged:
            updated_blocks.append(new_block)

        self.__received_blocks_edges = updated_blocks
        self.out_of_order_buffer[packet.seq_number] = packet.payload  # Store the out-of-order packet

    def __handle_out_of_order_packet(self, packet):
        """Handle an out-of-order packet by buffering it and updating the ACK blocks."""
        seq_number = packet.seq_number

        # Store the packet in the buffer
        self.out_of_order_buffer[seq_number] = packet

        # Update received blocks (SACK)
        self.__update_received_blocks(packet)

        # Check if we can move the next expected sequence number forward
        if seq_number == self.next_expected_seq_number:
            self.__move_next_expected_seq_number()

    def __move_next_expected_seq_number(self):
        """Move the next expected sequence number forward if contiguous packets are received."""
        while self.next_expected_seq_number in self.out_of_order_buffer:
            # Remove the packet from the buffer and move the expected sequence number forward
            del self.out_of_order_buffer[self.next_expected_seq_number]
            self.next_expected_seq_number += 1

    def __send_packet_with_retransmission(self, packet):
        """Send a packet and handle retransmissions"""
        self.__send_packet(packet)

        # Retransmit packets if needed based on unacknowledged packets and received SACK blocks
        while packet.seq_number not in self.unacknowledged_packets:
            self.__send_packet(packet)
            self.__get_packet()  # Wait for acknowledgment or retransmission request


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
        if not (self.__last_packet_received.upl or self.__last_packet_received.dwl):
            raise Exception("Invalid request")

        file_name = self.__handle_file_name()  

        # Handle file transfer (upload or download)
        if self.__last_packet_received.upl:
            self.__send_sack_ack()
            self.__handle_upl(file_name)  
        elif self.__last_packet_received.dwl:
            self.__handle_dwl(file_name)  

        # Handle out-of-order packets if needed
        if not self.__last_packet_sent_was_ack():
            self.__handle_out_of_order_packet(self.__last_packet_received)


'''    
    def __handle_packet(self, packet):
        """Handle an incoming packet and determine if it is in order or out-of-order."""
        seq_number = packet.seq_number

        if seq_number == self.next_expected_seq_number:
            # Packet is in order, process it
            self.__last_packet_received = packet
            self.__move_next_expected_seq_number()  # Move the next expected seq number forward
        else:
            # Packet is out of order, handle it and send a SACK ACK
            self.__handle_out_of_order_packet(packet)

        self.__send_sack_ack()
'''