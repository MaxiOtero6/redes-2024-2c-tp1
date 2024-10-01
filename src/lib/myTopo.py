from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
import sys
import subprocess
import time


class MyTopo(Topo):
    "Simple topology example with a variable number of clients."

    def __init__(self, num_hosts=2):
        self.num_hosts = num_hosts
        Topo.__init__(self)
        self.build()

    def build(self):
        "Create custom topo."

        # Add switch
        switch = self.addSwitch('s1')

        # Add hosts
        for i in range(1, self.num_hosts + 1):
            host = self.addHost(f'h{i}')
            self.addLink(host, switch, cls=TCLink, loss=10)


topos = {'mytopo': (lambda: MyTopo())}


def start_server_and_clients(num_hosts, server_command, client_command):
    net = Mininet(topo=MyTopo(num_hosts=num_hosts), link=TCLink)

    # Start the network
    net.start()

    print(f"Network started with {num_hosts} hosts.")

    # Start the server on host h1
    server_host = net.get('h1')

    #server_command = f"xterm -e python3.11 /home/mininet/redes-2024-2c-tp1/src/start-server.py -H 10.0.0.1 -p 5001 -s /home/mininet/redes-2024-2c-tp1/storage &"
    server_output = server_host.cmd(server_command)

    # Open an xterm window for the server host and run the server command
    print(f"Starting server on {server_host.name}...")
    time.sleep(2)
    # Start clients on other hosts
    for i in range(2, num_hosts + 1):
        client_host = net.get('h2')
        #client_command = f"xterm -hold -e  python3.11 /home/mininet/redes-2024-2c-tp1/src/upload.py -s '/home/mininet/redes-2024-2c-tp1/upload-data/sos-groso.jpg' -n sos-groso.jpg  -H 10.0.0.1 -p 5001 &"
        client_output = client_host.cmd(client_command)

    # Wait for user input before stopping
    input("Press Enter to stop the network...")
    net.stop()


if __name__ == '__main__':
    if __name__ == '__main__':
        setLogLevel('info')

    # Example: Pass server and client commands via command line
    if len(sys.argv) < 4:
        print("Usage: python3.11 topology.py <num_hosts> <server_command> <client_command>")
        sys.exit(1)

    num_hosts = int(sys.argv[1])
    server_command = sys.argv[2]
    client_command = sys.argv[3]

    start_server_and_clients(num_hosts, server_command, client_command)
