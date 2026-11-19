import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models import Category, User

DEFAULT_CATEGORIES = ("Food", "Transport", "Rent", "Entertainment", "Utilities", "Healthcare", "Shopping", "Other")


async def seed() -> None:
    # Convenient for first local startup. Production schema changes should use Alembic.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        for name in DEFAULT_CATEGORIES:
            existing = await db.scalar(select(Category).where(Category.name == name, Category.is_default.is_(True)))
            if existing is None:
                db.add(Category(name=name, is_default=True, user_id=None))
        demo = await db.scalar(select(User).where(User.email == "demo@example.com"))
        if demo is None:
            db.add(User(email="demo@example.com", full_name="Demo User", hashed_password=hash_password("demo-password-change-me")))
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
