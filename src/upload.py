from lib.arguments.args_parser import ArgsParser
from lib.client.upload_config import UploadConfig
from sys import argv
from lib.client.upload_client_sw import UploadClient


def main():
    parser = ArgsParser()
    config: UploadConfig = parser.load_args(argv)
    client: UploadClient = UploadClient(config)
    client.run()


if __name__ == "__main__":
    main()
