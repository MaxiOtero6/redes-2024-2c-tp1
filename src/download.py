from lib.arguments.args_parser import ArgsParser
from lib.client.download_config import DownloadConfig
from lib.client.download_client_sw import DownloadClient
from sys import argv


def main():
    parser = ArgsParser()
    config: DownloadConfig = parser.load_args(argv)
    client: DownloadClient = DownloadClient(config)
    client.run()


if __name__ == "__main__":
    main()
