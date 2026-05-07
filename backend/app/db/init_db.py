import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.base import Base
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.core.config import settings

async def init_db():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Create Organization
        org_stmt = select(Organization).where(Organization.slug == "ovm")
        result = await session.execute(org_stmt)
        org = result.scalar_one_or_none()
        
        if not org:
            org = Organization(
                name="OVM System",
                slug="ovm"
            )
            session.add(org)
            await session.flush()
            print(f"Created Organization: {org.name} (slug: {org.slug})")
        else:
            print(f"Organization already exists: {org.name}")

        # 2. Create Admin User
        user_stmt = select(User).where(User.email == "admin@ovm.com")
        result = await session.execute(user_stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email="admin@ovm.com",
                hashed_password=get_password_hash("password"),
                full_name="System Admin",
                organization_id=org.id,
                is_superuser=True
            )
            session.add(user)
            await session.flush()
            print(f"Created Admin User: {user.email}")
        else:
            print(f"Admin User already exists: {user.email}")

        await session.commit()

if __name__ == "__main__":
    asyncio.run(init_db())
