from lib.args_parser import ArgsParser
from lib.config import UploadConfig
from sys import argv


def main():
    parser = ArgsParser()
    config: UploadConfig = parser.load_args(argv)


if __name__ == "__main__":
    main()
