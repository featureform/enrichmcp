"""Data models for the EnrichMCP Dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class EntityInfo:
    """Information about a registered entity."""

    name: str
    description: str
    field_count: int
    relationship_count: int
    instance_count: int
    last_accessed: datetime
    fields: dict[str, str]  # field_name -> field_type
    relationships: dict[str, str]  # relationship_name -> target_entity


@dataclass
class ToolInfo:
    """Information about a generated MCP tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    return_type: str
    call_count: int
    avg_latency: float  # milliseconds
    error_rate: float  # percentage
    last_called: datetime | None
    entity_name: str | None  # Associated entity if applicable


@dataclass
class ConnectionInfo:
    """Information about an active MCP connection."""

    client_id: str
    agent_type: str
    connected_at: datetime
    last_activity: datetime
    status: str  # "active", "idle", "disconnected"
    session_count: int
    total_requests: int
    user_agent: str | None


@dataclass
class MetricSnapshot:
    """Performance metrics snapshot."""

    timestamp: datetime
    active_connections: int
    requests_per_second: float
    avg_latency: float  # milliseconds
    error_rate: float  # percentage
    memory_usage: float  # MB
    cpu_usage: float  # percentage
    total_requests: int
    total_errors: int


@dataclass
class ToolCall:
    """Individual tool call record."""

    timestamp: datetime
    tool_name: str
    client_id: str
    parameters: dict[str, Any]
    response_time: float  # milliseconds
    success: bool
    error_message: str | None
    response_size: int  # bytes
