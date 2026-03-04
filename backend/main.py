import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="Multi-Agent System")

app.include_router(router)