from concurrent.futures import ThreadPoolExecutor
import os
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

            if address not in self.__clients_handlers:
                client = ClientHandler(
                    address, self.__skt, self.__config.STORAGE_DIR_PATH
                )
                self.__clients_handlers[address] = client
                self.__pool.submit(self.__handle_client, client)

            self.__clients_handlers[address].data_queue.put(data)

    def __handle_client(self, client: ClientHandler):
        """Handle the client."""
        address = client.address
        print("Handling client, ", address)

        client.handle_request()

        print("Client disconnected, ", address)
        del self.__clients_handlers[address]

    def run(self):
        """Main server function."""
        print("Server started")
        self.__listener()
