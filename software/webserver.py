import asyncio
from typing import TypedDict

from microdot import Microdot, send_file
from microdot.websocket import websocket_upgrade
import json
import pathlib
from env import env

app = Microdot()


try:
    assert __file__
except Exception:
    __file__ = "webserver.py"


templates_dir = pathlib.Path(__file__).parent / "templates"


@app.route("/")
def home(request):
    return send_file(str(templates_dir / "index.html"))


class Message(TypedDict):
    x: float
    y: float
    z: float
    rot: float


@app.route("/ws")
async def ws(request):
    ws = await websocket_upgrade(request)
    print("WebSocket client connected.")
    while True:
        try:
            data = await ws.receive()
            msg = Message(json.loads(data))
            print(
                f"Received command: x={msg['x']:.2f}, y={msg['y']:.2f}, z={msg['z']:.2f}, rot={msg['rot']:.2f}"
            )
        except Exception as e:
            print(f"WebSocket connection closed: {e}")
            break
    print("WebSocket client disconnected.")


def connect_to_wifi(ssid, password):
    import network  # pyright: ignore[reportMissingImports]
    import time

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    max_wait = 10
    print("Connecting to Wi-Fi...")
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError("Wi-Fi connection failed!")
    else:
        status = wlan.ifconfig()
        print("IP address:", status[0])
        return status[0]


async def main():
    if env["WLAN"] is not None:
        try:
            ip = connect_to_wifi(env["WLAN"]["SSID"], env["WLAN"]["PASSWORD"])
        except RuntimeError as e:
            print(f"Error: {e}")
            return
        server = asyncio.create_task(app.start_server(host=ip, port=80))
    else:
        server = asyncio.create_task(app.start_server(port=5000))
    await server


if __name__ == "__main__":
    asyncio.run(main())
# sudo uvicorn main:app --host 0.0.0.0 --port 80
