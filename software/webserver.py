from fastapi import FastAPI, Request, responses
from fastapi.templating import Jinja2Templates
import pathlib

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


# sudo uvicorn main:app --host 0.0.0.0 --port 80
