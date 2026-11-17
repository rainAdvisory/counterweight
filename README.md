# Counterweight

Robotics Club weight-based inventory project using an ESP32-C6, HX711 and load cell.

<img width="534" height="438" alt="image" src="https://github.com/user-attachments/assets/096df94e-e93c-4000-8662-566218890465" />


## Current repository contents

- `simulator/local_server.py`: existing standalone Python demonstration with fixed simulated readings (30 g, 3 items). It does not connect to the ESP32 or implement the full inventory system. (Planned PhET Sim executable later.)

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

(Don't run, it is still in progress.)


## Submission scope

This repository is for source code and instructions. Nothing crazy— A macOS Apple Silicon executable is planned for final submission only; no executable or packaging setup is included at this time.
