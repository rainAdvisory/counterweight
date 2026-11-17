"""ChatGPT's attempt at a sim."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

EMPTY_READING = -685478.0
COUNTS_PER_GRAM = -1668.83

# Demonstration values, not measurements of actual inventory.
UNIT_WEIGHT_G = 10.0
SIMULATED_ITEMS = 3

PAGE = """<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inventory local test</title>
</head>
<body>
  <h1>Inventory dashboard</h1>
  <p>SIMULATED DATA — no ESP32 connected</p>
  <p>Weight: <strong id="weight">--</strong></p>
  <p>Estimated quantity: <strong id="quantity">--</strong></p>
  <p id="status">Loading...</p>
  <script>
    async function refresh() {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const response = await fetch('/api/status', {
          cache: 'no-store', signal: controller.signal
        });
        if (!response.ok) throw new Error('Request failed');
        const data = await response.json();
        document.getElementById('weight').textContent =
          data.weight_g.toFixed(1) + ' g';
        document.getElementById('quantity').textContent = data.quantity;
        document.getElementById('status').textContent =
          'Connected to local simulation';
      } catch (error) {
        document.getElementById('weight').textContent = '--';
        document.getElementById('quantity').textContent = '--';
        document.getElementById('status').textContent = 'Server unavailable';
      } finally {
        clearTimeout(timeout);
        setTimeout(refresh, 2000);
      }
    }
    refresh();
  </script>
</body>
</html>"""


def status():
    simulated_raw = (
        EMPTY_READING
        + SIMULATED_ITEMS * UNIT_WEIGHT_G * COUNTS_PER_GRAM
    )
    weight = (simulated_raw - EMPTY_READING) / COUNTS_PER_GRAM
    quantity = max(0, int(weight / UNIT_WEIGHT_G + 0.5))
    return {
        'simulated': True,
        'raw': simulated_raw,
        'weight_g': weight,
        'quantity': quantity,
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            self.respond(200, PAGE.encode('utf-8'), 'text/html; charset=utf-8')
        elif path == '/api/status':
            self.respond(200, json.dumps(status()).encode('utf-8'),
                         'application/json')
        else:
            self.respond(404, b'Not found', 'text/plain')

    def respond(self, code, body, content_type):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    try:
        server = HTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as error:
        raise SystemExit(
            f'Cannot start server: {error}\n'
            'Try: python3 local_server.py --port 5001'
        )
    print(f'Open http://127.0.0.1:{args.port}', flush=True)
    print('Offline simulation only. Press Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
    finally:
        server.server_close()
