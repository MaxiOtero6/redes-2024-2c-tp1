from .verbose import Verbose

DOWNLOAD_CLIENT: str = "download"
UPLOAD_CLIENT: str = "upload"
SERVER: str = "start-server"

DEFAULT_VERBOSE: bool = Verbose.DEFAULT

DEFAULT_SERVER_HOST: str = "127.0.0.1"
DEFAULT_SERVER_PORT: int = 8080
DEFAULT_SERVER_STORAGE_DIR_PATH: str = "~/server-storage"

DEFAULT_DOWNLOAD_DESTINATION_PATH: str = "~/Downloads"
