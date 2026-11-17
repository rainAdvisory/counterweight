# ESP32 firmware

`main.py` is the user's supplied prototype, with paste escaping removed and formatting cleaned. Hardware behaviour is preserved. Wi-Fi credentials remain placeholders.

## Requirements

- ESP32-C6 with MicroPython (user reports version 1.29.0).
- Microdot installed on the board; its exact installed version is not yet recorded. Third-party library source is not bundled here. Project: https://github.com/miguelgrinberg/microdot
- HX711: DT to GPIO4, SCK to GPIO5, compatible 3.3 V supply and common ground; connected load cell.

Configure credentials locally, and set `UNIT_WEIGHT_G` to the measured mass of one identical item to enable quantity estimates. Do not commit actual credentials. Copy the program to the board as `main.py` along with its required Microdot dependency. The program prints its HTTP address after connecting to Wi-Fi.

## Current limitations

- Automatically tares on EVERY startup: keep the scale empty (or with only the empty container). Existing stock would otherwise be treated as zero. This is not yet restart-safe inventory storage.
- Calibration factor is the earlier experimental value and should be verified for the mounting.
- Five-reading moving average is not a stability acceptance rule.
- No product persistence, transaction history, authentication or executable packaging is implemented here.
- Desktop simulator is a separate fixed-data demo, not yet shared firmware logic.
- Syntax checking on a Mac does not verify hardware or MicroPython runtime behaviour.
