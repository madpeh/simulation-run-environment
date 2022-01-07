from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.exceptions import SimulationException
from src.models import CreateSimulation, InstanceStatus
from src.settings import backup_settings, instance_settings
from src.state import state

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_ROUTERS", "INFO"))

router = APIRouter()


@router.post("/simulation", status_code=201)
async def create_simulation(simulation_data: CreateSimulation):
    logger.debug(f"Creating simulation, state: {state.get_state()}")
    try:
        state.start_simulation_process(
            simulation_data.agent_code_lines, simulation_data.agent_data
        )
    except SimulationException as e:
        raise HTTPException(400, str(e))


@router.delete("/simulation")
async def delete_simulation():
    logger.debug(f"Deleting simulation, state: {state.get_state()}")
    try:
        state.kill_simulation_process()
    except SimulationException as e:
        raise HTTPException(400, str(e))


@router.post("/simulation/agent_data", status_code=201)
async def backup_agent_data(body: Dict[Any, Any]):
    logger.debug(f"Backup from agent: {body['jid']}")
    agent_data = {"instance_id": instance_settings.id, "agent_data": body}
    async with httpx.AsyncClient() as client:
        await client.post(backup_settings.api_backup_url, json=agent_data)


@router.post("/instance/status", status_code=201)
async def update_instance_status(instance_status: InstanceStatus):
    logger.debug(f"Update instance state: {instance_status}")
    try:
        state.update_running_state(
            instance_status.status,
            instance_status.num_agents,
            instance_status.num_alive_agents,
        )
    except SimulationException as e:
        raise HTTPException(400, str(e))
