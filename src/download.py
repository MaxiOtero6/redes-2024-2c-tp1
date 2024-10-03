from lib.arguments.args_parser import ArgsParser
from lib.client.download_config import DownloadConfig
from lib.client.download_client_sw import DownloadClientSW
from lib.client.download_client_sack import DownloadClientSACK
from sys import argv


def main():
    parser = ArgsParser()
    config: DownloadConfig = parser.load_args(argv)

    client: DownloadClientSW | DownloadClientSACK
    match config.ALGORITHM:
        case "sw":
            client: DownloadClientSW = DownloadClientSW(config)
        case "sack":
            client: DownloadClientSACK = DownloadClientSACK(config)

    client.run()


if __name__ == "__main__":
    main()
