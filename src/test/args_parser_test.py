import unittest
from lib.args_parser import ArgsParser
from lib.config import *
from lib.verbose import Verbose


class ArgsParserTest(unittest.TestCase):
    def test_load_server_args(self):
        parser = ArgsParser()
        argv = [
            "start-server", "-v", "-H",
            "127.0.0.1", "-p", "8080", "-s", "~/Documents"
        ]

        config: ServerConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, Verbose.VERBOSE)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, 8080)
        self.assertEqual(config.STORAGE_DIR_PATH, "~/Documents")

    def test_load_upload_client_args(self):
        parser = ArgsParser()
        argv = [
            "upload", "-q", "-H",
            "127.0.0.1", "-p", "8080", "-s",
            "dev/null", "-n", "cat"
        ]

        config: UploadConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, Verbose.QUIET)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, 8080)
        self.assertEqual(config.SOURCE_PATH, "dev/null")
        self.assertEqual(config.FILE_NAME, "cat")

    def test_load_download_client_args(self):
        parser = ArgsParser()
        argv = [
            "download", "-H",
            "127.0.0.1", "-p", "8080", "-d",
            "dev/null", "-n", "dog"
        ]

        config: DownloadConfig = parser.load_args(argv)

        self.assertEqual(config.VERBOSE, Verbose.DEFAULT)
        self.assertEqual(config.HOST, "127.0.0.1")
        self.assertEqual(config.PORT, 8080)
        self.assertEqual(config.DESTINATION_PATH, "dev/null")
        self.assertEqual(config.FILE_NAME, "dog")
