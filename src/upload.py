from lib.arguments.args_parser import ArgsParser
from lib.client.upload_config import UploadConfig
from sys import argv
from lib.client.upload_client_sw import UploadClientSW
from lib.client.upload_client_sack import UploadClientSACK


def main():
    parser = ArgsParser()
    config: UploadConfig = parser.load_args(argv)

    if config.ALGORITHM == "sw":
        client: UploadClientSW = UploadClientSW(config)
    elif config.ALGORITHM == "sack":
        client: UploadClientSACK = UploadClientSACK(config)

    client.run()


if __name__ == "__main__":
    main()
