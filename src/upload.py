from lib.args_parser import ArgsParser
from lib.config import UploadConfig
from sys import argv
from lib.upload_client  import UploadClient


def main():
    parser = ArgsParser()
    config: UploadConfig = parser.load_args(argv)
    client : UploadClient = UploadClient(config)
    client.run()

if __name__ == "__main__":
    main()
