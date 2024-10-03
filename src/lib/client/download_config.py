from lib.config import Config

DESTINATION_PATH_INDEX = 5
FILE_NAME_INDEX = 6


class DownloadConfig(Config):
    DESTINATION_PATH: str
    FILE_NAME: str

    def __init__(self, args: list):
        super().__init__(args)
        self.DESTINATION_PATH = args[DESTINATION_PATH_INDEX]
        self.FILE_NAME = args[FILE_NAME_INDEX]
