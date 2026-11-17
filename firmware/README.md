For the people who like forking, (and are especially new GitHub users),

## Do not commit actual Wi-Fi credentials. 

# ESP32 firmware

`main.py` is a prototype. Won't be the best. 

## Requirements

- ESP32-C6 with MicroPython (user reports version 1.29.0).
- Microdot installed on the board; its exact installed version is not yet recorded. Third-party library source is not bundled here. Project: https://github.com/miguelgrinberg/microdot
- HX711: DT to GPIO4, SCK to GPIO5, compatible 3.3 V supply and common ground; connected load cell.



## Current limitations

- Automatically tares on EVERY startup: keep the scale empty (or with only the empty container). Existing stock would otherwise be treated as zero. This is not yet restart-safe inventory storage.
- Calibration factor is the earlier experimental value and should be verified for the mounting.
- Five-reading moving average is not a stability acceptance rule.
- No product persistence, transaction history, authentication or executable packaging is implemented here.
- Desktop simulator is a separate fixed-data demo, not yet shared firmware logic.
- Syntax checking on a Mac does not verify hardware or MicroPython runtime behaviour.

## How to Set up: 
- Configure credentials locally, and set `UNIT_WEIGHT_G` to the measured mass of one identical item to enable quantity estimates.
- Download Microdot, and
-  Connect the ESP32 to your laptop/device that has an IDE.
- Run this in the terminal to find the ESP's modem port. ls /dev/cu.* # This will be useful in the next step.
- Run command: python -m mpremote connect (ESP32's USB Modem port) fs cp main.py :main.py
- Run another command in the terminal: python -m mpremote connect (The ESP32's USB modem port) run main.py
- The program prints its HTTP address after connecting to Wi-Fi.
- Enjoy.

