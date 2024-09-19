from lib.args_parser import ArgsParser
from lib.config import UploadConfig
from sys import argv

import socket
from lib.sw_packet import SWPacket


def main():
    parser = ArgsParser()
    config: UploadConfig = parser.load_args(argv)
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_to_send = SWPacket(1, 1, False, True, False, b"Hello, world!").encode()
    skt.sendto(data_to_send, (config.HOST, config.PORT))
    (data, address) = skt.recvfrom(520)
    packet = SWPacket.decode(data)
    print(f"Packet sequence N°: {packet.seq_number}")
    print(f"Packet ACK N°: {packet.ack_number}")
    print(f"Packet SYN: {packet.syn}")
    print(f"Packet FIN: {packet.fin}")
    print(f"Packet payload: {packet.payload}")
    skt.close()
    print("Connection closed")


if __name__ == "__main__":
    main()
