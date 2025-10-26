import json
from pydantic import BaseModel
from env import env
from webserver import Message
from inputs import get_gamepad
import threading
import time
import websockets
import asyncio


class ControllerState(BaseModel):
    class Stick(BaseModel):
        x: float
        y: float

    left_stick: Stick
    right_stick: Stick

    class Triggers(BaseModel):
        left: float
        right: float

    triggers: Triggers


class Controller:
    def __init__(self):
        self.left_stick_x = 0.0
        self.left_stick_y = 0.0
        self.right_stick_x = 0.0
        self.right_stick_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0
        self.running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_controller, args=()
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _monitor_controller(self):
        while self.running:
            try:
                events = get_gamepad()
                for event in events:
                    if event.ev_type == "Absolute":
                        if event.code == "ABS_X":
                            self.left_stick_x = self._normalize_stick(event.state)
                        elif event.code == "ABS_Y":
                            self.left_stick_y = self._normalize_stick(event.state)
                        elif event.code == "ABS_RX":
                            self.right_stick_x = self._normalize_stick(event.state)
                        elif event.code == "ABS_RY":
                            self.right_stick_y = self._normalize_stick(event.state)
                        elif event.code == "ABS_Z":
                            self.left_trigger = self._normalize_trigger(event.state)
                        elif event.code == "ABS_RZ":
                            self.right_trigger = self._normalize_trigger(event.state)
            except Exception as e:
                print(f"Controller error: {str(e)}")
                time.sleep(1)  # Wait before retrying

    def _normalize_stick(self, value):
        return value / 32768.0  # Convert to range -1.0 to 1.0

    def _normalize_trigger(self, value):
        return value / 255.0  # Convert to range 0.0 to 1.0

    def get_state(self):
        return ControllerState(
            left_stick=ControllerState.Stick(x=self.left_stick_x, y=self.left_stick_y),
            right_stick=ControllerState.Stick(
                x=self.right_stick_x, y=self.right_stick_y
            ),
            triggers=ControllerState.Triggers(
                left=self.left_trigger, right=self.right_trigger
            ),
        )

    def stop(self):
        self.running = False
        self._monitor_thread.join()


async def websocket_client(controller: Controller):
    """
    Connects to the WebSocket server and sends controller state updates.
    This function should be run in a separate thread using asyncio.
    """
    assert env["WSURI"]
    while controller.running:
        try:
            async with websockets.connect(env["WSURI"]) as websocket:
                print("Connected to WebSocket server")
                while controller.running:
                    state = controller.get_state()
                    # Map controller values to drone controls:
                    # Left stick Y: forward/backward (-1 to 1)
                    # Left stick X: left/right strafe (-1 to 1                    # Right stick X: rotation (-1 to 1)

                    # Right stick Y: up/down (-1 to 1)
                    message = Message(
                        {
                            "x": state.left_stick.x,
                            "y": -state.left_stick.y,
                            "z": state.right_stick.y,
                            "rot": state.right_stick.x,
                        }
                    )
                    await websocket.send(json.dumps(message))
                    await asyncio.sleep(0.05)  # Send updates at 20Hz
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            await asyncio.sleep(1)  # Wait before retrying


def run_controller_with_websocket():
    """
    Creates a controller instance and runs it with WebSocket communication.
    This function handles all the threading and asyncio setup.
    """
    controller = Controller()
    ws_thread = threading.Thread(
        target=asyncio.run, args=(websocket_client(controller),)
    )
    ws_thread.daemon = True
    ws_thread.start()

    return controller, ws_thread


controller, ws_thread = run_controller_with_websocket()
ws_thread.join()
