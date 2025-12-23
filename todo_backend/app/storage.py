import os
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from .models import Base, TodoDB, TodoCreate, TodoResponse, TodoUpdate

namespace = os.getenv('POD_NAMESPACE', 'default')
logger = logging.getLogger(f"{namespace}-todo-backend")



# Globals
engine: AsyncEngine | None = None
AsyncSessionLocal: sessionmaker | None = None

def get_required_env(var_name: str, default: str = None) -> str:
    """Check if env var exists, log status, return value or default"""
    if var_name in os.environ:
        value = os.environ[var_name]
        logger.info(f"{var_name}={value}")
        return value
    else:
        logger.warning(f"{var_name} MISSING - using default: {default}")
        return default or ""

def build_db_url() -> str:
    namespace = get_required_env("POD_NAMESPACE", "undefined")
    host = get_required_env("DB_HOST", "undefined")
    port = int(get_required_env("DB_PORT", "1111"))
    db = get_required_env("POSTGRES_DB", "undefined")
    user = get_required_env("POSTGRES_USER", "undefined")
    password = get_required_env("POSTGRES_PASSWORD", "")
    url = f"postgresql+asyncpg://{user}:{password}@{namespace}-{host}:{port}/{db}"
    logger.info("storage.py: Final DB URL: %s", url)
    return url

async def init_db():
    """Create tables on startup with graceful retries."""
    global engine, AsyncSessionLocal

    if engine is not None and AsyncSessionLocal is not None:
        return

    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    # logger.info("storage.py: Database tables created")
    db_url = build_db_url()
    engine = create_async_engine(
        db_url,
        echo=False,        # THIS SUPPRESSES ALL SQL LOGS
        echo_pool=False,   # NO pool logs
        future=True
    )
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )

    max_retries = 3
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database ready!")
            return # success - normal startup
        except Exception as e:
            # avoid f-strings in log calls so interpolation is lazy)
            #logger.warning(f"Database Table Creation: Attempt {attempt+1}/{max_retries} failed: {e}")
            logger.warning(
                "Database Table Creation: Attempt %d/%d failed: %s",
                attempt + 1, max_retries, e,
            )
            #if attempt == max_retries - 1:
                # No raise after last attempt in startup context to avoid crash
                # raise
                # App continues to run;
                # later readiness probe `/todos/healthz` returns 503 if db still didn't comeup
            await asyncio.sleep(retry_delay)

    # After all retries, log and give up, but DO NOT crash the app
    logger.error("Database not ready after max retries; continuing without DB")

async def get_db_session() -> AsyncSession:
    if AsyncSessionLocal is None:
        raise RuntimeError("AsyncSessionLocal is not initialized. Call init_db() first.")    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_todos(db: AsyncSession) -> list[TodoResponse]:
    result = await db.execute(select(TodoDB).order_by(TodoDB.created_at.desc()))
    todos = result.scalars().all()
    return [TodoResponse.model_validate(todo) for todo in todos]

async def create_todo(db: AsyncSession, todo: TodoCreate) -> TodoResponse:
    db_todo = TodoDB(text=todo.text)
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return TodoResponse.model_validate(db_todo)

async def get_todo(db: AsyncSession, todo_id: int) -> TodoDB:
    """Return ORM TodoDB instance or raise."""
    result = await db.execute(select(TodoDB).where(TodoDB.id == todo_id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise ValueError(f"Todo {todo_id} not found")
    return todo

async def update_todo(db: AsyncSession, todo_id: int, update_data: TodoUpdate) -> TodoResponse:
    # Get ORM instance
    todo = await get_todo(db, todo_id)

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(todo, field, value)

    await db.commit()
    await db.refresh(todo)

    return TodoResponse.model_validate(todo)

async def delete_todo(db: AsyncSession, todo_id: int) -> bool:
    result = await db.execute(select(TodoDB).where(TodoDB.id == todo_id))
    todo = result.scalar_one_or_none()
    if not todo:
        return False
    await db.delete(todo)
    await db.commit()
    return True
