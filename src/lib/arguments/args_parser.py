from sys import exit

from lib.arguments import constants
from lib.arguments.args_validator import ArgsValidator
from lib.client.download_config import DownloadConfig
from lib.client.upload_config import UploadConfig
from lib.config import Config
from lib.errors.unknown_binary import UnknownBinary
from lib.server.server_config import ServerConfig
from lib.verbose import Verbose


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
            """usage: download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-a ALGORITHM] # noqa
<command description> # noqa
optional arguments: # noqa
    -h, --help show this help message and exit # noqa
    -v, --verbose increase output verbosity # noqa
    -q, --quiet decrease output verbosity # noqa
    -H, --host server IP address # noqa
    -p, --port server port # noqa
    -d, --dst destination file path # noqa
    -n, --name file name # noqa
    -a, --algorithm data transfer algorithm [sw | sack] # noqa
    -t --timeout timeout in miliseconds"""  # noqa
        )
        exit()

    def __show_help_upload(self) -> None:
        print(
            """usage: upload [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME] [-a ALGORITHM] # noqa
<command description> # noqa
optional arguments: # noqa
    -h, --help show this help message and exit # noqa
    -v, --verbose increase output verbosity # noqa
    -q, --quiet decrease output verbosity # noqa
    -H, --host server IP address # noqa
    -p, --port server port # noqa
    -s, --src source file path # noqa
    -n, --name file name # noqa
    -a, --algorithm data transfer algorithm [sw | sack] # noqa
    -t --timeout timeout in miliseconds"""  # noqa
        )
        exit()

    def __show_help_server(self) -> None:
        print(
            """usage: start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH] [-a ALGORITHM] # noqa
<command description> # noqa
optional arguments: # noqa
    -h, --help show this help message and exit # noqa
    -v, --verbose increase output verbosity # noqa
    -q, --quiet decrease output verbosity # noqa
    -H, --host service IP address # noqa
    -p, --port service port # noqa
    -s, --storage storage dir path # noqa
    -a, --algorithm data transfer algorithm [sw | sack] # noqa
    -t --timeout timeout in miliseconds"""  # noqa
        )
        exit()

    def __get_host(self, argv: list[str]) -> str:
        try:
            idx: int = self.__get_argv_index(("-H", "--host"), argv)
            return self.validator.validate_host(argv[idx + 1])

        except IndexError:
            print(
                "The host address must be specified after -H or --host, e.g: -H 127.0.0.15"  # noqa
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
            print(
                "The port number must be specified after -p or --port, e.g: -p 25565"  # noqa
            )
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
                "The storage dir must be specified after -s or --storage, e.g: -s ~/storage"  # noqa
            )
            exit()

        except Exception as e:
            print(str(e))

    def __get_source_path(self, argv: list[str]) -> str:
        try:
            idx = self.__get_argv_index(("-s", "--src"), argv)
            return argv[idx + 1]

        except IndexError:
            print(
                "The source path must be specified after -s or --src, e.g: -s ~/Documents/file.txt"  # noqa
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
                "The destination path must be specified after -d or --dst, e.g: -d ~/Documents/file.txt"  # noqa
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
            print(
                "The file name must be specified after -n or --name, e.g: -n file.txt"  # noqa
            )
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __get_algorithm(self, argv: list[str]) -> str:
        try:
            idx = self.__get_argv_index(("-a", "--algorithm"), argv)
            return self.validator.validate_algorithm(argv[idx + 1])

        except IndexError:
            print(
                "The algorithm must be specified after -a or --algorithm, e.g: -a sw"  # noqa
            )
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __get_timeout(self, argv: list[str]) -> int:
        try:
            idx = self.__get_argv_index(("-t", "--timeout"), argv)
            return self.validator.validate_timeout(argv[idx + 1])

        except IndexError:
            print(
                "The timeout must be specified after -t or --timeout, e.g: -t 1000"  # noqa
            )
            exit()

        except Exception as e:
            print(str(e))
            exit()

    def __load_server_args(self, argv: list[str]) -> ServerConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_server()

        verbose = constants.DEFAULT_VERBOSE
        host = constants.DEFAULT_SERVER_HOST
        port = constants.DEFAULT_SERVER_PORT
        storage_dir_path = constants.DEFAULT_SERVER_STORAGE_DIR_PATH
        algorithm = constants.DEFAULT_ALGORITHM
        timeout = constants.DEFAULT_TIMEOUT

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

        if "-a" in argv or "--algorithm" in argv:
            algorithm = self.__get_algorithm(argv)

        if "-t" in argv or "--timeout" in argv:
            timeout = self.__get_timeout(argv)

        return ServerConfig([verbose, host, port, algorithm, timeout, storage_dir_path])

    def __load_upload_client_args(self, argv: list[str]) -> UploadConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_upload()

        verbose = constants.DEFAULT_VERBOSE
        host = constants.DEFAULT_SERVER_HOST
        port = constants.DEFAULT_SERVER_PORT
        file_name = None
        source_path = None
        algorithm = constants.DEFAULT_ALGORITHM
        timeout = constants.DEFAULT_TIMEOUT

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

        if "-a" in argv or "--algorithm" in argv:
            algorithm = self.__get_algorithm(argv)

        if "-t" in argv or "--timeout" in argv:
            timeout = self.__get_timeout(argv)

        return UploadConfig(
            [verbose, host, port, algorithm, timeout, source_path, file_name]
        )

    def __load_download_client_args(self, argv: list[str]) -> DownloadConfig:
        if "-h" in argv or "--help" in argv:
            self.__show_help_download()

        verbose = constants.DEFAULT_VERBOSE
        host = constants.DEFAULT_SERVER_HOST
        port = constants.DEFAULT_SERVER_PORT
        destination_path = constants.DEFAULT_DOWNLOAD_DESTINATION_PATH
        file_name = None
        algorithm = constants.DEFAULT_ALGORITHM
        timeout = constants.DEFAULT_TIMEOUT

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

        if "-a" in argv or "--algorithm" in argv:
            algorithm = self.__get_algorithm(argv)

        if "-t" in argv or "--timeout" in argv:
            timeout = self.__get_timeout(argv)

        return DownloadConfig(
            [verbose, host, port, algorithm, timeout, destination_path, file_name]
        )

    def __get_binary(self, path: str) -> str:
        if "/" in path:
            path = path.rsplit("/", 1)[1]
        return path

    def load_args(self, argv: list[str]) -> Config:

        binary = self.__get_binary(argv[0])

        if binary == constants.DOWNLOAD_CLIENT:
            return self.__load_download_client_args(argv)

        elif binary == constants.UPLOAD_CLIENT:
            return self.__load_upload_client_args(argv)

        elif binary == constants.SERVER:
            return self.__load_server_args(argv)

        else:
            raise UnknownBinary("Unknown executed binary")
