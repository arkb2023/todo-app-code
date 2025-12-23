import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import frontend

# 1. CONFIGURE LOGGING FIRST
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

namespace = os.getenv("POD_NAMESPACE", "default")
logger = logging.getLogger(f"{namespace}-todo-frontend")

app = FastAPI(lifespan=frontend.lifespan)

# Mount static directory to serve JS/CSS files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize templates pointing to your templates directory
templates = Jinja2Templates(directory="app/templates")

# Include routers (you may pass templates as dependency or import inside routes)
app.include_router(frontend.router)
