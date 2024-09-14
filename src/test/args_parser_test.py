import unittest
from lib.args_parser import ArgsParser
from lib.config import *


class ArgsParserTest(unittest.TestCase):
    def test_load_server_args(self):
        parser = ArgsParser()
        argv = [
            "start-server", "-v", "-H",
            "127.0.0.1", "-p", "8080", "-s", "repository"
        ]

        config: ServerConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, True)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, "8080")
        self.assertEqual(config.STORAGE_DIR_PATH, "repository")

    def test_load_upload_client_args(self):
        parser = ArgsParser()
        argv = [
            "upload", "-q", "-H",
            "127.0.0.1", "-p", "8080", "-s",
            "~/Documents/cat.png", "-n", "cat"
        ]

        config: UploadConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, False)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, "8080")
        self.assertEqual(config.SOURCE_PATH, "~/Documents/cat.png")
        self.assertEqual(config.FILE_NAME, "cat")

    def test_load_download_client_args(self):
        parser = ArgsParser()
        argv = [
            "download", "-v", "-H",
            "127.0.0.1", "-p", "8080", "-d",
            "~/Downloads/dog.png", "-n", "dog"
        ]

        config: DownloadConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, True)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, "8080")
        self.assertEqual(config.DESTINATION_PATH, "~/Downloads/dog.png")
        self.assertEqual(config.FILE_NAME, "dog")
