# redes-2024-2c-tp1

https://www.youtube.com/watch?v=dQw4w9WgXcQ


## Mininet Installation and Running the Project

This guide provides the steps to install Mininet and explains how to run the network topology and commands using the provided Makefile.

### Prerequisites
Before running the project, ensure that you have the following installed:

**Mininet**: A network emulator that can create, configure, and run large-scale networks on a single machine.

**xterm**: A terminal emulator for the X Window System, required to open multiple terminals for the server and client processes.
Installing Mininet

In our case, we used the Mininet VM option available on the [official Mininet download page](https://mininet.org/download/#option-4-upgrading-an-existing-mininet-installation). This option comes preconfigured with `xterm`, so there's no need for additional installations. However, please note that the VM does not provide a graphical user interface (GUI) by default. If you need a GUI, you may need to install additional software or use an X11 server.


If you'd like to explore other installation options, such as installing Mininet natively on your system, please refer to [official Mininet download page](https://mininet.org/download/#option-4-upgrading-an-existing-mininet-installation) for detailed instructions.

### Running Mininet
After downloading and setting up the Mininet VM, you can run the network topology and different predefined scenarios using the provided Makefile.

### Running the Project with the Makefile
The Makefile provided in this project contains several predefined scenarios for starting a network with various client-server interactions. These scenarios include actions such as file uploads and downloads between clients and a server.

To run any of these scenarios, simply use make <target> to execute them. For example, you can start the network with a server and a client trying to download an invalid file, or with multiple clients uploading files to the server.

### Cleaning the Network
After running any scenario, you can clean up the Mininet environment by using the make clean command, which will stop the network and close any xterm windows that were opened.

### Removing Server Data
If you want to remove files stored on the server, there's a target in the Makefile to clean the server's data directory without deleting the directory itself.

### Notes
Mininet documentation: For more information on how Mininet works and other installation options, refer to the [official Mininet documentation](https://mininet.org).

xterm: If you are using the Mininet VM, xterm comes pre-installed. However, if you're installing Mininet in another way and xterm is not available, make sure to install it to properly visualize the consoles for each client and server interaction.