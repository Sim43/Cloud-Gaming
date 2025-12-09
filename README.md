# Gamepad Control System

A GUI-based application for remote gamepad control with screen streaming capabilities.

## Features

- **Server Mode**: Runs gamepad server and screen streaming server simultaneously
- **Client Mode**: Connects to server and sends keyboard commands
- **Auto IP Detection**: Automatically detects and displays server IP address

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the GUI application:

```bash
python3 main.py
```

### Server Mode
1. Select "Server Mode"
2. Click "Start Server"
3. Note the displayed IP address
4. Share the IP with clients

### Client Mode
1. Select "Client Mode"
2. Enter the server IP address
3. Click "Connect & Start"
4. Use the keyboard input window to send commands

## Controls

- **W/A/S/D**: D-pad directions
- **U/I/J/K**: Gamepad buttons (X/Y/A/B)
- **Arrow Keys**: D-pad directions
- **Space**: A button
