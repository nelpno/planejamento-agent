import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse
from app.services import cliente_service

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.post("", response_model=ClienteResponse, status_code=201)
async def create_cliente(
    data: ClienteCreate,
    session: AsyncSession = Depends(get_session),
):
    cliente = await cliente_service.create_cliente(session, data.model_dump(exclude_none=True))
    return cliente


@router.get("", response_model=list[ClienteResponse])
async def list_clientes(session: AsyncSession = Depends(get_session)):
    return await cliente_service.get_clientes(session)


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(
    cliente_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    cliente = await cliente_service.get_cliente(session, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def update_cliente(
    cliente_id: uuid.UUID,
    data: ClienteUpdate,
    session: AsyncSession = Depends(get_session),
):
    cliente = await cliente_service.update_cliente(
        session, cliente_id, data.model_dump(exclude_none=True)
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.delete("/{cliente_id}", status_code=204)
async def delete_cliente(
    cliente_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await cliente_service.delete_cliente(session, cliente_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
