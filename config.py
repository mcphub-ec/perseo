"""Perseo MCP Server — configuration module."""

import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "name":"%(name)s", "message":"%(message)s"}',
)
logger = logging.getLogger("perseo-mcp")

HTTP_TIMEOUT: float = 30.0
