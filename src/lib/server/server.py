from concurrent.futures import ThreadPoolExecutor
import os
import queue
from lib.packets.sw_packet import SWPacket
from lib.server.server_config import ServerConfig
from lib.arguments.constants import MAX_PACKET_SIZE_SW
import socket

from lib.server.client_handler import ClientHandler


class Server:
    def __init__(self, config: ServerConfig):
        self.__config = config
        self.__pool = ThreadPoolExecutor(max_workers=os.cpu_count())
        self.__skt: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__skt.bind((config.HOST, config.PORT))
        self.__clients_handlers = {}

    def __listener(self):
        """Listen for packets and route them to the correct client handler."""
        while True:
            data, address = self.__skt.recvfrom(MAX_PACKET_SIZE_SW)
            packet = SWPacket.decode(data)

            if address not in self.__clients_handlers:
                client = ClientHandler(
                    address, self.__skt, self.__config.STORAGE_DIR_PATH
                )
                self.__clients_handlers[address] = client
                self.__pool.submit(self.__handle_client, client)

            self.__clients_handlers[address].packet_queue.put(packet)

    def __handle_client(self, client: ClientHandler):
        """Handle the client."""
        print("Handling client, ", client.address)

        while client.is_active:
            try:
                packet = client.packet_queue.get(timeout=1)

                if packet.syn:
                    client.handle_syn(packet)
                elif packet.fin:
                    client.handle_fin(packet)
                elif packet.upl:
                    client.handle_upl(packet)
                elif packet.dwl:
                    client.handle_dwl(packet)
            except queue.Empty:
                continue

        print("Client disconnected, ", client.address)
        del self.__clients_handlers[client.address]

    def run(self):
        """Main server function."""
        print("Server started")
        self.__listener()
