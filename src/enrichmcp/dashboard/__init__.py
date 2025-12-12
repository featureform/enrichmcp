"""EnrichMCP Dashboard - Web-based monitoring and management interface.

This module provides a Streamlit-based dashboard for monitoring EnrichMCP applications,
including entities, tools, connections, and performance metrics.
"""

from .app import DashboardApp
from .data.models import ConnectionInfo, EntityInfo, MetricSnapshot, ToolInfo

__all__ = ["ConnectionInfo", "DashboardApp", "EntityInfo", "MetricSnapshot", "ToolInfo"]
