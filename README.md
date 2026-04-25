# Perseo MCP Server

Servidor oficial de integración con la API de Perseo (Ecuador) a través del estándar Model Context Protocol (MCP). Configurado para ser usado en plataformas como OpenWebUI o herramientas locales de agentes mediante `HTTP Streamable` en el puerto `8005`.

## Características
- Todas las interacciones inyectan silenciosamente la `api_key` como lo requiere la arquitectura técnica de Perseo.
- Peticiones siempre ejecutadas por método `POST`, abstraídas a llamados semánticamente correctos de herramientas (`create_factura`, `query_facturas`, etc.).
- Respeta estrictamente los requerimientos de la Especificación de la API de Perseo (OpenAPI 3.0).

## Instalación y Configuración

```bash
# 1. Copiar archivo de entorno y configurar
cp .env.example .env

# EDITA .env con tu entorno:
# PERSEO_API_KEY=tu_clave_secreta_aqui
# PERSEO_URL_SERVIDOR=perseo-data-c1.app

# 2. Instalar las dependencias (dentro de un venv o global si eres persistente)
pip install -r ../requirements.txt  # Asumiendo que comparten un requirements
# O manualmente: pip install mcp httpx python-dotenv uvicorn

# 3. Iniciar el Servidor
python server.py
```

## Herramientas Ofertadas
1. **`create_factura`**: Genera facturas (código "01") y notas de crédito.
2. **`query_facturas`**: Busca facturas mediante filtros.
3. **`create_producto`**: Inserta catálogos nuevos.
4. **`update_producto`**: Modifica configuraciones de inventario ya existentes.
5. **`query_asientos`**: Chequeo de estados financieros y entradas contables.
# perseo
