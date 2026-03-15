import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente


async def create_cliente(session: AsyncSession, data: dict) -> Cliente:
    cliente = Cliente(**data)
    session.add(cliente)
    await session.flush()
    return cliente


async def get_clientes(session: AsyncSession) -> list[Cliente]:
    result = await session.execute(
        select(Cliente).order_by(Cliente.nome_empresa)
    )
    return list(result.scalars().all())


async def get_cliente(session: AsyncSession, cliente_id: uuid.UUID) -> Cliente | None:
    result = await session.execute(
        select(Cliente).where(Cliente.id == cliente_id)
    )
    return result.scalar_one_or_none()


async def update_cliente(session: AsyncSession, cliente_id: uuid.UUID, data: dict) -> Cliente | None:
    cliente = await get_cliente(session, cliente_id)
    if not cliente:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(cliente, key, value)
    await session.flush()
    return cliente


async def delete_cliente(session: AsyncSession, cliente_id: uuid.UUID) -> bool:
    cliente = await get_cliente(session, cliente_id)
    if not cliente:
        return False
    await session.delete(cliente)
    return True
