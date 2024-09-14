from .verbose import Verbose

VERBOSE_INDEX = 0
HOST_INDEX = 1
PORT_INDEX = 2
DESTINATION_PATH_INDEX = 3
SOURCE_PATH_INDEX = 3
STORAGE_DIR_PATH_INDEX = 3
FILE_NAME_INDEX = 4


class Config:
    VERBOSE: bool
    HOST: str
    PORT: int

    def __init__(self, args: list):
        self.VERBOSE = args[VERBOSE_INDEX]
        self.HOST = args[HOST_INDEX]
        self.PORT = args[PORT_INDEX]


class DownloadConfig(Config):
    DESTINATION_PATH: str
    FILE_NAME: str

    def __init__(self, args: list):
        super().__init__(args)
        self.DESTINATION_PATH = args[DESTINATION_PATH_INDEX]
        self.FILE_NAME = args[FILE_NAME_INDEX]


class UploadConfig(Config):
    SOURCE_PATH: str
    FILE_NAME: str

    def __init__(self, args: list):
        super().__init__(args)
        self.SOURCE_PATH = args[SOURCE_PATH_INDEX]
        self.FILE_NAME = args[FILE_NAME_INDEX]


class ServerConfig(Config):
    STORAGE_DIR_PATH: str

    def __init__(self, args: list):
        super().__init__(args)
        self.STORAGE_DIR_PATH = args[STORAGE_DIR_PATH_INDEX]
