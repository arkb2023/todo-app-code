import logging
import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager


# 1. CONFIGURE LOGGING FIRST
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

# Suppress noise from other libraries
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)
namespace = os.getenv('POD_NAMESPACE', 'default')
logger = logging.getLogger(f"{namespace}-todo-backend")

# Local app code inherit the logging config set above
from .storage import init_db, engine
from .routes import todos


# 2. CREATE APP FIRST
app = FastAPI(title="Todo API")

# 3. ADD EXCEPTION HANDLERS (NOW app exists)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "todo_validation_failed",
        extra={
            "endpoint": request.url.path,
            "method": request.method,
            "error": exc.errors()[0]["msg"],
            "input_length": len(str(exc.errors()[0].get("input", ""))),
            "status": "rejected_422"
        }
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("todo_http_error", extra={"status_code": exc.status_code})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# 4. LIFESPAN & MIDDLEWARE
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()

app.router.lifespan_context = lifespan  # FastAPI v0.100+

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. ADD ROUTERS LAST
app.include_router(todos.router)

# 6. ROOT ENDPOINTS
@app.get("/")
async def root():
    return {"message": "Todo API is running"}

@app.get("/test")
async def test():
    return {"status": "ok"}


# Run with: uvicorn app.main:app --reload

# Code files:
# app/
#   main.py
#   models.py: # Models: Todo defines the todo data schema.
# storage.py
# routes/todos.py
# models.py

# Supported Endpoints:
# GET /todos:
# Handler: app/routes/todos.py:get_todos
# Returns: app/storage.py:todo_list

# POST /todos:
# Handler: app/routes/todos.py:create_todo
# Input: Pydantic validates incoming todo JSON body against app/models.py:Todo
# Store:  Add todo to storage
#   Calls storage.py:add_todo to add new todo to in-memory list.
# Return: 201 Created JSON response on success.
