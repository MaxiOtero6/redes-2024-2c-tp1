from sys import exit
from . import constants as const
from .config import Config, ServerConfig, UploadConfig, DownloadConfig
from .verbose import Verbose


class ArgsParser:

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

    def __load_server_args(self, argv: list[str]) -> ServerConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_server()

        verbose = None
        host = None
        port = None
        storage_dir_path = None

        if "-v" in argv or "--verbose" in argv:
            verbose = Verbose.VERBOSE

        elif "-q" in argv or "--quiet" in argv:
            verbose = Verbose.QUIET

        if "-H" in argv or "--host" in argv:
            host = argv[
                self.__get_argv_index(("-H", "--host"), argv) + 1
            ]

        if "-p" in argv or "--port" in argv:
            port = argv[
                self.__get_argv_index(("-p", "--port"), argv) + 1
            ]

        if "-s" in argv or "--storage" in argv:
            storage_dir_path = argv[
                self.__get_argv_index(("-s", "--storage"), argv) + 1
            ]

        return ServerConfig([verbose, host, port, storage_dir_path])

    def __load_upload_client_args(self, argv: list[str]) -> UploadConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_upload()

        verbose = None
        host = None
        port = None
        source_path = None
        file_name = None

        if "-v" in argv or "--verbose" in argv:
            verbose = Verbose.VERBOSE

        elif "-q" in argv or "--quiet" in argv:
            verbose = Verbose.QUIET

        if "-H" in argv or "--host" in argv:
            host = argv[
                self.__get_argv_index(("-H", "--host"), argv) + 1
            ]

        if "-p" in argv or "--port" in argv:
            port = argv[
                self.__get_argv_index(("-p", "--port"), argv) + 1
            ]

        if "-s" in argv or "--src" in argv:
            source_path = argv[
                self.__get_argv_index(("-s", "--src"), argv) + 1
            ]

        if "-n" in argv or "--name" in argv:
            file_name = argv[
                self.__get_argv_index(("-n", "--name"), argv) + 1
            ]

        return UploadConfig([verbose, host, port, source_path, file_name])

    def __load_download_client_args(self, argv: list[str]) -> DownloadConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_download()

        verbose = None
        host = None
        port = None
        destination_path = None
        file_name = None

        if "-v" in argv or "--verbose" in argv:
            verbose = Verbose.VERBOSE

        elif "-q" in argv or "--quiet" in argv:
            verbose = Verbose.QUIET

        if "-H" in argv or "--host" in argv:
            host = argv[
                self.__get_argv_index(("-H", "--host"), argv) + 1
            ]

        if "-p" in argv or "--port" in argv:
            port = argv[
                self.__get_argv_index(("-p", "--port"), argv) + 1
            ]

        if "-d" in argv or "--dst" in argv:
            destination_path = argv[
                self.__get_argv_index(("-d", "--dst"), argv) + 1
            ]

        if "-n" in argv or "--name" in argv:
            file_name = argv[
                self.__get_argv_index(("-n", "--name"), argv) + 1
            ]

        return DownloadConfig([verbose, host, port, destination_path, file_name])

    def load_args(self, argv: list[str]) -> Config:
        match argv[0]:
            case const.DOWNLOAD_CLIENT:
                return self.__load_download_client_args(argv)

            case const.UPLOAD_CLIENT:
                return self.__load_upload_client_args(argv)

            case const.SERVER:
                return self.__load_server_args(argv)

            case _:
                raise Exception("Unknown executed binary")
