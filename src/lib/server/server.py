from concurrent.futures import ThreadPoolExecutor
import os
from lib.server.server_config import ServerConfig
from lib.arguments.constants import MAX_PACKET_SIZE_SACK, MAX_PACKET_SIZE_SW
import socket

from lib.server.client_handler_sw import ClientHandlerSW
from lib.server.client_handler_sack import ClientHandlerSACK
from lib.errors.unknown_algorithm import UnknownAlgorithm

WORKERS = max(os.cpu_count(), 4)


class Server:
    def __init__(self, config: ServerConfig):
        self.__config = config
        self.__pool = ThreadPoolExecutor(max_workers=WORKERS)
        self.__socket: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind((config.HOST, config.PORT))
        self.__clients_handlers = {}

    def __create_client(
        self, address: tuple[str, int]
    ) -> ClientHandlerSW | ClientHandlerSACK:
        match (self.__config.ALGORITHM):
            case "sw":
                return ClientHandlerSW(
                    address,
                    self.__socket,
                    self.__config.STORAGE_DIR_PATH,
                    self.__config.TIMEOUT,
                )

            case "sack":
                return ClientHandlerSACK(
                    address,
                    self.__socket,
                    self.__config.STORAGE_DIR_PATH,
                    self.__config.TIMEOUT,
                )

            case _:
                raise UnknownAlgorithm(f"Unknown algorithm: {self.__config.ALGORITHM}")

    def __listener(self):
        """Listen for packets and route them to the correct client handler."""
        MAX_EXPECTED_PACKET_SIZE = (
            MAX_PACKET_SIZE_SW
            if self.__config.ALGORITHM == "sw"
            else MAX_PACKET_SIZE_SACK
        )

        while True:
            data, address = self.__socket.recvfrom(MAX_EXPECTED_PACKET_SIZE)
            if address not in self.__clients_handlers:
                client = self.__create_client(address)
                self.__clients_handlers[address] = client
                self.__pool.submit(self.__handle_client, client)

            self.__clients_handlers[address].data_queue.put(data)

    def __handle_client(self, client: ClientHandlerSW):
        """Handle the client."""
        address = client.address
        print("Handling client, ", address)

        client.handle_request()

        print("Client disconnected, ", address)
        del self.__clients_handlers[address]

    def __check_storage_dir(self):
        """Check if the storage directory exists and create it if it doesn't."""
        if not os.path.exists(self.__config.STORAGE_DIR_PATH):
            os.makedirs(self.__config.STORAGE_DIR_PATH)

    def run(self):
        """Main server function."""
        print("Server started")
        self.__check_storage_dir()
        self.__listener()
