import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import AsyncSessionLocal

router = APIRouter()


@router.websocket("/ws/planejamento/{planejamento_id}")
async def planejamento_websocket(websocket: WebSocket, planejamento_id: str):
    """WebSocket endpoint that streams planning pipeline status updates."""
    await websocket.accept()

    try:
        plan_uuid = uuid.UUID(planejamento_id)
    except ValueError:
        await websocket.close(code=4000)
        return

    try:
        while True:
            from app.models.planejamento import Planejamento

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Planejamento).where(Planejamento.id == plan_uuid)
                )
                planejamento = result.scalar_one_or_none()

                if planejamento:
                    # Get pipeline logs
                    from app.models.pipeline_log import PipelineLog
                    logs_result = await session.execute(
                        select(PipelineLog)
                        .where(PipelineLog.planejamento_id == plan_uuid)
                        .order_by(PipelineLog.created_at)
                    )
                    logs = logs_result.scalars().all()

                    status_data = {
                        "status": planejamento.status,
                        "pipeline_logs": [
                            {
                                "agent_name": log.agent_name,
                                "iteration": log.iteration,
                                "decision": log.decision,
                                "reasoning": log.reasoning,
                                "duration_ms": log.duration_ms,
                                "created_at": log.created_at.isoformat() if log.created_at else None,
                            }
                            for log in logs
                        ],
                        "pipeline_duration": planejamento.pipeline_duration,
                    }
                    await websocket.send_json(status_data)

                    if planejamento.status in ("revisao", "aprovado", "failed"):
                        break

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        pass
