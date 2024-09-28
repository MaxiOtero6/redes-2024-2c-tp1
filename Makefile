# Variables
PYTHON=python3
SERVER_SCRIPT=start_server.py
UPLOAD_SCRIPT=upload.py
DOWNLOAD_SCRIPT=download.py
STORAGE_DIR=./storage
MININET_TOPOLOGY=single,2
MININET_OPTIONS=--mac --switch ovsk --controller remote

# Mininet command
MN=sudo mn --topo $(MININET_TOPOLOGY) $(MININET_OPTIONS)

# Phony targets
.PHONY: all clean run_server run_client upload download

# Default target
all: clean

# Clean storage directory
clean:
	rm -rf $(STORAGE_DIR)
	mkdir -p $(STORAGE_DIR)

# Run the server in Mininet
run_server:
	$(MN) -- bash -c "$(PYTHON) $(SERVER_SCRIPT) -H 10.0.0.1 -p 5001 -s $(STORAGE_DIR)"

# Upload a file to the server in Mininet
upload:
	$(MN) -- bash -c "$(PYTHON) $(UPLOAD_SCRIPT) -H 10.0.0.1 -p 5001 -s /path/to/local/file -n filename"

# Download a file from the server in Mininet
download:
	$(MN) -- bash -c "$(PYTHON) $(DOWNLOAD_SCRIPT) -H 10.0.0.1 -p 5001 -d /path/to/save/file -n filename"

# Run all (server and client upload/download)
run_all: run_server upload download
