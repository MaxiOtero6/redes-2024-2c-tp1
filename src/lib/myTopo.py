from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
import sys
import subprocess
import time


class MyTopo(Topo):
    "Simple topology example with a variable number of clients."

    def __init__(self, num_hosts=2, loss=10, delay=20):
        self.num_hosts = num_hosts
        self.loss = loss
        self.delay = str(delay) + "ms"
        Topo.__init__(self)
        self.build()

    def build(self):
        "Create custom topo."

        # Add switch
        switch = self.addSwitch("s1")

        # Add hosts
        server = self.addHost(f"h1")
        self.addLink(server, switch, cls=TCLink, loss=self.loss, delay=self.delay)

        for i in range(2, self.num_hosts + 1):
            host = self.addHost(f"h{i}")
            self.addLink(host, switch)


topos = {"mytopo": (lambda: MyTopo())}


def start_server_and_clients(num_hosts, server_command, client_command, loss, delay):
    net = Mininet(topo=MyTopo(num_hosts=num_hosts, loss=loss, delay=delay), link=TCLink)

    # Start the network
    net.start()

    print(f"Network started with {num_hosts} hosts.")

    # Start the server on host h1
    server_host = net.get("h1")
    print(f"Starting server on {server_host.name}...")
    server_output = server_host.cmd(server_command)

    time.sleep(2)

    # Start clients on other hosts
    for i in range(2, num_hosts + 1):
        client_host = net.get(f"h{i}")
        client_output = client_host.cmd(client_command)
        print(client_output)

    # Wait for user input before stopping
    input("Press Enter to stop the network...")
    net.stop()


if __name__ == "__main__":
    if __name__ == "__main__":
        setLogLevel("info")

    # Example: Pass server and client commands via command line
    if len(sys.argv) < 4:
        print(
            "Usage: python3 topology.py <num_hosts> <server_command> <client_command>"
        )
        sys.exit(1)

    num_hosts = int(sys.argv[1])
    server_command = sys.argv[2]
    client_command = sys.argv[3]
    loss = int(sys.argv[4])
    delay = int(sys.argv[5])

    start_server_and_clients(num_hosts, server_command, client_command, loss, delay)
