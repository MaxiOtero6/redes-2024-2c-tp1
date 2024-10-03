import ipaddress
from ..errors.port_out_of_bounds import PortOutOfBounds


class ArgsValidator:
    def validate_host(self, host: str) -> str:
        ipaddress.ip_address(host)
        return host

    def validate_port(self, port: str) -> int:
        if not port.isnumeric():
            raise ValueError("Port must be an unsigned integer")

        port = int(port)

        if port >= 0 and port <= 65535:
            return port

        raise PortOutOfBounds("Port must be between 0 and 65535")

    def validate_algorithm(self, algo: str) -> str:
        if algo != "sw" and algo != "sack":
            raise ValueError("Algorithm must be 'sw' or 'sack'")

        return algo

    def validate_timeout(self, timeout: str) -> int:
        if not timeout.isnumeric():
            raise ValueError("Timeout must be an unsigned integer")

        timeout = int(timeout)

        if timeout >= 0:
            return timeout

        raise ValueError("Timeout must be a positive integer")
