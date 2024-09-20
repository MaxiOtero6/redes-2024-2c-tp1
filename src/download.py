from lib.args_parser import ArgsParser
from lib.config import DownloadConfig
from sys import argv
from lib.download_client import DownloadClient


def main():
    parser = ArgsParser()
    config: DownloadConfig = parser.load_args(argv)
    client : DownloadClient = DownloadClient(config)
    client.run()

if __name__ == "__main__":
    main()
