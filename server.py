"""
Perseo MCP Server
=================
MCP server bridging the Perseo Accounting Software API (Ecuador).

All tools communicate via POST requests to the Perseo REST API.
"""

from config import HTTP_TIMEOUT, logger  # noqa: F401
from app import mcp  # noqa: F401
from _http import _perseo_request, _json  # noqa: F401

# All 5 tools live in custom.py (POST-only architecture, api_key in body)
import tools.custom  # noqa: F401, E402

__all__ = ["mcp", "_perseo_request", "_json", "logger"]
