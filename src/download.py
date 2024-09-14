from lib.args_parser import ArgsParser
from lib.config import DownloadConfig
from sys import argv


def main():
    parser = ArgsParser()
    config: DownloadConfig = parser.load_args(argv)

if __name__ == "__main__":
    main()
