import logging
from fastapi import (
    FastAPI,
)
from fastapi.middleware.cors import CORSMiddleware
from utils.infrastructure.error import install_exception_handlers

app = FastAPI(
    title="Document Service", servers=[{"url": "/"}]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("app")
install_exception_handlers(app, logger)

@app.get("/hello")
def hello():
    return "Hello world"
