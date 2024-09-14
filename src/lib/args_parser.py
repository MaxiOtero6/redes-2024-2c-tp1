from sys import exit
from . import constants as const
from .config import Config, ServerConfig, UploadConfig, DownloadConfig
from .verbose import Verbose
from .args_validator import ArgsValidator
from .errors.unknown_binary import UnknownBinary


class ArgsParser:
    validator: ArgsValidator

    def __init__(self):
        self.validator = ArgsValidator()

    def __get_argv_index(self, values: tuple[str], argv: list[str]) -> int:

        try:
            return argv.index(values[0])

        except ValueError:
            return argv.index(values[1])

    def __show_help_download(self) -> None:
        print(
            """usage: download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]
<command description>
optional arguments:
    -h, --help show this help message and exit
    -v, --verbose increase output verbosity
    -q, --quiet decrease output verbosity
    -H, --host server IP address
    -p, --port server port
    -d, --dst destination file path
    -n, --name file name"""
        )
        exit()

    def __show_help_upload(self) -> None:
        print(
            """usage: upload [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME]
<command description>
optional arguments:
-h, --help show this help message and exit
-v, --verbose increase output verbosity
-q, --quiet decrease output verbosity
-H, --host server IP address
-p, --port server port
-s, --src source file path
-n, --name file name"""
        )
        exit()

    def __show_help_server(self) -> None:
        print(
            """usage: start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]
<command description>
optional arguments:
-h, --help show this help message and exit
-v, --verbose increase output verbosity
-q, --quiet decrease output verbosity
-H, --host service IP address
-p, --port service port
-s, --storage storage dir path"""
        )
        exit()

    def __get_host(self, argv: list[str]) -> str:
        try:
            idx: int = self.__get_argv_index(("-H", "--host"), argv)
            return self.validator.validate_host(argv[idx + 1])

        except IndexError:
            print(
                "The host address must be specified after -H or --host, e.g: -H 127.0.0.15"
            )
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __get_port(self, argv: list[str]) -> int:
        try:
            idx: int = self.__get_argv_index(("-p", "--port"), argv)
            return self.validator.validate_port(argv[idx + 1])

        except IndexError:
            print("The port number must be specified after -p or --port, e.g: -p 25565")
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __get_storage_dir(self, argv: list[str]) -> str:
        try:
            idx = self.__get_argv_index(("-s", "--storage"), argv)
            return argv[idx + 1]

        except IndexError:
            print(
                "The storage dir must be specified after -s or --storage, e.g: -s ~/storage")
            exit()

        except Exception as e:
            print(str(e))

    def __get_source_path(self, argv: list[str]) -> str:
        try:
            idx = self.__get_argv_index(("-s", "--src"), argv)
            return argv[idx + 1]

        except IndexError:
            print(
                "The source path must be specified after -s or --src, e.g: -s ~/Documents/file.txt"
            )
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __get_destination_path(self, argv: list[str]) -> str:
        try:
            idx = self.__get_argv_index(("-d", "--dst"), argv)
            return argv[idx + 1]

        except IndexError:
            print(
                "The destination path must be specified after -d or --dst, e.g: -d ~/Documents/file.txt"
            )
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __get_file_name(self, argv: list[str]) -> str:
        try:
            idx = self.__get_argv_index(("-n", "--name"), argv)
            return argv[idx + 1]

        except IndexError:
            print("The file name must be specified after -n or --name, e.g: -n file.txt")
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __load_server_args(self, argv: list[str]) -> ServerConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_server()

        verbose = const.DEFAULT_VERBOSE
        host = const.DEFAULT_SERVER_HOST
        port = const.DEFAULT_SERVER_PORT
        storage_dir_path = const.DEFAULT_SERVER_STORAGE_DIR_PATH

        if "-v" in argv or "--verbose" in argv:
            verbose = Verbose.VERBOSE

        elif "-q" in argv or "--quiet" in argv:
            verbose = Verbose.QUIET

        if "-H" in argv or "--host" in argv:
            host = self.__get_host(argv)

        if "-p" in argv or "--port" in argv:
            port = self.__get_port(argv)

        if "-s" in argv or "--storage" in argv:
            storage_dir_path = self.__get_storage_dir(argv)

        return ServerConfig([verbose, host, port, storage_dir_path])

    def __load_upload_client_args(self, argv: list[str]) -> UploadConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_upload()

        verbose = const.DEFAULT_VERBOSE
        host = const.DEFAULT_SERVER_HOST
        port = const.DEFAULT_SERVER_PORT
        file_name = None
        source_path = None

        if "-v" in argv or "--verbose" in argv:
            verbose = Verbose.VERBOSE

        elif "-q" in argv or "--quiet" in argv:
            verbose = Verbose.QUIET

        if "-H" in argv or "--host" in argv:
            host = self.__get_host(argv)

        if "-p" in argv or "--port" in argv:
            port = self.__get_port(argv)

        if "-s" in argv or "--src" in argv:
            source_path = self.__get_source_path(argv)

        if "-n" in argv or "--name" in argv:
            file_name = self.__get_file_name(argv)

        return UploadConfig([verbose, host, port, source_path, file_name])

    def __load_download_client_args(self, argv: list[str]) -> DownloadConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_download()

        verbose = const.DEFAULT_VERBOSE
        host = const.DEFAULT_SERVER_HOST
        port = const.DEFAULT_SERVER_PORT
        destination_path = const.DEFAULT_DOWNLOAD_DESTINATION_PATH
        file_name = None

        if "-v" in argv or "--verbose" in argv:
            verbose = Verbose.VERBOSE

        elif "-q" in argv or "--quiet" in argv:
            verbose = Verbose.QUIET

        if "-H" in argv or "--host" in argv:
            host = self.__get_host(argv)

        if "-p" in argv or "--port" in argv:
            port = self.__get_port(argv)

        if "-d" in argv or "--dst" in argv:
            destination_path = self.__get_destination_path(argv)

        if "-n" in argv or "--name" in argv:
            file_name = self.__get_file_name(argv)

        return DownloadConfig([verbose, host, port, destination_path, file_name])

    def __get_binary(self, path: str) -> str:
        if '/' in path:
            path = path.rsplit('/', 1)[1]
        return path

    def load_args(self, argv: list[str]) -> Config:

        match self.__get_binary(argv[0]):
            case const.DOWNLOAD_CLIENT:
                return self.__load_download_client_args(argv)

            case const.UPLOAD_CLIENT:
                return self.__load_upload_client_args(argv)

            case const.SERVER:
                return self.__load_server_args(argv)

            case _:
                raise UnknownBinary("Unknown executed binary")
