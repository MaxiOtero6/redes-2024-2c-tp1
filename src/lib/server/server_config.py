from lib.config import Config

STORAGE_DIR_PATH_INDEX = 5


class ServerConfig(Config):
    STORAGE_DIR_PATH: str

    def __init__(self, args: list):
        super().__init__(args)
        self.STORAGE_DIR_PATH = args[STORAGE_DIR_PATH_INDEX]
