import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import AsyncSessionLocal

router = APIRouter()

MAX_POLLS = 300  # Fix #11: 10 min timeout (300 * 2s)


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
        for _ in range(MAX_POLLS):
            from app.models.planejamento import Planejamento
            from app.models.pipeline_log import PipelineLog

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Planejamento).where(Planejamento.id == plan_uuid)
                )
                planejamento = result.scalar_one_or_none()

                if planejamento:
                    logs_result = await session.execute(
                        select(PipelineLog)
                        .where(PipelineLog.planejamento_id == plan_uuid)
                        .order_by(PipelineLog.created_at)
                    )
                    logs = logs_result.scalars().all()

                    # Fix #3: Send format compatible with frontend
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
        else:
            await websocket.close(code=4008)  # timeout
            return

    except WebSocketDisconnect:
        pass
