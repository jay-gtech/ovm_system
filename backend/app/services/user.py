import uuid
from typing import Optional, Sequence
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.uow import BaseUnitOfWork
from app.services.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
)


class UserService:
    async def create_user(
        self, uow: BaseUnitOfWork, *, user_in: UserCreate
    ) -> User:
        """
        Create a new user within the current tenant scope.
        """
        async with uow:
            # Check if user already exists in this tenant
            existing_user = await uow.users.get_by_email(uow.session, email=user_in.email)
            if existing_user:
                raise ConflictDomainError(
                    f"User with email {user_in.email} already exists in this organization."
                )

            obj_data = user_in.model_dump(exclude={"password"})
            obj_data["hashed_password"] = get_password_hash(user_in.password)
            
            user = await uow.users.create(uow.session, obj_in=obj_data)
            await uow.commit()
            return user

    async def get_user(self, uow: BaseUnitOfWork, user_id: uuid.UUID) -> User:
        """
        Get user by ID within current tenant scope.
        """
        async with uow:
            user = await uow.users.get(uow.session, id=user_id)
            if not user:
                raise NotFoundDomainError(f"User with id {user_id} not found.")
            return user

    async def list_users(
        self, uow: BaseUnitOfWork, *, skip: int = 0, limit: int = 100
    ) -> Sequence[User]:
        """
        List users within current tenant scope.
        """
        async with uow:
            return await uow.users.get_multi(uow.session, skip=skip, limit=limit)

    async def update_user(
        self, uow: BaseUnitOfWork, *, user_id: uuid.UUID, user_in: UserUpdate
    ) -> User:
        """
        Update user within current tenant scope.
        """
        async with uow:
            user = await uow.users.get(uow.session, id=user_id)
            if not user:
                raise NotFoundDomainError(f"User with id {user_id} not found.")
            
            update_data = user_in.model_dump(exclude_unset=True)
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
            user = await uow.users.update(uow.session, db_obj=user, obj_in=update_data)
            await uow.commit()
            return user
