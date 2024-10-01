# Variables
MININET_PYTHON = python3
PYTHON = python3.11
TOPOLOGY_SCRIPT = /home/mininet/redes-2024-2c-tp1/src/myTopo.py
SERVER_COMMAND = "xterm -e python3.11 /home/mininet/redes-2024-2c-tp1/src/start-server.py -H 10.0.0.1 -p 5001 -s /home/mininet/redes-2024-2c-tp1/storage &"
CLIENT_UPLOAD_COMMAND = "xterm -hold -e python3.11 /home/mininet/redes-2024-2c-tp1/src/upload.py -s '/home/mininet/redes-2024-2c-tp1/upload-data/sos-groso.jpg' -n sos-groso.jpg -H 10.0.0.1 -p 5001 &"
CLIENT_DOWNLOAD_COMMAND = "xterm -hold -e python3.11 /home/mininet/redes-2024-2c-tp1/src/download.py -s '/home/mininet/redes-2024-2c-tp1/upload-data/sos-groso.jpg' -n sos-groso.jpg -H 10.0.0.1 -p 5001 &"
# Start the Mininet network with dynamic commands
start_one_server_one_client_upload:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 2 "$(SERVER_COMMAND)" "$(CLIENT_COMMAND)"


start_one_server_two_clients_upload:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 3 "$(SERVER_COMMAND)" "$(CLIENT_COMMAND)"


# Stop the Mininet network
stop_network:
	@echo "Stopping the Mininet network..."
	@sudo mn -c

# Default target: Start network
all: start_network
