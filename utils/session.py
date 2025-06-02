from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from utils.db_utils import DATABASE_URL


def get_session_id(request: Request) -> str:
    session_id = getattr(request.state, "session_id", None)
    if not session_id:
        raise HTTPException(400, detail="Session ID is missing")
    return session_id


async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=50,
    max_overflow=20,
    pool_recycle=3600
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=True,
    info=None
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


