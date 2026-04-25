# Guía para Agentes - Perseo MCP Server

Este documento sirve como referencia de sistema para agentes de IA que integran y ejecutan herramientas contra el Servidor MCP de Perseo.

## Convenciones Estrictas de Perseo
- **Autenticación (Invisible):** La lógica del servidor MCP inyecta automáticamente el parámetro requerido `"api_key"` en el payload. Como Agente, NUNCA necesitas solicitar un token de Perseo al usuario para inyectarlo.
- **Fechas:** Perseo utiliza el estándar `YYYYMMDD` (ej: `20241231`) en lugar de ISO-8601 con guiones. Nunca envíes formatos separados por `-` o `/`.
- **Estructura Anidada:** APIs como `/productos_crear` o `/facturas_crear` utilizan un encapsulamiento extraño donde envías una llave base. Ejemplo en productos (el parámetro `registros`):
  ```json
  [
    {"productos": { "productocodigo": "A1", "descripcion": "Prod 1" }}
  ]
  ```
  El mismo patrón con `facturas` para facturación.
- **Modificar (Update):** En Perseo, la modificación (ej: `update_producto`) REQUIERE obligatoriamente el envío del ID interno (`productosid`) dentro del payload que envías para actualizar. Siempre realiza un GET previo si no sabes el ID numérico de Perseo.

## Herramientas Disponibles

### `create_factura`
- Entrada: `registro`, `controlexistencia`.
- Nota: Las transacciones requieren mapeo de catálogos foráneos (IDs de clientes, cajas, vendedores, SRI = "01" o "04").

### `query_facturas`
- Consulta unánime por `facturaid`, o histórico de la cantidad de `dias`. Concede retornar representaciones base64 mandando `generarpdf=True`.

### `create_producto` & `update_producto`
- Mantenimiento principal del catálogo. Los códigos de IVA de SRI comúnmente son: `2` (Activo 12/15%), `0` (IVA 0%).

### `query_asientos`
- Consulta contable. Usa `fechadesde` y `fechahasta` (YYYYMMDD).
