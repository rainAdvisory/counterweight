import network
import time
import asyncio
from machine import Pin, disable_irq, enable_irq
from microdot import Microdot

# Replace placeholders
# --- !!NEVER COMMIT REAL NETWORK CREDENTIALS!!! --- 
SSID = "~~"
PASSWORD = "~~"
EMPTY_READING = -685478
COUNTS_PER_GRAM = -1668.83
# Set to the measured mass of one identical item. 
# For further details, open README.md (firmware)
UNIT_WEIGHT_G = None  


dt = Pin(4, Pin.IN)
sck = Pin(5, Pin.OUT, value=0)
app = Microdot()
latest_weight = None
last_read_ms = None
samples = []


def read_raw():
    if dt.value() == 1:
        return None
    value = 0
    irq_state = disable_irq()
    try:
        for _ in range(24):
            sck.value(1)
            time.sleep_us(1)
            value = (value << 1) | dt.value()
            sck.value(0)
            time.sleep_us(1)
        # Channel A, gain 128.
        sck.value(1)
        time.sleep_us(1)
        sck.value(0)
    finally:
        sck.value(0)
        enable_irq(irq_state)
    if value & 0x800000:
        value -= 16777216
    return value


async def sample_sensor():
    global latest_weight, last_read_ms
    while True:
        raw = read_raw()
        if raw is not None:
            now = time.ticks_ms()
            if (last_read_ms is not None
                    and time.ticks_diff(now, last_read_ms) > 2000):
                samples.clear()
            samples.append(raw)
            if len(samples) > 5:
                samples.pop(0)
            average_raw = sum(samples) / len(samples)
            latest_weight = (average_raw - EMPTY_READING) / COUNTS_PER_GRAM
            last_read_ms = now
        await asyncio.sleep_ms(20)


PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inventory dashboard</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 600px;
      margin: 50px auto;
      padding: 20px;
    }
    .value { font-size: 2rem; font-weight: bold; }
  </style>
</head>
<body>
  <h1>Inventory dashboard</h1>
  <p>Net weight</p>
  <div id="weight" class="value">--</div>
  <p>Estimated quantity</p>
  <div id="quantity" class="value">--</div>
  <p id="status">Connecting...</p>
  <script>
    async function refresh() {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 5000);
      try {
        const response = await fetch('/api/status', {
          cache: 'no-store', signal: controller.signal
        });
        if (!response.ok) throw new Error('Request failed');
        const data = await response.json();
        document.getElementById('weight').textContent =
          data.weight_g === null ? '--' : data.weight_g.toFixed(1) + ' g';
        document.getElementById('quantity').textContent =
          data.quantity === null ? '--' : data.quantity;
        document.getElementById('status').textContent =
          !data.sensor_ok
            ? 'Sensor unavailable or readings stale'
            : !data.unit_weight_set
              ? 'Live weight — set unit weight to calculate quantity'
              : 'Live estimate — not yet stability-validated';
      } catch (error) {
        document.getElementById('weight').textContent = '--';
        document.getElementById('quantity').textContent = '--';
        document.getElementById('status').textContent = 'Cannot reach ESP32';
      } finally {
        clearTimeout(timer);
        setTimeout(refresh, 2000);
      }
    }
    refresh();
  </script>
</body>
</html>
"""


@app.route("/")
async def dashboard(request):
    return PAGE, 200, {"Content-Type": "text/html"}


@app.route("/api/status")
async def status(request):
    age = (None if last_read_ms is None
           else time.ticks_diff(time.ticks_ms(), last_read_ms))
    sensor_ok = age is not None and age <= 2000
    unit_weight_set = UNIT_WEIGHT_G is not None and UNIT_WEIGHT_G > 0
    weight = latest_weight if sensor_ok else None
    quantity = None
    if weight is not None and unit_weight_set:
        quantity = max(0, int(weight / UNIT_WEIGHT_G + 0.5))
    return {
        "weight_g": weight,
        "quantity": quantity,
        "sensor_ok": sensor_ok,
        "unit_weight_set": unit_weight_set,
        "measurement_age_ms": age,
    }, 200, {"Cache-Control": "no-store"}


async def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    if not wifi.isconnected():
        wifi.connect(SSID, PASSWORD)
        start = time.ticks_ms()
        while not wifi.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 20000:
                wifi.disconnect()
                raise RuntimeError("Wi-Fi connection timed out")
            await asyncio.sleep_ms(250)
    print("http://" + wifi.ifconfig()[0])
    return wifi


async def tare_scale():
    global EMPTY_READING
    print("Keep the scale empty and still. Zeroing in 2 seconds...")
    await asyncio.sleep_ms(2000)
    readings = []
    start = time.ticks_ms()
    while len(readings) < 20:
        raw = read_raw()
        if raw is not None:
            readings.append(raw)
        if time.ticks_diff(time.ticks_ms(), start) > 5000:
            raise RuntimeError("Cannot zero: HX711 not responding")
        await asyncio.sleep_ms(20)
    EMPTY_READING = sum(readings) / len(readings)
    print("Scale zeroed. You can now add items.")


async def main():
    # !!PROTOTYPE!! empty the scale before EVERY startup.
    await tare_scale()
    sensor_task = asyncio.create_task(sample_sensor())
    try:
        wifi = await connect_wifi()
        await app.start_server(host="0.0.0.0", port=80)
    finally:
        sensor_task.cancel()


asyncio.run(main())
