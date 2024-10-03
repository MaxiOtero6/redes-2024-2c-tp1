# Environment variables
MININET_PYTHON = python3.8
PYTHON = python3.11

# Network configuration
HOST = 10.0.0.1
PORT = 5001

#Time
TIME = time

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

#Timeout 
TIMEOUT = $(shell expr $(DELAY) \* 3 )

#Loss 
DEFAULT_LOSS = 10

#Delay (value in ms)
DEFAULT_DELAY = 10

# Commands for server and clients
SERVER_COMMAND_SW = xterm -e $(PYTHON) $(SERVER_SCRIPT) -H $(HOST) -p $(PORT) -s $(SERVER_DATA_DIR) -a $(SW) -t $(TIMEOUT)  &
CLIENT_UPLOAD_COMMAND_SW = xterm -hold -e time $(PYTHON) $(UPLOAD_SCRIPT) -s '$(CLIENT_UPLOAD_DIR)/$(CLIENT_FILE)' -n $(CLIENT_FILE) -H $(HOST) -p $(PORT) -a $(SW) -t $(TIMEOUT)  &
VALID_CLIENT_DOWNLOAD_COMMAND_SW = xterm -hold -e $(PYTHON) $(DOWNLOAD_SCRIPT) -d $(CLIENT_DOWNLOAD_DIR) -n $(CLIENT_FILE) -H $(HOST) -p $(PORT) -a $(SW) -t $(TIMEOUT) &


SERVER_COMMAND_SACK = xterm -e $(PYTHON) $(SERVER_SCRIPT) -H $(HOST) -p $(PORT) -s $(SERVER_DATA_DIR) -a $(SACK) -t $(TIMEOUT) &
CLIENT_UPLOAD_COMMAND_SACK = xterm -hold -e time $(PYTHON) $(UPLOAD_SCRIPT) -s '$(CLIENT_UPLOAD_DIR)/$(CLIENT_FILE)' -n $(CLIENT_FILE) -H $(HOST) -p $(PORT) -a $(SACK) -t $(TIMEOUT) &
VALID_CLIENT_DOWNLOAD_COMMAND_SACK = xterm -hold -e $(PYTHON) $(DOWNLOAD_SCRIPT) -d $(CLIENT_DOWNLOAD_DIR) -n $(CLIENT_FILE) -H $(HOST) -p $(PORT) -a $(SACK) -t $(TIMEOUT) &

# Use default file if FILE is not passed
CLIENT_FILE = $(if $(FILE),$(FILE),$(UPLOAD_FILE))
LOSS = $(if $(A_LOSS),$(A_LOSS), $(DEFAULT_LOSS))
DELAY = $(if $(A_DELAY),$(A_DELAY), $(DEFAULT_DELAY))

# Makefile targets

upload_to_server_sw:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) $(NUM_HOST) "$(SERVER_COMMAND_SW)" "$(CLIENT_UPLOAD_COMMAND_SW)" $(LOSS) $(DELAY)
	@sudo mn -c
	@sudo killall xterm

upload_to_server_sack:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) $(NUM_HOST) "$(SERVER_COMMAND_SACK)" "$(CLIENT_UPLOAD_COMMAND_SACK)" $(LOSS) $(DELAY)
	@sudo mn -c
	@sudo killall xterm


download_from_server_sw:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) $(NUM_HOST) "$(SERVER_COMMAND_SW)" "$(VALID_CLIENT_DOWNLOAD_COMMAND_SW)" $(LOSS) $(DELAY)
	@sudo mn -c
	@sudo killall xterm


download_from_server_sack:
	@echo "Starting the Mininet network with server and client commands..."
	@sudo $(MININET_PYTHON) $(TOPOLOGY_SCRIPT) $(NUM_HOST) "$(SERVER_COMMAND_SACK)" "$(VALID_CLIENT_DOWNLOAD_COMMAND_SACK)" $(LOSS) $(DELAY)
	@sudo mn -c
	@sudo killall xterm

remove_server_db:
	rm -rf server-download-data/*

remove_client_download_data:
	rm -rf clients-download-data/*

# Stop the Mininet network
clean:
	@echo "Cleaning the Mininet network..."
	@sudo mn -c
	@sudo killall xterm

