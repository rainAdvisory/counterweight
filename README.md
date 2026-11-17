# Counterweight

Robotics Club weight-based inventory project using an ESP32-C6, HX711 and load cell.

## Current repository contents

- `simulator/local_server.py`: existing standalone Python demonstration with fixed simulated readings (30 g, 3 items). It does not connect to the ESP32 or implement the full inventory system.
- `firmware/main.py`: supplied MicroPython prototype, with embedded dashboard and placeholder Wi-Fi credentials.

## Run the existing demo

Requires Python 3. No external packages are required.

From this repository folder:

```sh
python3 simulator/local_server.py
```

Open http://127.0.0.1:5000 in a browser. Stop with Ctrl+C.
If the port is occupied, use `python3 simulator/local_server.py --port 5001`.

## Hardware version

The hardware version runs MicroPython and Microdot on the ESP32, with HX711 DT on GPIO4 and SCK on GPIO5. Hardware-specific code cannot run unchanged in desktop Python. See `firmware/README.md` for prerequisites and current limitations.

Never commit Wi-Fi passwords or private network configuration. Use a separate ignored configuration file and share only placeholders.

## Submission scope

This repository is for source code and instructions. A macOS Apple Silicon executable is planned for final submission only; no executable or packaging setup is included now.
