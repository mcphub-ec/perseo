# **Documentación API Perseo Software para Servidor MCP**

Esta documentación técnica detalla el funcionamiento de la API REST de Perseo Software Contable (Ecuador), diseñada para ser utilizada como referencia en la creación de un servidor Model Context Protocol (MCP).

## **1\. Arquitectura y Configuración Base**

* **URL Base (Perseo Web):** https://{url\_servidor}/api/ (Ejemplo: https://perseo-data-c1.app/api/)  
* **URL Base (Perseo PC):** https://{ip\_publica\_servidor}:{puerto}/api/  
* **Métodos HTTP:** **TODOS los endpoints utilizan el método POST**, independientemente de si la operación es de lectura (consulta), creación o edición. El nombre de la acción va en la URL (ej. /facturas\_crear o /facturas\_consulta).

### **Autenticación (¡IMPORTANTE\!)**

A diferencia de las APIs REST tradicionales, Perseo **no utiliza cabeceras (Headers)** como Authorization para validar la sesión.

El api\_key **debe inyectarse obligatoriamente en el cuerpo (Body JSON)** de cada petición.

{  
  "api\_key": "TU\_CLAVE\_API\_AQUI",  
  "...": "..."  
}

## **2\. Especificación de Endpoints Principales**

La API divide sus operaciones agregando sufijos a las entidades como \_crear, \_editar o \_consulta.

### **Módulo: Facturación (/facturas\_crear, /facturas\_consulta)**

**Crear Factura / Nota de Crédito (POST /facturas\_crear)**

* Inserta una nueva factura o nota de crédito.  
* El campo sri\_documentoscodigo define el tipo: "01" para Factura, "04" para Nota de Crédito.  
* Requiere relacionar catálogos internos (IDs preexistentes de clientes, formas de pago, almacenes, centros de costos).  
* La estructura del cuerpo es anidada: Contiene un arreglo registro que incluye el encabezado (facturas), los ítems (detalles) y la forma de pago (movimiento).

**Consultar Facturas (POST /facturas\_consulta)**

* Retorna el historial o una factura específica.  
* Parámetros de filtro en el body: dias (historial hacia atrás) o facturaid (específica).  
* Soporta el flag generarpdf: true para obtener la representación impresa en Base64/URL.

### **Módulo: Productos / Inventario (/productos\_crear, /productos\_editar)**

**Crear / Editar Producto (POST /productos\_crear y POST /productos\_editar)**

* Permite sincronizar el catálogo de artículos.  
* Requiere especificar impuestos (sri\_tipos\_ivas\_codigo), líneas de negocio y tarifas (precios).  
* Las tarifas (precios múltiples) se envían como un arreglo dentro del objeto producto indicando márgenes y precios con/sin IVA.

### **Módulo: Contabilidad (/asientoscontables\_consulta)**

**Consultar Asientos Contables (POST /asientoscontables\_consulta)**

* Devuelve los asientos contables generados en el sistema Perseo.  
* Parámetros de filtro: fechadesde, fechahasta, codigocontable, id.

*(Nota arquitectónica: Los módulos de Clientes, Proveedores, Cobros y Pagos siguen exactamente el mismo patrón de diseño: /clientes\_crear, /pagos\_consulta, etc.)*

## **3\. Reglas de Negocio Críticas para el MCP**

1. **Gestión de Ceros y Nulls:** Perseo usa valores enteros (0 o 1\) y booleanos (true/false) para el control de inventarios (controlnegativos, servicio).  
2. **Impuestos (IVA):** Se definen mediante códigos del SRI. 2 para 12/15%, 0 para 0%, 6 para No Objeto.  
3. **Manejo de Respuestas:** Al consultar una factura, se puede requerir la llave control para saber si hay productos compuestos. La respuesta del SRI (autorizacionfecha, numeroautorizacion) vendrá en los nodos de facturas si fue enviada a la entidad gubernamental.