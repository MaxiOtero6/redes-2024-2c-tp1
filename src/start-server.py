from lib.args_parser import ArgsParser
from lib.config import ServerConfig
from sys import argv


def main():
    parser = ArgsParser()
    config: ServerConfig = parser.load_args(argv)


if __name__ == "__main__":
    main()
