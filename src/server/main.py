from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .config_loader import load_config 

# Create the FastAPI application instance
app = FastAPI()

# Load the configuration from the config file
config = load_config(Path("config/adam.yaml")) # Use the path to your main config file

# Mount the StaticFiles directory using the configuration values
# The `html=True` flag tells FastAPI to serve index.html by default
app.mount("/", StaticFiles(directory="src/ui", html=True), name="static")

# Add a redirect for the root URL
# @app.get("/api/data")
# async def get_data():
#    return {"message": "This is an API endpoint"}
