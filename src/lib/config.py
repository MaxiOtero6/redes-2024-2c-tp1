VERBOSE_INDEX = 0
HOST_INDEX = 1
PORT_INDEX = 2
ALGORITHM_INDEX = 3
TIMEOUT_INDEX = 4


class Config:
    VERBOSE: bool
    HOST: str
    PORT: int
    ALGORITHM: str
    TIMEOUT: int

    def __init__(self, args: list):
        self.VERBOSE = args[VERBOSE_INDEX]
        self.HOST = args[HOST_INDEX]
        self.PORT = args[PORT_INDEX]
        self.ALGORITHM = args[ALGORITHM_INDEX]
        self.TIMEOUT = args[TIMEOUT_INDEX]
