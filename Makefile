# Environment variables
MININET_PYTHON = python3.8
PYTHON = python3.11

# Network configuration
HOST = 10.0.0.1
PORT = 5001

#Protocol configuration
SW = 'sw'
SACK = 'sack'

# Script paths
TOPOLOGY_SCRIPT = /home/mininet/redes-2024-2c-tp1/src/lib/myTopo.py
SERVER_SCRIPT = /home/mininet/redes-2024-2c-tp1/src/start-server.py
UPLOAD_SCRIPT = /home/mininet/redes-2024-2c-tp1/src/upload.py
DOWNLOAD_SCRIPT = /home/mininet/redes-2024-2c-tp1/src/download.py

# Data directories
SERVER_DATA_DIR = /home/mininet/redes-2024-2c-tp1/server-download-data
CLIENT_UPLOAD_DIR = /home/mininet/redes-2024-2c-tp1/clients-upload-data
CLIENT_DOWNLOAD_DIR = /home/mininet/redes-2024-2c-tp1/clients-download-data

# Files
UPLOAD_FILE = sos-groso.jpg
INVALID_FILE = invalid-file.jpg

# Commands for server and clients
SERVER_COMMAND_SW = xterm -e $(PYTHON) $(SERVER_SCRIPT) -H $(HOST) -p $(PORT) -s $(SERVER_DATA_DIR) -a $(SW)  &
CLIENT_UPLOAD_COMMAND_SW = xterm -hold -e $(PYTHON) $(UPLOAD_SCRIPT) -s '$(CLIENT_UPLOAD_DIR)/$(UPLOAD_FILE)' -n $(UPLOAD_FILE) -H $(HOST) -p $(PORT) -a $(SW) &
INVALID_CLIENT_DOWNLOAD_COMMAND_SW = xterm -e $(PYTHON) $(DOWNLOAD_SCRIPT) -n $(INVALID_FILE) -H $(HOST) -p $(PORT) -a $(SW) &
VALID_CLIENT_DOWNLOAD_COMMAND_SW = xterm -e $(PYTHON) $(DOWNLOAD_SCRIPT) -d $(CLIENT_DOWNLOAD_DIR) -n $(UPLOAD_FILE) -H $(HOST) -p $(PORT) -a $(SW) &



SERVER_COMMAND_SACK = xterm -e $(PYTHON) $(SERVER_SCRIPT) -H $(HOST) -p $(PORT) -s $(SERVER_DATA_DIR) -a $(SACK)  &
CLIENT_UPLOAD_COMMAND_SACK = xterm -hold -e $(PYTHON) $(UPLOAD_SCRIPT) -s '$(CLIENT_UPLOAD_DIR)/$(UPLOAD_FILE)' -n $(UPLOAD_FILE) -H $(HOST) -p $(PORT) -a $(SACK) &
INVALID_CLIENT_DOWNLOAD_COMMAND_SACK = xterm -e $(PYTHON) $(DOWNLOAD_SCRIPT) -n $(INVALID_FILE) -H $(HOST) -p $(PORT) -a $(SACK) &
VALID_CLIENT_DOWNLOAD_COMMAND_SACK = xterm -e $(PYTHON) $(DOWNLOAD_SCRIPT) -d $(CLIENT_DOWNLOAD_DIR) -n $(UPLOAD_FILE) -H $(HOST) -p $(PORT) -a $(SACK) &



# Makefile targets

one_client_download_to_server_and_fail_sw:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) $(NUM_HOST) "$(SERVER_COMMAND_SW)" "$(INVALID_CLIENT_DOWNLOAD_COMMAND_SW)"

one_client_upload_to_server_sw:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) $(NUM_HOST) "$(SERVER_COMMAND_SW)" "$(CLIENT_UPLOAD_COMMAND_SW)"

one_client_upload_to_server_sack:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 2 "$(SERVER_COMMAND_SACK)" "$(CLIENT_UPLOAD_COMMAND_SACK)"



two_clients_upload_to_server_sw:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 3 "$(SERVER_COMMAND_SW)" "$(CLIENT_UPLOAD_COMMAND_SW)"

one_client_download_from_server_sw:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 2 "$(SERVER_COMMAND_SW)" "$(VALID_CLIENT_DOWNLOAD_COMMAND_SW)"
	open $()

two_clients_download_from_server_sw:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) 3 "$(SERVER_COMMAND_SW)" "$(VALID_CLIENT_DOWNLOAD_COMMAND_SW)"

remove_server_db:
	rm -rf server-download-data/*

# Stop the Mininet network
clean:
	@echo "Cleaning the Mininet network..."
	@sudo mn -c
	@sudo killall xterm

