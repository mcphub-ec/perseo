"""
Perseo MCP Server v2.0.0
────────────────────────
Model Context Protocol (MCP) server bridging the Perseo Accounting Software
API (Ecuador). All tools communicate via POST requests to the Perseo REST API.

Transport: Streamable HTTP  →  POST/GET/DELETE  http://<host>:8005/mcp

MULTI-ACCOUNT SUPPORT (v2.0)
  Every tool accepts `api_key` and `url_servidor` as explicit parameters.
  This allows the agent to operate on different client accounts without
  changing environment variables:
    - api_key (str): Perseo API key for the specific account.
    - url_servidor (str): Perseo server hostname, e.g. "perseo-data-c1.app"
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()


# ─────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "name":"%(name)s", "message":"%(message)s"}',
)
logger = logging.getLogger("perseo-mcp")

HTTP_TIMEOUT = 30.0

# ─────────────────────────────────────────────────────────────────────
# MCP Server
# ─────────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "Perseo",
    host="0.0.0.0",
    instructions=(
        "MCP server for Perseo Accounting Software (Ecuador). "
        "Provides tools to create and query invoices (facturas), manage products "
        "in the catalog, and query accounting journal entries (asientos contables). "
        "api_key is loaded from PERSEO_API_KEY env var. Pass `url_servidor` per call. "
        "Date format for ALL date fields: YYYYMMDD (e.g. '20250130'). "
        "Document types: '01'=Invoice (Factura), '04'=Credit Note (Nota de Crédito). "
        "VAT codes (codigoiva): 2=15%, 0=0%."
    ))


# ─────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────

def _resolve_api_key() -> str:
    """Return the Perseo API key from environment."""
    resolved = os.getenv("PERSEO_API_KEY", "")
    if not resolved:
        raise ValueError(
            "PERSEO_API_KEY env var is required. Configure it in your .env file."
        )
    return resolved


def _resolve_base_url(url_servidor: str) -> str:
    """Build the Perseo API base URL from the provided server hostname."""
    resolved = url_servidor or os.getenv("PERSEO_URL_SERVIDOR", "")
    if not resolved:
        raise ValueError(
            "Perseo url_servidor is required (e.g. 'perseo-data-c1.app'). "
            "Pass `url_servidor` as a tool parameter."
        )
    return f"https://{resolved}/api"


async def _perseo_request(path: str, payload: dict, *, url_servidor: str) -> dict:
    """
    Execute a POST request to the Perseo API.
    Injects `api_key` into the request body automatically.
    """
    resolved_key = _resolve_api_key()
    base_url = _resolve_base_url(url_servidor)

    url = f"{base_url}{path}"
    payload["api_key"] = resolved_key

    logger.info("→ POST %s", url)

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"})
    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"Cannot connect to Perseo API ({url}). "
            f"Check network connectivity and url_servidor. Detail: {exc}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(
            f"Timeout connecting to Perseo API ({url}). "
            f"Request exceeded {HTTP_TIMEOUT}s. Detail: {exc}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Unexpected HTTP error contacting Perseo API: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        status = response.status_code
        detail = (
            f"Error ({status}) calling Perseo {path}. "
            f"Response: {json.dumps(error_body, ensure_ascii=False) if isinstance(error_body, dict) else error_body}"
        )
        logger.error("← POST %s → %d: %s", url, status, detail)
        raise RuntimeError(detail)

    data = response.json()
    logger.info("← POST %s → %d OK", url, response.status_code)
    return data


# ─────────────────────────────────────────────────────────────────────
# MCP Tools
# ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def create_factura(    url_servidor: str,
    registro: List[Dict[str, Any]],
    controlexistencia: bool = True) -> dict:
    """⚠️ MUTATION — Create an invoice or credit note in Perseo Accounting.

    Use this tool to record a new sale document into Perseo.
    Supported types: '01' = Invoice (Factura), '04' = Credit Note (Nota de Crédito).

    REQUIRED PARAMETERS:
      url_servidor (str): Perseo server hostname. Example: "perseo-data-c1.app"
      registro (list[dict]): Array of invoice objects to insert.
                             Each element must follow this structure:
                             [{"facturas": {
                                 "tipo": "01",              # "01"=Invoice, "04"=Credit Note
                                 "fecha": "20250130",       # Date in YYYYMMDD format
                                 "clienteid": 123,          # Client ID in Perseo
                                 "forma_pago_empresaid": 1, # Payment method ID
                                 "detalles": [...],         # Line items array
                                 "movimiento": {...}        # Inventory movement info
                             }}]

    OPTIONAL PARAMETERS:
      controlexistencia (bool, default=True): If True, system checks and decrements
                                              stock on each sale line item.

    RETURNS:
      {"success": True/False, "facturaid": int, "mensaje": str}

    EXAMPLE CALL:
      create_factura(api_key="xxx", url_servidor="perseo-data-c1.app",
                     registro=[{"facturas": {"tipo": "01", "fecha": "20250130", ...}}])
    """
    payload = {
        "controlexistencia": controlexistencia,
        "registro": registro,
    }
    return await _perseo_request("/facturas_crear", payload, url_servidor=url_servidor)


@mcp.tool()
async def query_facturas(    url_servidor: str,
    facturaid: Optional[str] = None,
    dias: Optional[str] = None,
    generarpdf: bool = False) -> dict:
    """Search and retrieve invoices from Perseo by ID or recent date range.

    Use this tool to look up a specific invoice by its internal ID, or to
    retrieve recent invoice history for the last N days.
    At least one filter (facturaid or dias) is recommended.

    REQUIRED PARAMETERS:
      url_servidor (str): Perseo server hostname. Example: "perseo-data-c1.app"

    OPTIONAL PARAMETERS:
      facturaid (str): Internal Perseo invoice ID to fetch a specific document.
                       Example: "12345"
      dias (str): Number of past days to retrieve history from.
                  Example: "30" to get invoices from the last 30 days.
      generarpdf (bool, default=False): If True, returns a Base64-encoded PDF
                                        of each document.

    RETURNS:
      List or dict of invoice objects. Fields include: facturaid, tipo, fecha,
      clienteid, total, estado. If generarpdf=True, includes a Base64 PDF attachment.

    EXAMPLE CALLS:
      query_facturas(api_key="xxx", url_servidor="perseo-data-c1.app", dias="30")
      query_facturas(api_key="xxx", url_servidor="perseo-data-c1.app", facturaid="12345", generarpdf=True)
    """
    payload: Dict[str, Any] = {"generarpdf": generarpdf}
    if facturaid:
        payload["facturaid"] = facturaid
    if dias:
        payload["dias"] = dias

    return await _perseo_request("/facturas_consulta", payload, url_servidor=url_servidor)


@mcp.tool()
async def create_producto(    url_servidor: str,
    registros: List[Dict[str, Any]]) -> dict:
    """⚠️ MUTATION — Add one or more new products to the Perseo product catalog.

    Use this tool to create new products or services in Perseo.

    REQUIRED PARAMETERS:
      url_servidor (str): Perseo server hostname. Example: "perseo-data-c1.app"
      registros (list[dict]): Array of product objects to create.
                              Each element must follow this structure:
                              [{"productos": {
                                  "codigo": "PROD-001",      # Unique product code
                                  "nombre": "Product Name",  # Product display name
                                  "codigoiva": 2,            # VAT code: 2=15%, 0=0%
                                  "pvp": 10.50,              # Retail sale price
                                  "costo": 7.00,             # Cost/purchase price
                                  "linea": "Electronics"     # Product line or category
                              }}]

    RETURNS:
      {"success": True/False, "productosid": int, "mensaje": str}

    EXAMPLE CALL:
      create_producto(api_key="xxx", url_servidor="perseo-data-c1.app",
                      registros=[{"productos": {"codigo": "PROD-001", "nombre": "Laptop",
                                                "codigoiva": 2, "pvp": 950.00}}])
    """
    payload = {"registros": registros}
    return await _perseo_request("/productos_crear", payload, url_servidor=url_servidor)


@mcp.tool()
async def update_producto(    url_servidor: str,
    registros: List[Dict[str, Any]]) -> dict:
    """⚠️ MUTATION — Update one or more existing products in the Perseo catalog.

    Use this tool to modify product fields such as price, name, or VAT code.
    The field productosid is MANDATORY inside each product object.

    REQUIRED PARAMETERS:
      url_servidor (str): Perseo server hostname. Example: "perseo-data-c1.app"
      registros (list[dict]): Array of product objects to update.
                              Each element MUST include productosid:
                              [{"productos": {
                                  "productosid": 1234,       # REQUIRED: Internal Perseo ID
                                  "nombre": "Updated Name",  # Fields to update
                                  "pvp": 12.50               # New sale price
                              }}]
                              Error if productosid is missing: "productosid is required".

    RETURNS:
      {"success": True/False, "mensaje": str}

    EXAMPLE CALL:
      update_producto(api_key="xxx", url_servidor="perseo-data-c1.app",
                      registros=[{"productos": {"productosid": 1234, "pvp": 12.50}}])
    """
    payload = {"registros": registros}
    return await _perseo_request("/productos_editar", payload, url_servidor=url_servidor)


@mcp.tool()
async def query_asientos(    url_servidor: str,
    fechadesde: Optional[str] = None,
    fechahasta: Optional[str] = None,
    codigocontable: Optional[str] = None,
    id: Optional[str] = None) -> dict:
    """Search accounting journal entries (asientos contables) in Perseo.

    Use this tool to retrieve accounting entries within a date range, by
    account code from Ecuador's standard chart of accounts (PGCE), or by ID.

    REQUIRED PARAMETERS:
      url_servidor (str): Perseo server hostname. Example: "perseo-data-c1.app"

    OPTIONAL PARAMETERS:
      fechadesde (str): Start date in YYYYMMDD format. Example: "20250101"
      fechahasta (str): End date in YYYYMMDD format. Example: "20250131"
      codigocontable (str): Account code from the PGCE chart of accounts.
                            Example: "1.1.1.01" for a cash account.
      id (str): Specific journal entry ID auto-generated by Perseo.

    RETURNS:
      List of journal entries. Each entry includes: id, fecha, glosa (description),
      and detalles (list with cuenta_id, centro_costo_id, tipo D/H, valor).

    EXAMPLE CALLS:
      query_asientos(api_key="xxx", url_servidor="perseo-data-c1.app",
                     fechadesde="20250101", fechahasta="20250131")
      query_asientos(api_key="xxx", url_servidor="perseo-data-c1.app",
                     codigocontable="1.1.1.01")
    """
    payload: Dict[str, Any] = {}
    if fechadesde:
        payload["fechadesde"] = fechadesde
    if fechahasta:
        payload["fechahasta"] = fechahasta
    if codigocontable:
        payload["codigocontable"] = codigocontable
    if id:
        payload["id"] = id

    return await _perseo_request("/asientoscontables_consulta", payload, url_servidor=url_servidor)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_PORT", 8000))
    transport_mode = os.getenv("MCP_TRANSPORT_MODE", "sse").lower()
    print(f"Starting Perseo MCP Server on http://0.0.0.0:{port}/mcp ({transport_mode})")
    if transport_mode == "sse":
        app = mcp.sse_app()
    elif transport_mode == "http_stream":
        app = mcp.streamable_http_app()
    else:
        raise ValueError(f"Unknown transport mode: {transport_mode}")
    uvicorn.run(app, host="0.0.0.0", port=port)
