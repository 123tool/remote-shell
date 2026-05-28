## 🚀 Remote Shell

A secure, multi-threaded, and cross-platform **Remote Administration Tool (RAT) / Reverse Shell Management** written in Python. This tool allows developers and system administrators to manage remote sessions over an encrypted channel across Windows (CMD) and Linux/Xubuntu (Bash/Sh) systems.

---

## 📌 About The Project

**Prowler Remote Shell** operating on a Client-Server architecture using **Reverse TCP Connections**. Instead of the server connecting to the client (which is often blocked by firewalls or NAT), the client initiates an outbound connection back to the controller.

### Core Architecture & Flow
```text
  [ Attacker / Server ] <--- (Encrypted Outbound Connection) --- [ Target / Client ]
  (prowler-pro console)                                          (Windows Registry/Cronjob)
```

## Key Features
- ​🔒 AES-256 Bit Encryption: All commands and outputs are dynamically encrypted using symmetric AES (CBC Mode). Network sniffers (like Wireshark) or IDS/IPS firewalls cannot read the payload.
- ​🧵 Multi-Threaded Controller: The server can listen for and manage multiple concurrent client connections simultaneously.
- ​🔄 Cross-Platform Capability: Automatically detects the target environment. Executes native commands via cmd.exe on Windows and /bin/bash on Linux systems.
- ​⚡ Boot Persistence: Seamless stealth persistence injection via Windows Registry Run Keys or Linux Cronjobs (@reboot) with a single command.
- ​📁 Advanced File Manager: High-speed encrypted upload and download functions built directly into the remote shell environment.
- ​🎯 Resilient Connection: Features an infinite automated reconnection loop on the client side, ensuring re-engagement if the network drops.

## ​🛠️ Installation & Requirements
​Prerequisites
​Both Server and Client machines require Python 3.x and the standard cryptographic library installed.
```
pip install pycryptodome
```
## Configuration
​Before deploying, open `client.py` and modify the connection configuration to match your server's network parameters :
```
SERVER_IP = 'YOUR_SERVER_IP_OR_DOMAIN'  # e.g., '192.168.1.5' or 'pub-ip.ddns.net'
SERVER_PORT = 9999
```
## How to Use
​Step 1: Start the Server (Controller)
​Run the handler on your controller terminal. This will start listening for inbound beacons :
```
python server.py
```
Step 2: Execute the Client (Target Machine)
​Run the script on the target environment. It will establish an encrypted handshake back to your server :
```
python client.py
```
