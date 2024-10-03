from lib.config import Config

SOURCE_PATH_INDEX = 5
FILE_NAME_INDEX = 6


class UploadConfig(Config):
    SOURCE_PATH: str
    FILE_NAME: str

    def __init__(self, args: list):
        super().__init__(args)
        self.SOURCE_PATH = args[SOURCE_PATH_INDEX]
        self.FILE_NAME = args[FILE_NAME_INDEX]
