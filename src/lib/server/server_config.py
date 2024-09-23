from lib.arguments.constants import MAX_PACKET_SIZE_SW, MAX_PAYLOAD_SIZE
from lib.config import Config
from lib.packets.sw_packet import SWPacket

STORAGE_DIR_PATH_INDEX = 4


class ServerConfig(Config):
    STORAGE_DIR_PATH: str

    def __init__(self, args: list):
        super().__init__(args)
        self.STORAGE_DIR_PATH = args[STORAGE_DIR_PATH_INDEX]
