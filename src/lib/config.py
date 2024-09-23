VERBOSE_INDEX = 0
HOST_INDEX = 1
PORT_INDEX = 2
ALGORITHM_INDEX = 3


class Config:
    VERBOSE: bool
    HOST: str
    PORT: int
    ALGORITHM: str

    def __init__(self, args: list):
        self.VERBOSE = args[VERBOSE_INDEX]
        self.HOST = args[HOST_INDEX]
        self.PORT = args[PORT_INDEX]
        self.ALGORITHM = args[ALGORITHM_INDEX]
