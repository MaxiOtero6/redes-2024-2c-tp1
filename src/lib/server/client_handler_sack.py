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
        self.__window_size = 4096

        # Sender
        self.__maximum_segment_size = 512
        self.__sent_unacknowledged_base = 0
        self.__next_seq_number = 0
        self.__all_data_payloads = {} # {seq_number: payload}
        self.__acknowledged_seq_numbers = set()
        self.__final_data_sequence_number = 0

        # Receiver
        self.__expected_seq_number = 0
        self.__received_data = {}  # {seq_number: payload}
        self.__received_blocks_edges = []  # list of (start_seq, end_seq)
        self.__last_ack_number = 0
        self.out_of_order_buffer = {}  # {seq_number: packet}
        self.__sack_blocks = []  # SACK blocks to send
        self.__received_seq_numbers = set()

    def __get_packet(self):
        """Get the next packet from the queue."""
        data = self.data_queue.get()
        packet = SACKPacket.decode(data)
        self.__last_packet_received = packet

    def __send_packet(self, packet):
        """Send a packet to the client."""
        self.__socket.sendto(packet.encode(), self.address)

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
        if not (self.__last_packet_received.upl or self.__last_packet_received.dwl):
            raise Exception("Invalid request")

        file_name = self.__handle_file_name()  

        # Handle file transfer (upload or download)
        if self.__last_packet_received.upl:
            self.__send_sack_ack()
            self.__handle_upl(file_name)  
        elif self.__last_packet_received.dwl:
            self.__handle_dwl(file_name)  

    def __save_file_data(self, file_path):
        """Save file data received from the client."""
        with open(file_path, "ab") as file:
            file.write(self.__last_packet_received.payload)



    # -------------- SENDER METHODS -------------- #

    def __create_new_sender_packet(self, sequence_number, syn, fin, ack, upl, dwl, payload):
        return SACKPacket(
            sequence_number,
            self.__sent_unacknowledged_base + 1,    # For sender side, ack number will always be the next sequence number to be sent
            self.__window_size,
            upl,
            dwl,
            ack,
            syn,
            fin,
            [],                                     # No block edges in sender side
            payload,
        )
    
    def __handle_dwl(self, file_name):
        """Handle a download packet."""
        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Sending file: {file_name}")

        self.__send_file_data(file_path)
        self.__send_fin()

    def __send_file_data(self, file_path):
        """Send file data to the client."""
        self.__construct_all_payloads(file_path)

        self.__initialize_window()

        while self.__sent_unacknowledged_base < self.__final_data_sequence_number:
            self.__wait_for_ack_and_retransmit()
    
    def __construct_all_payloads(self, file_path):
        """Construct and store all the payloads to be sent."""
        with open(file_path, "rb") as file:
            payload = file.read(MAX_PAYLOAD_SIZE)
            current_seq_number = 0
            while len(payload) > 0:
                self.__all_data_payloads[current_seq_number] = payload
                payload = file.read(self.__maximum_segment_size)
                current_seq_number += self.__maximum_segment_size

            self.__final_data_sequence_number = current_seq_number

    def __initialize_window(self):
        """Initialize the window by sending the first packets."""
        for i in range(self.__window_size // self.__maximum_segment_size):
            seq_number = i * self.__maximum_segment_size

            # Check if the sequence number exists in the payloads
            if seq_number in self.__all_data_payloads:
                payload = self.__all_data_payloads[seq_number]
                
                # Create a new sender packet with the payload
                packet = self.__create_new_sender_packet(
                    sequence_number=seq_number,
                    syn=False,
                    fin=False,
                    ack=False,
                    upl=False,
                    dwl=False,
                    payload=payload,
                )

                # Send the packet and update the last packet sent
                self.__send_packet(packet)
                self.__last_packet_sent = packet
    
    def __wait_for_ack_and_retransmit(self):
        """Wait for ACKs or SACKs, and retransmit missing packets."""
        self.__get_packet()  

        if self.__last_packet_received.block_edges:
            self.__handle_sack(self.__last_packet_received.block_edges)

        # Send new packets if there's room in the window
        self.__send_new_window_packets()

    def __handle_sack(self, sack_blocks):
        """Handle SACK blocks and retransmit missing packets."""
        # Mark the acknowledged sequence numbers based on SACK blocks in order to avoid re-sending an ACKed payload
        for block in sack_blocks:
            left_edge, right_edge = block
            
            # Iterate over the sequence numbers in the range of [left_edge, right_edge)
            for seq_num in range(left_edge, right_edge, self.__maximum_segment_size):
                self.__acknowledged_seq_numbers.add(seq_num)

        self.__update_sent_unacknowledged_base()
    
        # Retransmit any unacknowledged packets in the current window
        for seq_num in range(self.__sent_unacknowledged_base, self.__sent_unacknowledged_base + self.__window_size, self.__maximum_segment_size):
            if seq_num not in self.__acknowledged_seq_numbers:
                # If the sequence number has not been acknowledged, retransmit the packet
                payload = self.__all_data_payloads[seq_num]
                packet = self.__create_new_sender_packet(
                    sequence_number=seq_num,
                    syn=False,
                    fin=False,
                    ack=False,
                    upl=False,
                    dwl=False,
                    payload=payload,
                )
                self.__send_packet(packet)

    def __update_sent_unacknowledged_base(self):
        """Update the sent unacknowledged base based on the acknowledged sequence numbers."""
                # Update sent_unacknowledged_base to the lowest acknowledged seq number
        if self.__acknowledged_seq_numbers:
            # Get the smallest acknowledged sequence number
            new_base = min(self.__acknowledged_seq_numbers)
            
            # Move the base forward if it's valid
            if new_base > self.__sent_unacknowledged_base:
                self.__sent_unacknowledged_base = new_base

    def __send_new_window_packets(self):
        """Send new packets if there's room in the window."""
        while len(self.__acknowledged_seq_numbers) * self.__maximum_segment_size < self.__window_size:
            seq_num = self.__next_seq_number
            if seq_num in self.__all_data_payloads:
                payload = self.__all_data_payloads[seq_num]
                packet = self.__create_new_sender_packet(
                    sequence_number=seq_num,
                    syn=False,
                    fin=False,
                    ack=False,
                    upl=False,
                    dwl=False,
                    payload=payload,
                )
                self.__send_packet(packet)
                self.__next_seq_number += self.__maximum_segment_size
            else:
                break




    # Receiver:

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
    
    def __handle_upl(self, file_name):
        """Handle an upload packet."""

        file_path = f"{self.__folder_path}/{file_name}"
        print(f"Receiving file: {file_name}")

        self.__receive_file_data(file_path)
        

    def __receive_file_data(self, file_path):
        """Receive file data in chunks and save it to the specified file path."""
        
        while True: # SACAR ESTE While true
            self.__get_packet()  

            # Check if the packet is a valid data packet
            if self.__last_packet_received.seq_number >= self.__expected_seq_number:
                # Process the packet based on its sequence number
                if self.__last_packet_received.seq_number == self.__expected_seq_number:
                    # Correct sequence number, save the data
                    self.__save_file_data(file_path)
                    
                    # Acknowledge the received packet
                    self.__last_ack_number = self.__last_packet_received.seq_number
                    self.__send_sack_ack()

                    # Move to the next expected sequence number
                    self.__expected_seq_number += self.__maximum_segment_size

                    # Check if there are any out-of-order packets in the buffer
                    self.__check_out_of_order_packets()
                    
                else:
                    # Out-of-order packet; store it in the buffer
                    self.out_of_order_buffer[self.__last_packet_received.seq_number] = self.__last_packet_received

            else:
                # Packet is old and can be ignored
                print(f"Ignoring old packet with seq number: {self.__last_packet_received.seq_number}")

            # Check if the end of file has been reached
            if self.__last_packet_received.fin:
                print("End of file reached.")
                break

    def __check_out_of_order_packets(self):
        """Check and process any out-of-order packets that can now be received."""
        # Iterate through the out-of-order buffer and process packets that are now in order
        for seq_num in sorted(self.out_of_order_buffer.keys()):
            if seq_num == self.__expected_seq_number:
                # Process the packet
                packet = self.out_of_order_buffer.pop(seq_num)
                self.__save_file_data(packet.payload)
                
                # Acknowledge the packet
                self.__last_ack_number = seq_num
                self.__send_sack_ack()

                # Update the expected sequence number
                self.__expected_seq_number += self.__maximum_segment_size
                
                # Recursively check for more out-of-order packets
                self.__check_out_of_order_packets()


    def __send_sack_ack(self):
        """Send a SACK acknowledgment to the client."""
        sack_packet = self.__create_new_packet(
            False,
            False,
            True,
            self.__last_packet_received.upl,
            self.__last_packet_received.dwl,
            b"",
            self.__received_blocks_edges
        )
        self.__send_packet(sack_packet)
