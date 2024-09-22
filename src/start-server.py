from lib.args_parser import ArgsParser
from lib.config import ServerConfig
from sys import argv
from lib.server import Server


def main():
    parser = ArgsParser()
    config: ServerConfig = parser.load_args(argv)
    sv : Server = Server(config)
    sv.run()


if __name__ == "__main__":
    main()
