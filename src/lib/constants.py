from .verbose import Verbose

DOWNLOAD_CLIENT: str = "download.py"
UPLOAD_CLIENT: str = "upload.py"
SERVER: str = "start-server.py"

DEFAULT_VERBOSE: bool = Verbose.DEFAULT

DEFAULT_SERVER_HOST: str = "127.0.0.1"
DEFAULT_SERVER_PORT: int = 8080
DEFAULT_SERVER_STORAGE_DIR_PATH: str = "~/server-storage"

DEFAULT_DOWNLOAD_DESTINATION_PATH: str = "~/Downloads"

MAX_PAYLOAD_SIZE = 512
MAX_PACKET_SIZE_SW = 520