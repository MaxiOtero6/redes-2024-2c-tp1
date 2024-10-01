# Variables
MININET_PYTHON = python3.8
PYTHON = python3.11
TOPOLOGY_SCRIPT = /home/mininet/redes-2024-2c-tp1/src/lib/myTopo.py 
SERVER_COMMAND = xterm -e python3.11 /home/mininet/redes-2024-2c-tp1/src/start-server.py -H 10.0.0.1 -p 5001 -s /home/mininet/redes-2024-2c-tp1/server-download-data &
CLIENT_UPLOAD_COMMAND = xterm -hold -e python3.11 /home/mininet/redes-2024-2c-tp1/src/upload.py -s '/home/mininet/redes-2024-2c-tp1/clients-upload-data/sos-groso.jpg' -n sos-groso.jpg -H 10.0.0.1 -p 5001 &
INVALID_CLIENT_DOWNLOAD_COMMAND = xterm -e python3.11 /home/mininet/redes-2024-2c-tp1/src/download.py -n invalid-file.jpg -H 10.0.0.1 -p 5001 &
VALID_CLIENT_DOWNLOAD_COMMAND = xterm -e python3.11 /home/mininet/redes-2024-2c-tp1/src/download.py -d /home/mininet/redes-2024-2c-tp1/clients-download-data -n sos-groso.jpg -H 10.0.0.1 -p 5001 &

# Start the Mininet network with dynamic commands
one_client_download_to_server_and_fail:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 2 "$(SERVER_COMMAND)" "$(INVALID_CLIENT_DOWNLOAD_COMMAND)"

one_client_upload_to_server:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 2 "$(SERVER_COMMAND)" "$(CLIENT_UPLOAD_COMMAND)"

two_clients_upload_to_server:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 3 "$(SERVER_COMMAND)" "$(CLIENT_UPLOAD_COMMAND)"

one_client_download_from_server:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 2 "$(SERVER_COMMAND)" "$(VALID_CLIENT_DOWNLOAD_COMMAND)"
	open $()

two_clients_download_from_server:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 3 "$(SERVER_COMMAND)" "$(VALID_CLIENT_DOWNLOAD_COMMAND)"
	open $()

remove_server_db:
	rm -rf server-download-data/*


# Stop the Mininet network
clean:
	@echo "Cleaning the Mininet network..."
	@sudo mn -c

# Default target: Start network
all: start_network
