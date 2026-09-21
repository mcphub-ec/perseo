"""
Perseo — all 5 tools as explicit @mcp.tool() functions.

Perseo's architecture (POST-only, api_key in body, per-call url_servidor)
is incompatible with the generic ToolSpec factory. All tools live here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import server
from app import mcp


@mcp.tool()
async def create_factura(
    registro: List[Dict[str, Any]],
    url_servidor: str | None = None,
    controlexistencia: bool = True,
) -> dict:
    """⚠️ MUTATION — Create an invoice or credit note in Perseo Accounting.

    REQUIRED PARAMETERS:
      registro (list[dict]): Array of invoice objects to insert.
                             Each element: {"facturas": {"tipo": "01", "fecha": "20250130",
                             "clienteid": 123, "forma_pago_empresaid": 1,
                             "detalles": [...], "movimiento": {...}}}

    OPTIONAL PARAMETERS:
      controlexistencia (bool, default=True): Check and decrement stock.

    RETURNS:
      {"success": True/False, "facturaid": int, "mensaje": str}
    """
    payload = {"controlexistencia": controlexistencia, "registro": registro}
    return await server._perseo_request("/facturas_crear", payload, url_servidor=url_servidor)


@mcp.tool()
async def query_facturas(
    facturaid: Optional[str] = None,
    dias: Optional[str] = None,
    generarpdf: bool = False,
    url_servidor: str | None = None,
) -> dict:
    """Search and retrieve invoices from Perseo by ID or recent date range.

    OPTIONAL PARAMETERS:
      facturaid (str): Internal Perseo invoice ID.
      dias (str): Number of past days to retrieve. Example: "30"
      generarpdf (bool, default=False): Returns Base64 PDF if True.

    RETURNS:
      List or dict of invoice objects.
    """
    payload: Dict[str, Any] = {"generarpdf": generarpdf}
    if facturaid:
        payload["facturaid"] = facturaid
    if dias:
        payload["dias"] = dias
    return await server._perseo_request("/facturas_consulta", payload, url_servidor=url_servidor)


@mcp.tool()
async def create_producto(
    registros: List[Dict[str, Any]],
    url_servidor: str | None = None,
) -> dict:
    """⚠️ MUTATION — Add one or more new products to the Perseo product catalog.

    REQUIRED PARAMETERS:
      registros (list[dict]): Array of product objects:
                              [{"productos": {"codigo": "PROD-001", "nombre": "...",
                              "codigoiva": 2, "pvp": 10.50, "costo": 7.00}}]

    RETURNS:
      {"success": True/False, "productosid": int, "mensaje": str}
    """
    return await server._perseo_request("/productos_crear", {"registros": registros}, url_servidor=url_servidor)


@mcp.tool()
async def update_producto(
    registros: List[Dict[str, Any]],
    url_servidor: str | None = None,
) -> dict:
    """⚠️ MUTATION — Update one or more existing products in the Perseo catalog.

    REQUIRED PARAMETERS:
      registros (list[dict]): Array with productosid (REQUIRED) + fields to update:
                              [{"productos": {"productosid": 1234, "pvp": 12.50}}]

    RETURNS:
      {"success": True/False, "mensaje": str}
    """
    return await server._perseo_request("/productos_editar", {"registros": registros}, url_servidor=url_servidor)


@mcp.tool()
async def query_asientos(
    fechadesde: Optional[str] = None,
    fechahasta: Optional[str] = None,
    codigocontable: Optional[str] = None,
    id: Optional[str] = None,
    url_servidor: str | None = None,
) -> dict:
    """Search accounting journal entries (asientos contables) in Perseo.

    OPTIONAL PARAMETERS:
      fechadesde (str): Start date YYYYMMDD.
      fechahasta (str): End date YYYYMMDD.
      codigocontable (str): Account code from PGCE chart. Example: "1.1.1.01"
      id (str): Specific journal entry ID.

    RETURNS:
      List of journal entries with: id, fecha, glosa, detalles.
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
    return await server._perseo_request("/asientoscontables_consulta", payload, url_servidor=url_servidor)
