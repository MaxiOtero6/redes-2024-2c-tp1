import unittest
from lib.arguments.args_parser import ArgsParser
from lib.client.download_config import DownloadConfig
from lib.client.upload_config import UploadConfig
from lib.server.server_config import ServerConfig
from lib.verbose import Verbose


class ArgsParserTest(unittest.TestCase):
    def test_load_server_args(self):
        parser = ArgsParser()
        argv = [
            "start-server.py",
            "-v",
            "-H",
            "127.0.0.1",
            "-p",
            "8080",
            "-s",
            "~/Documents",
            "-a",
            "sw",
        ]

        config: ServerConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, Verbose.VERBOSE)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, 8080)
        self.assertEqual(config.ALGORITHM, "sw")
        self.assertEqual(config.STORAGE_DIR_PATH, "~/Documents")

    def test_load_upload_client_args(self):
        parser = ArgsParser()
        argv = [
            "upload.py",
            "-q",
            "-H",
            "127.0.0.1",
            "-p",
            "8080",
            "-s",
            "dev/null",
            "-n",
            "cat",
            "-a",
            "sack",
        ]

        config: UploadConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, Verbose.QUIET)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, 8080)
        self.assertEqual(config.ALGORITHM, "sack")
        self.assertEqual(config.SOURCE_PATH, "dev/null")
        self.assertEqual(config.FILE_NAME, "cat")

    def test_load_download_client_args(self):
        parser = ArgsParser()
        argv = [
            "download.py",
            "-H",
            "127.0.0.1",
            "-p",
            "8080",
            "-d",
            "dev/null",
            "-n",
            "dog",
        ]

        config: DownloadConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, Verbose.DEFAULT)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, 8080)
        self.assertEqual(config.ALGORITHM, "sw")
        self.assertEqual(config.DESTINATION_PATH, "dev/null")
        self.assertEqual(config.FILE_NAME, "dog")
