import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Fallback to SQLite if PostgreSQL URL fails or is local default
db_url = settings.assemble_db_url()
if not os.getenv("DATABASE_URL") and "postgresql" in db_url:
    # Use SQLite for reliable zero-config async local database operation
    db_url = "sqlite+aiosqlite:///./ire_local.db"

engine = create_async_engine(
    db_url,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        import app.infrastructure.db.models.auth_models
        import app.infrastructure.db.models.hospital
        import app.infrastructure.db.models.tenant
        import app.infrastructure.db.models.audit_log
        import app.infrastructure.db.models.claim
        await conn.run_sync(Base.metadata.create_all)
