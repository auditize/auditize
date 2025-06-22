import uuid

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database.dbm import Base
from auditize.exceptions import ConstraintViolation, UnknownModelException


async def save_sql_model(session: AsyncSession, model: Base) -> None:
    session.add(model)
    try:
        await session.commit()
    except IntegrityError as exc:
        raise ConstraintViolation() from exc
    await session.refresh(model)


async def get_sql_model[T: Base](
    session: AsyncSession, model_class: type[T], model_id: uuid.UUID
) -> T:
    model = await session.get(model_class, model_id)
    if not model:
        raise UnknownModelException(
            f"Resource {model_class.__name__} with ID {str(model_id)!r} not found."
        )
    return model


async def delete_sql_model[T: Base](
    session: AsyncSession, model_class: type[T], model_id: uuid.UUID
) -> None:
    query = delete(model_class).where(model_class.id == model_id)
    result = await session.execute(query)
    await session.commit()
    if result.rowcount == 0:
        raise UnknownModelException(
            f"Resource {model_class.__name__} with ID {str(model_id)!r} not found."
        )
