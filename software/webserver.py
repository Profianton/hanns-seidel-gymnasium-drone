from typing import Annotated
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, responses
from fastapi.templating import Jinja2Templates
import pathlib

from pydantic import BaseModel, Field, ValidationError

# Initialize FastAPI
app = FastAPI(redirect_slashes=False)

# Define the templates directory path
# This looks for a folder named 'templates' in the same directory as main.py
templates_dir = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=templates_dir)


@app.get("/")
def redirect():
    return responses.RedirectResponse("/home")


@app.get("/home")
def home(request: Request):
    """
    Serves the main page using the Jinja2 template.
    The status code is 200 OK for a successful page load.
    """
    return templates.TemplateResponse(request, "index.html")


class Message(BaseModel):
    x: Annotated[float, Field(ge=-1, le=1)]
    y: Annotated[float, Field(ge=-1, le=1)]
    z: Annotated[float, Field(ge=-1, le=1)]
    rot: Annotated[float, Field(ge=-1, le=1)]


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            cmd = Message.model_validate(await websocket.receive_json())
            print(cmd)
    except WebSocketDisconnect:
        pass
    except ValidationError:
        await websocket.close()


# sudo uvicorn main:app --host 0.0.0.0 --port 80
