import network
import time
import asyncio
from machine import Pin, disable_irq, enable_irq
from microdot import Microdot

# -- settings -- 
SSID = "WIFI NAME"
PASSWORD = "YOUR WIFI's PASSWORD HERE"

EMPTY_READING = -685478
COUNTS_PER_GRAM = -1668.83
# replace unit_weight with the recorded mass of one item. (fyi, do this for an uno.)
UNIT_WEIGHT_G = 50

dt = Pin(4, Pin.IN)
sck = Pin(5, Pin.OUT, value=0)

app = Microdot()

latest_weight = None
last_read_ms = None
samples = []


# hx711 reading 
def read_raw():
    # return immediately if the sensor is not ready
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

            # discard old samples after a sensor interruption (error-handling )
            if (
                last_read_ms is not None
                and time.ticks_diff(now, last_read_ms) > 2000
            ):
                samples.clear()

            samples.append(raw)

            # take the avg from the latest five readings.
            if len(samples) > 5:
                samples.pop(0)

            average_raw = sum(samples) / len(samples)
            latest_weight = (
                average_raw - EMPTY_READING
            ) / COUNTS_PER_GRAM

            last_read_ms = now

        # Let the server handle requests between checks.
        await asyncio.sleep_ms(20)


# -- webpage --
PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inventory dashboard</title>
  <style>
    /* Base */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #111;
  color: #fff;
  font-family: Arial, sans-serif;
}

.dashboard {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}

h1 {
  margin: 0;
  font-size: 28px;
}

h2 {
  margin: 0 0 16px;
  font-size: 20px;
}

/* Summary cards */
.summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.card {
  padding: 20px;
  border-radius: 20px;
  background: #980d0d;
}

.label {
  margin: 0 0 12px;
  font-size: 14px;
}

.value {
  margin: 0;
  font-size: 32px;
  font-weight: bold;
  overflow-wrap: anywhere;
}

/* Product and activity panels */
.content {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.panel {
  padding: 24px;
  border-radius: 20px;
  background: #242424;
}

.activity {
  border-top: 5px solid #ff794d;
}

.detail,
.transaction {
  padding: 12px 0;
  border-bottom: 1px solid #555;
}

.detail {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.empty-message,
.timestamp {
  color: #ccc;
  font-size: 14px;
}

/* Status text */
.status {
  font-size: 14px;
  font-weight: bold;
}

.online,
.in-stock {
  color: #8be59b;
}

.low-stock {
  color: #ffd479;
}

.offline {
  color: #ffb0b0;
}

/* Product settings form */
label {
  display: block;
  margin-bottom: 6px;
}

input,
select {
  width: 100%;
  min-width: 0;
  padding: 12px;
  margin-bottom: 16px;
  border: 1px solid #777;
  border-radius: 8px;
  background: #161616;
  color: #fff;
  font: inherit;
}

button {
  min-height: 44px;
  padding: 12px 18px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: #980d0d;
  color: #fff;
  font: inherit;
  font-weight: bold;
  cursor: pointer;
}

button.secondary {
  background: #383838;
  border-color: #777;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
a:focus-visible {
  outline: 3px solid #ffd479;
  outline-offset: 3px;
}

.error {
  color: #ffb0b0;
}

[hidden] {
  display: none !important;
}

@media (max-width: 600px) {
  .dashboard {
    padding: 16px;
  }

  .summary,
  .content {
    grid-template-columns: 1fr;
  }
}
  </style>
</head>
<body>
  <main class="dashboard">
  <header class="header">
    <h1>COUNTERWEIGHT</h1>
  </header>

  <p id="status" class="status">Connecting...</p>

  <section class="summary">
    <div class="card">
      <p class="label">Net weight</p>
      <p id="weight" class="value">--</p>
    </div>

    <div class="card">
      <p class="label">Estimated quantity</p>
      <p id="quantity" class="value">--</p>
    </div>

    <div class="card">
      <p class="label">Stock status</p>
      <p class="value">Not configured</p>
    </div>
  </section>

  <section class="content">
    <div class="panel">
      <h2>Current inventory</h2>
      <p>Product X</p>
      <p class="empty-message">
        I haven't considered a specific product yet.
      </p>
    </div>

    <div class="panel activity">
      <h2>Activity</h2>
      <p class="empty-message">
        Not yet.
      </p>
    </div>
  </section>
</main>
<script>
  async function refresh() {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch('/api/status', {
        cache: 'no-store',
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error('Request failed');
      }

      const data = await response.json();

      document.getElementById('weight').textContent =
        data.weight_g === null
          ? '--'
          : data.weight_g.toFixed(1) + ' g';

      document.getElementById('quantity').textContent =
        data.quantity === null ? '--' : data.quantity;

      document.getElementById('status').textContent =
        !data.sensor_ok
          ? 'Sensor unavailable or readings stale'
          : !data.unit_weight_set
            ? 'Live weight - set unit weight to calculate quantity'
            : 'Live estimate - not yet stability-validated';

    } catch (error) {
      document.getElementById('weight').textContent = '--';
      document.getElementById('quantity').textContent = '--';
      document.getElementById('status').textContent =
        'Cannot reach ESP32';

    } finally {
      clearTimeout(timer);
      setTimeout(refresh, 2000);
    }
  }

  refresh();
</script>
</body>
</html>
  </script>
</body>
</html>
"""


@app.route("/")
async def dashboard(request):
    return PAGE, 200, {"Content-Type": "text/html"}


@app.route("/api/status")
async def status(request):
    age = (
        None if last_read_ms is None
        else time.ticks_diff(time.ticks_ms(), last_read_ms)
    )

    sensor_ok = age is not None and age <= 2000
    unit_weight_set = (
        UNIT_WEIGHT_G is not None and UNIT_WEIGHT_G > 0
    )

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


# Wifi + Startup
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
    # zero before starting continuous measurements
    await tare_scale()

    sensor_task = asyncio.create_task(sample_sensor())

    try:
        wifi = await connect_wifi()
        await app.start_server(host="0.0.0.0", port=80)
    finally:
        sensor_task.cancel()


asyncio.run(main())


