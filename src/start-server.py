from lib.arguments.args_parser import ArgsParser
from lib.server.server_config import ServerConfig
from sys import argv
from lib.server.server import Server


def main():
    parser = ArgsParser()
    config: ServerConfig = parser.load_args(argv)
    sv: Server = Server(config)
    sv.run()


if __name__ == "__main__":
    main()
