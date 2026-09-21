"""
Perseo HTTP client module.

Perseo's API differs from the other MCPs:
- All requests are POST (even queries).
- api_key is injected into the request body.
- url_servidor is a per-call hostname with SSRF guard.
- Errors raise RuntimeError (not return {"error": ...}).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

from config import HTTP_TIMEOUT, logger


def _resolve_api_key() -> str:
    resolved = os.getenv("PERSEO_API_KEY", "")
    if not resolved:
        raise ValueError("PERSEO_API_KEY env var is required. Configure it in your .env file.")
    return resolved


def _resolve_base_url(url_servidor: str | None) -> str:
    resolved = url_servidor or os.getenv("PERSEO_URL_SERVIDOR", "")
    if not resolved:
        raise ValueError(
            "Perseo url_servidor is required (e.g. 'perseo-data-c1.app'). "
            "Pass `url_servidor` as a tool parameter."
        )
    if "/" in resolved or " " in resolved:
        raise ValueError(f"url_servidor inválido: {resolved!r}")
    if not re.match(r"^[a-z0-9][a-z0-9.\-]*\.(app|com|ec|net|io|local)$", resolved):
        raise ValueError(
            f"url_servidor {resolved!r} no es un hostname válido. "
            "Solo se aceptan dominios públicos (app, com, ec, net, io, local)."
        )
    return f"https://{resolved}/api"


async def _perseo_request(path: str, payload: dict, *, url_servidor: str | None) -> dict:
    """POST to the Perseo API, injecting api_key into the body."""
    resolved_key = _resolve_api_key()
    base_url = _resolve_base_url(url_servidor)
    url = f"{base_url}{path}"
    payload["api_key"] = resolved_key

    logger.info("→ POST %s", url)

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
    except httpx.ConnectError as exc:
        raise RuntimeError(f"Cannot connect to Perseo API ({url}). Detail: {exc}") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"Timeout connecting to Perseo API ({url}). Detail: {exc}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Unexpected HTTP error contacting Perseo API: {exc}") from exc

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


def _json(result: Any) -> str:
    return json.dumps(result, ensure_ascii=False, default=str)
