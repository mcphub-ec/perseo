"""Perseo FastMCP application instance."""

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Perseo",
    host=os.getenv("MCP_HOST", "0.0.0.0"),  # nosec B104
    instructions=(
        "MCP server for Perseo Accounting Software (Ecuador). "
        "Provides tools to create and query invoices (facturas), manage products "
        "in the catalog, and query accounting journal entries (asientos contables). "
        "api_key is loaded from PERSEO_API_KEY env var. Pass `url_servidor` per call. "
        "Date format for ALL date fields: YYYYMMDD (e.g. '20250130'). "
        "Document types: '01'=Invoice (Factura), '04'=Credit Note (Nota de Crédito). "
        "VAT codes (codigoiva): 2=15%, 0=0%."
    ),
)
