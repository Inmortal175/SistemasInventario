# **Especificaciones Técnicas y QA — Sistema de Inventario Pastelería**

Metodología: **Spec-Driven Development (SDD) & Spec-Driven Testing (SDT)**

Plataforma y Entorno: FastAPI (Python), Next.js, PostgreSQL, Redis y Docker local

Gobernanza de Calidad: SOLID, Clean Code Architecture & Trazabilidad Multiusuario (RBAC)

## **Glosario de Roles y Permisos (RBAC)**

* **SUPERADMIN**: Gestión de cuentas de usuarios, auditoría global de trazabilidad y parametrización de base de datos.  
* **ADMIN**: Creación de categorías, registro de insumos, gestión de ubicaciones, reabastecimientos (ENTRY) y conciliación de ajustes físicos (ADJUSTMENT).  
* **STAFF**: Perfil operativo de cocina (Maestros pasteleros, asistentes, limpieza). Solo puede registrar salidas (EXIT) y mermas (WASTE) de insumos. No tiene acceso a reportes globales ni gestión de ubicaciones.

## **Arquitectura de Datos: Modelo OLTP a Preparación OLAP**

Para garantizar la consistencia en el sistema transaccional (OLTP) y preparar los datos de manera óptima para análisis multidimensionales (OLAP), la base de datos PostgreSQL mantendrá un esquema altamente normalizado, mientras que los endpoints de exportación generarán estructuras planas (vistas de hechos desnormalizadas) listas para procesos ETL.

### **Estructura de Hechos y Dimensiones (Modelo en Estrella \- OLAP Ready)**

* **DimUsers**: id (UUID), email, role, is\_active, created\_at  
* **DimSupplies**: id (UUID), name, category\_name, minimum\_stock  
* **DimLocations**: id (UUID), code, location\_type  
* **FactMovements**: id (UUID), user\_id, supply\_id, location\_id, movement\_type, quantity, stock\_before, stock\_after, timestamp, is\_adjustment, adjustment\_reason

## **HU-01: Creación Dinámica de Categorías**

**Como** Administrador o Superadministrador

**Quiero** crear nuevas categorías de insumos en tiempo real

**Para** clasificar el inventario sin modificar el código base

### **SC-HU01-01 — Creación exitosa**

Dado que no existe categoría con nombre "Colorantes Artificiales"  
  Y el usuario autenticado tiene rol ADMIN  
  Y el payload contiene: name, description, color\_hex, icon\_name  
Cuando realiza POST /api/v1/categories  
Entonces el sistema persiste en PostgreSQL con is\_active=true  
  Y genera slug automático "colorantes-artificiales"  
  Y almacena en Redis con clave "category:{id}" TTL=3600s  
  Y invalida el índice "categories:active:all"  
  Y retorna HTTP 201 con campo "id" (UUID)

### **SC-HU01-02 — Nombre duplicado (cache-first)**

Dado que existe categoría activa "Harinas Especiales" en Redis  
Cuando ADMIN intenta POST con name="Harinas Especiales"  
Entonces el sistema consulta Redis ANTES que PostgreSQL  
  Y retorna HTTP 409 Conflict  
  Y error\_code="CATEGORY\_NAME\_ALREADY\_EXISTS"  
  Y NO inserta ningún registro en PostgreSQL

### **SC-HU01-03 — Denegación a rol STAFF**

Dado que el usuario tiene rol STAFF  
Cuando intenta POST /api/v1/categories con cualquier payload  
Entonces retorna HTTP 403 Forbidden  
  Y error\_code="INSUFFICIENT\_PERMISSIONS"  
  Y el endpoint NO procesa el payload

### **SC-HU01-04 — Redis offline (modo degradado)**

Dado que Redis no está disponible (circuit breaker activo)  
Cuando ADMIN crea categoría "Coberturas Premium"  
Entonces el sistema persiste igualmente en PostgreSQL  
  Y registra warning "REDIS\_UNAVAILABLE: cache write skipped"  
  Y retorna HTTP 201 con header "X-Cache-Status: BYPASS"

### **SC-HU01-05 — Validación de campos obligatorios**

Esquema: campo\_faltante  
  | name      |  
  | color\_hex  |

Dado que el payload no contiene "\<campo\_faltante\>"  
Cuando ADMIN realiza POST /api/v1/categories  
Entonces retorna HTTP 422 Unprocessable Entity  
  Y el body detalla exactamente qué campo falló

## **HU-02: Registro de Consumo de Insumos (STAFF)**

**Como** Personal Usuario (Maestro Pastelero o Limpieza)

**Quiero** registrar el consumo de insumos desde la cocina

**Para** mantener el stock actualizado y generar historial de auditoría

### **SC-HU02-01 — Consumo exitoso sin alerta**

Dado que "Harina de Trigo 000" tiene current\_stock=25.000, minimum=10.000  
  Y el usuario tiene rol STAFF (identificado como user\_id="usr-999")  
Cuando registra EXIT de 5.000 KG con notas "Preparación torta"  
Entonces el sistema aplica lock pesimista sobre el registro  
  Y verifica la expresión matemática: $current\\\_stock \= 25.000 \- 5.000 \= 20.000 \\ge 10.000$ (OK)  
  Y actualiza current\_stock=20.000 (transacción atómica)  
  Y inserta en movement\_history: user\_id="usr-999", stock\_before=25, stock\_after=20, alert\_triggered=false, is\_adjustment=false  
  Y retorna HTTP 201 con alert\_triggered=false

### **SC-HU02-02 — Consumo que activa alerta de stock crítico**

Dado que el insumo tiene current\_stock=12.000, minimum=10.000  
Cuando STAFF registra EXIT de 5.000 KG  
Entonces el sistema calcula el stock resultante: $12.000 \- 5.000 \= 7.000$ (donde $7.000 \< 10.000$)  
  Y actualiza current\_stock=7.000  
  Y inserta en movement\_history con alert\_triggered=true  
  Y publica en el canal de Redis "alerts:low\_stock":  
      { supply\_item\_id, name, current=7.000, minimum=10.000, deficit=3.000 }  
  Y retorna HTTP 201 con header "X-Alert-Triggered: true"

### **SC-HU02-03 — Rechazo por stock insuficiente**

Dado que el insumo tiene current\_stock=3.000  
Cuando STAFF intenta EXIT de 5.000 KG  
Entonces el sistema calcula: $3.000 \- 5.000 \= \-2.000$ (INVÁLIDO por ser $\< 0$)  
  Y retorna HTTP 422 Unprocessable Entity  
  Y error\_code="INSUFFICIENT\_STOCK"  
  Y el body contiene: { available\_stock: 3.000, requested: 5.000 }  
  Y NO modifica current\_stock en PostgreSQL  
  Y NO inserta en movement\_history

## **HU-03: Gestión de Ubicaciones Físicas**

**Como** Administrador o Superadministrador

**Quiero** registrar y administrar ubicaciones físicas rotuladas

**Para** localizar cada insumo dentro del almacén, refrigeradores y estantes

### **SC-HU03-01 — Creación exitosa con normalización de código**

Dado que el usuario autenticado tiene rol ADMIN  
  Y el payload contiene code="est-07-f2", location\_type="SHELF"  
Cuando realiza POST /api/v1/locations  
Entonces el sistema normaliza el código a "EST-07-F2"  
  Y persiste en PostgreSQL con is\_active=true  
  Y retorna HTTP 201 con el campo "id" (UUID)

### **SC-HU03-02 — Código con formato inválido**

Dado que ADMIN envía code="REF-01-F2" (REF no admite sufijo de fila de estante)  
Cuando realiza POST /api/v1/locations  
Entonces el validador del schema rechaza el código  
  Y retorna HTTP 422 con error\_code="VALIDATION\_ERROR"

## **HU-04: Login y Emisión de JWT**

**Como** Usuario registrado

**Quiero** ingresar mis credenciales de acceso

**Para** iniciar sesión de forma segura y obtener mi token de autorización con rol asignado

### **SC-HU04-01 — Inicio de sesión exitoso**

Dado que existe un usuario activo con email "pastelero@pasteleria.com"  
Cuando realiza POST /api/v1/auth/login con credenciales válidas  
Entonces genera un token JWT firmado criptográficamente  
  Y el payload incluye claims: sub (User UUID), email, rol, exp  
  Y retorna HTTP 200 con el token y el perfil

### **SC-HU04-02 — Rate Limiting de seguridad (Redis)**

Dado que el usuario intenta loguearse con contraseña errónea  
Cuando realiza POST /api/v1/auth/login  
Entonces retorna HTTP 401 Unauthorized  
  Y incrementa en Redis el contador "login:rate\_limit:{ip}"  
  Y si intentos fallidos $\\ge 5$ en un lapso de 15 minutos, bloquea la IP por 900s

## **HU-05: Gestión de Ítems de Insumo (CRUD por ADMIN)**

**Como** Administrador

**Quiero** dar de alta, modificar y listar los insumos del negocio

**Para** que estén disponibles para su posterior consumo o abastecimiento

### **SC-HU05-01 — Alta exitosa de insumo**

Dado que el usuario autenticado tiene rol ADMIN  
  Y la categoría con ID "cat-111" está activa  
  Y la ubicación con ID "loc-222" está activa  
  Y el payload contiene name="Esencia de Vainilla", current\_stock=10.000, minimum=2.000  
Cuando realiza POST /api/v1/supplies  
Entonces el sistema valida las relaciones en PostgreSQL  
  Y persiste el insumo con is\_active=true  
  Y retorna HTTP 201 Created

## **HU-06: Listado de Insumos con Filtros y Paginación**

**Como** Cocinero, Pastelero o Administrador

**Quiero** visualizar la lista de insumos disponibles con filtros de categoría y estado

**Para** revisar rápidamente las existencias del local de manera ágil

### **SC-HU06-01 — Búsqueda paginada optimizada (Cache-first)**

Dado que se solicita GET /api/v1/supplies?page=1\&limit=20\&category\_id=cat-111  
  Y la lista paginada de insumos se encuentra indexada en Redis  
Cuando se ejecuta la petición  
Entonces retorna HTTP 200 con la estructura JSON correspondiente de la caché  
  Y retorna el header "X-Cache: HIT"  
  Y calcula internamente el desplazamiento de paginación: $offset \= (page \- 1\) \\times limit$

### **SC-HU06-02 — Invalidación y recarga (Bypass cache en mutaciones)**

Dado que ADMIN acaba de crear un nuevo insumo bajo la categoría "cat-111"  
Cuando un usuario consulta GET /api/v1/supplies?category\_id=cat-111  
Entonces el sistema detecta la mutación previa (caché invalidada por inserción)  
  Y realiza la consulta relacional directamente a PostgreSQL (JOIN supplies \+ locations)  
  Y repuebla la caché de Redis con los nuevos datos paginados  
  Y retorna HTTP 200 con el header "X-Cache: MISS"

## **HU-07: Historial de Movimientos por Insumo (Auditoría)**

**Como** Administrador o Superadministrador

**Quiero** consultar los registros históricos de entradas y salidas de un insumo

**Para** realizar auditorías internas y detectar pérdidas de materiales

### **SC-HU07-01 — Consulta detallada con trazabilidad de usuarios**

Dado que el usuario tiene rol ADMIN  
Cuando realiza GET /api/v1/supplies/{id}/movements?page=1\&limit=50  
Entonces el sistema ejecuta una consulta en PostgreSQL ordenada descendentemente por timestamp  
  Y retorna HTTP 200 con la lista de movimientos que incluye de forma explícita:  
      { movement\_id, type, quantity, stock\_before, stock\_after, executed\_by\_user\_id, user\_email, is\_adjustment, adjustment\_reason, timestamp }

## **HU-08: Dashboard de KPIs en Tiempo Real**

**Como** Administrador o Superadministrador

**Quiero** visualizar métricas clave consolidadas en tiempo real

**Para** tomar decisiones inmediatas sobre compras y mermas en la pastelería

### **SC-HU08-01 — Obtención de KPIs consolidados**

Dado que existen 3 insumos por debajo del stock mínimo  
  Y se han registrado 12 movimientos en las últimas 24 horas  
Cuando el Administrador consulta GET /api/v1/dashboard/kpis  
Entonces retorna HTTP 200 con un resumen consolidado:  
    { total\_critical\_items: 3, movements\_last\_24h: 12, top\_wasted\_supplies: \[\] }  
  Y lee los valores agregados directamente desde Redis (actualizados dinámicamente)

## **HU-09: Reabastecimiento de Insumos (ENTRY por ADMIN)**

**Como** Administrador

**Quiero** registrar el reabastecimiento o ingreso de insumos adquiridos (compras)

**Para** incrementar el stock actual de un insumo de forma controlada

### **SC-HU09-01 — Reabastecimiento exitoso**

Dado que "Fudge de Chocolate" tiene current\_stock=2.000 KG (Stock Crítico)  
  Y el usuario tiene rol ADMIN  
Cuando registra un movimiento de tipo ENTRY por 10.000 KG  
Entonces el sistema aplica una transacción ACID en PostgreSQL  
  Y actualiza current\_stock a 12.000 KG (donde $2.000 \+ 10.000 \= 12.000$)  
  Y escribe en movement\_history indicando alert\_triggered=false  
  Y retorna HTTP 201 con el stock actualizado

## **HU-10: Gestión de Usuarios y Trazabilidad Global (SUPERADMIN)**

**Como** Superadministrador

**Quiero** crear, modificar, suspender cuentas de administradores y staff, y auditar todas sus acciones

**Para** controlar la seguridad informática y la total trazabilidad de responsabilidades en la pastelería

### **SC-HU10-01 — Creación de cuentas con asignación de rol**

Dado que el usuario autenticado tiene el rol SUPERADMIN  
  Y envía un payload con email="nuevo\_admin@pasteleria.com", password="Secure123Password", role="ADMIN"  
Cuando realiza POST /api/v1/users  
Entonces el sistema encripta la contraseña usando Bcrypt  
  Y persiste el usuario en PostgreSQL con is\_active=true  
  Y retorna HTTP 201 con el id, email y role (sin hash de contraseña)

### **SC-HU10-02 — Suspensión lógica de usuario e invalidación de sesión**

Dado que existe un usuario "cocinero\_infractor@pasteleria.com" con rol STAFF y Token JWT activo  
Cuando SUPERADMIN realiza PATCH /api/v1/users/{id}/suspend  
Entonces el sistema actualiza is\_active=false en PostgreSQL  
  Y añade el token del usuario a la Blacklist de tokens en Redis con un TTL igual al tiempo de expiración restante de su JWT  
  Y retorna HTTP 200 OK  
  Y cualquier petición posterior del usuario con ese token será rechazada con HTTP 401 Unauthorized

### **SC-HU10-03 — Trazabilidad: Historial de acciones por usuario**

Dado que SUPERADMIN quiere auditar las modificaciones hechas por el administrador "usr-123"  
Cuando realiza GET /api/v1/users/usr-123/audit-log  
Entonces retorna HTTP 200 con la lista consolidada de todas las mutaciones realizadas por ese usuario:  
  \- Categorías creadas  
  \- Ubicaciones registradas  
  \- Ajustes manuales e ingresos/salidas de inventario detallados

## **HU-11: Conciliación y Ajustes de Inventario por Error Humano (ADMIN/SUPERADMIN)**

**Como** Administrador o Superadministrador

**Quiero** corregir discrepancias físicas y cuadrar el stock del inventario ante errores de registro

**Para** mantener la base de datos alineada con la realidad física del almacén sin alterar la inmutabilidad histórica

### **SC-HU11-01 — Ajuste de stock exitoso por error de registro (Trazable)**

Dado que "Mantequilla Sin Sal" tiene un stock registrado de 15.000 KG  
  Y el Administrador realiza un conteo físico y encuentra que realmente hay 13.500 KG (Diferencia de \-1.500 KG)  
  Y el usuario autenticado es ADMIN (id="admin-555")  
Cuando realiza POST /api/v1/supplies/reconciliation con:  
    { supply\_id: "mant-001", physical\_stock: 13.500, reason: "Error de digitación en el registro de entrada anterior" }  
Entonces el sistema calcula el ajuste matemáticamente:   
    $\\Delta \= physical\\\_stock \- current\\\_stock \= 13.500 \- 15.000 \= \-1.500$  
  Y actualiza current\_stock=13.500 en PostgreSQL mediante una transacción atómica  
  Y escribe en movement\_history un registro de conciliación:  
      { user\_id: "admin-555", type: "ADJUSTMENT", quantity: \-1.500, stock\_before: 15.000, stock\_after: 13.500, is\_adjustment: true, adjustment\_reason: "Error de digitación en el registro de entrada anterior" }  
  Y retorna HTTP 200 OK con el nuevo balance e id de auditoría

### **SC-HU11-02 — Rechazo de ajuste directo por rol STAFF**

Dado que el usuario tiene rol STAFF  
Cuando intenta realizar un ajuste manual en /api/v1/supplies/reconciliation  
Entonces el sistema deniega la petición  
  Y retorna HTTP 403 Forbidden  
  Y error\_code="INSUFFICIENT\_PERMISSIONS"  
  Y NO se modifica el stock de PostgreSQL ni se genera ningún registro

### **SC-HU11-03 — Ajuste que dispara alerta de stock mínimo**

Dado que "Leche Fresca" tiene stock registrado de 20.000 L, con un mínimo requerido de 15.000 L  
Cuando ADMIN realiza un ajuste por merma física y establece el stock en 12.000 L  
Entonces el sistema calcula: $\\Delta \= 12.000 \- 20.000 \= \-8.000$  
  Y actualiza el stock a 12.000 L  
  Y al ser $12.000 \< 15.000$, marca alert\_triggered=true en el log de movimientos  
  Y publica la alerta crítica en Redis "alerts:low\_stock"  
  Y retorna HTTP 200 OK

## **HU-12: Exportación de Reportes Desnormalizados y Preparación OLAP**

**Como** Administrador o Superadministrador

**Quiero** exportar el historial de movimientos e inventarios en formatos planos (CSV, Excel)

**Para** generar informes de rendimiento y facilitar la carga (ETL) a un almacén de datos (OLAP)

### **SC-HU12-01 — Exportación exitosa de datos desnormalizados (Formato OLAP-Ready)**

Dado que ADMIN solicita exportación consolidada en GET /api/v1/reports/export?format=csv\&start\_date=2026-01-01  
Cuando el sistema procesa la solicitud  
Entonces genera una consulta desnormalizada (JOIN supplies \+ categories \+ locations \+ users) para aplanar la estructura en 3NF a un esquema relacional plano  
  Y el archivo CSV resultante contiene exactamente las siguientes columnas listas para ingestión de PowerBI o ClickHouse:  
      \[movement\_id, timestamp, user\_id, user\_role, user\_email, supply\_id, supply\_name, item\_type, category\_name, location\_code, movement\_type, quantity, unit\_cost, total\_cost, stock\_before, stock\_after, is\_adjustment, adjustment\_reason, notes\]  
  Y `item_type` distingue consumo de insumo de producción de producto terminado, y `unit_cost`/`total_cost` habilitan el análisis financiero (HU-16, HU-17)  
  Y retorna un archivo con cabecera HTTP "Content-Disposition: attachment; filename=inventory\_olap\_export.csv"

### **SC-HU12-02 — Restricción de acceso a reportes globales para rol STAFF**

Dado que el usuario autenticado tiene el rol STAFF  
Cuando intenta descargar reportes consolidados en /api/v1/reports/export  
Entonces el sistema rechaza la descarga de forma inmediata  
  Y retorna HTTP 403 Forbidden  
  Y error\_code="INSUFFICIENT\_PERMISSIONS"  


## **HU-13: Control de Lotes y Fechas de Vencimiento (FIFO)**

**Como** Administrador o Personal de Cocina (STAFF)

**Quiero** registrar y despachar insumos controlados por lotes y fechas de vencimiento

**Para** evitar la merma por descomposición y garantizar que los insumos expiren primero sean consumidos antes (FIFO)

### **SC-HU13-01 — Entrada de nuevo lote de insumo perecedero (ADMIN)**

Dado que el usuario autenticado tiene rol ADMIN  
  Y desea registrar una entrada (ENTRY) para "Crema de Leche" (supply\_id="cream-101")  
  Y el payload contiene quantity=50.00, batch\_code="L-CREM-2026-01", expiration\_date="2026-02-15"  
Cuando realiza POST /api/v1/supplies/cream-101/batches  
Entonces el sistema inserta un registro en la tabla "SupplyBatches" con stock\_inicial=50.00, stock\_actual=50.00, y expiration\_date  
  Y recalcula la suma total en PostgreSQL: $current\\\_stock \= \\sum (stock\\\_actual\\ de\\ todos\\ los\\ lotes\\ activos)$  
  Y actualiza "supplies" con la nueva sumatoria de stock total  
  Y retorna HTTP 201 Created con el ID del lote registrado

### **SC-HU13-02 — Consumo automático optimizado por metodología FIFO (STAFF)**

Dado que el insumo "Leche Fresca" cuenta con 2 lotes activos:  
  \- Lote A (Vence: 2026-01-20): stock\_actual \= 10.00 L  
  \- Lote B (Vence: 2026-02-10): stock\_actual \= 20.00 L  
  Y el stock total actual es de 30.00 L  
Cuando STAFF realiza una salida (EXIT) de 15.00 L del insumo  
Entonces el sistema aplica el principio FIFO y consume secuencialmente:  
  \- Consume 10.00 L del Lote A (dejando su stock\_actual \= 0.00 y lote inactivo)  
  \- Consume los 5.00 L restantes del Lote B (dejando su stock\_actual \= 15.00 L)  
  Y actualiza el stock consolidado del insumo a 15.00 L  
  Y registra un solo movimiento físico desglosando la deducción por lotes en auditoría  
  Y retorna HTTP 201 con el desglose del consumo por lote

### **SC-HU13-03 — Alerta predictiva de lotes próximos a vencer (Cron/Background Task)**

Dado que el sistema ejecuta un proceso programado cada 24 horas  
Cuando evalúa la tabla "SupplyBatches" para lotes con $expiration\\\_date \\le (current\\\_date \+ 5\\ días)$  
Entonces publica un mensaje de alerta en Redis canal "alerts:expiration\_critical":  
    { batch\_id: "lote-xyz", supply\_name: "Frutilla Fresca", expiration\_date: "2026-07-13", days\_left: 5 }  
  Y marca en PostgreSQL "alert\_sent=true" para evitar spam de alertas

## **HU-14: Alertas e Inventario en Tiempo Real (WebSockets \+ Redis Pub/Sub)**

**Como** Administrador o Superadministrador

**Quiero** recibir notificaciones visuales instantáneas en mi dashboard cuando ocurra una alerta de stock crítico o de vencimiento

**Para** tomar decisiones de compra o mermas inmediatamente sin recargar manualmente el navegador

### **SC-HU14-01 — Establecimiento de conexión WebSocket con autenticación JWT**

Dado que el usuario tiene una sesión activa con rol ADMIN y posee su token JWT  
Cuando el cliente Frontend Next.js inicia un handshake de WebSockets en /api/v1/ws/notifications?token={jwt}  
Entonces el backend FastAPI decodifica el token, valida los claims y asocia el ID de conexión al grupo de "Administradores"  
  Y responde con un mensaje de bienvenida JSON confirmando la conexión establecida

### **SC-HU14-02 — Difusión en tiempo real de alertas de stock mínimo**

Dado que un Personal Usuario (STAFF) ejecuta una salida (HU-02) que reduce el stock de "Harina" por debajo del mínimo  
  Y el backend publica la alerta de manera atómica en el canal de Redis "alerts:low\_stock"  
Cuando la tarea en background de FastAPI escucha el evento en Redis Pub/Sub  
Entonces retransmite el payload en milisegundos a todas las conexiones activas en el canal WebSocket de Administradores  
  Y el Frontend despliega una notificación emergente visual (Toast) sin requerir llamadas REST adicionales


## **HU-15: Producción Automatizada Basada en Recetas (BOM \- Bill of Materials)**

**Como** Personal de Cocina (STAFF) o Administrador

**Quiero** registrar la producción de un lote de productos finales (ej. "Torta de Tres Leches")

**Para** que el sistema descuente de manera atómica y automática la cantidad exacta de ingredientes según la receta usando FIFO

### **SC-HU15-01 — Simulación y descuento atómico exitoso (Transacción Completa)**

Dado que la receta "Torta Tres Leches (1 Unidad)" requiere:  
  \- 0.50 KG de "Harina de Trigo" (supply\_id="harina-01")  
  \- 1.00 L de "Leche Fresca" (supply\_id="leche-02")  
  Y el stock actual de Harina es 10.00 KG y Leche es 20.00 L  
  Y el usuario con rol STAFF solicita producir 10 Unidades (POST /api/v1/production/produce con {recipe\_id: "rec-3leches", quantity: 10})  
Cuando el backend inicia el proceso en una transacción de PostgreSQL  
Entonces calcula la necesidad total:  
    $Need\_{Harina} \= 0.50 \\times 10 \= 5.00\\text{ KG}$  
    $Need\_{Leche} \= 1.00 \\times 10 \= 10.00\\text{ L}$  
  Y verifica que existan existencias totales suficientes ($10.00 \\ge 5.00$ y $20.00 \\ge 10.00$)  
  Y aplica internamente el algoritmo FIFO (HU-13) descontando lotes secuenciales de harina y leche  
  Y registra la salida en el historial de movimientos  
  Y confirma (COMMIT) la transacción en PostgreSQL  
  Y retorna HTTP 201 Created confirmando el descuento de insumos

### **SC-HU15-02 — Aborto atómico por stock insuficiente de un ingrediente (Rollback)**

Dado que para producir 10 Tortas Tres Leches se requieren 5.00 KG de Harina y 10.00 L de Leche  
  Y en almacén solo se dispone de 10.00 KG de Harina pero únicamente 4.00 L de Leche (Déficit de 6.00 L)  
Cuando STAFF intenta registrar la producción de 10 unidades  
Entonces el validador de stock antes del consumo detecta la insuficiencia de Leche  
  Y detiene de inmediato la operación  
  Y ejecuta un ROLLBACK absoluto en PostgreSQL para que no se descuente ningún gramo de Harina  
  Y retorna HTTP 422 Unprocessable Entity  
  Y error\_code="RECIPE\_PRODUCTION\_FAILED\_STOCK\_SHORTAGE"  
  Y el cuerpo de la respuesta detalla exactamente qué insumo falló: { supply\_id: "leche-02", required: 10.00, available: 4.00 }

## **HU-16: Gestión de Proveedores y Valorización Financiera del Inventario**

**Como** Administrador o Superadministrador

**Quiero** registrar el costo unitario de adquisición de los lotes y asociarlos a un proveedor específico

**Para** conocer el valor financiero real de los activos en el almacén y auditar el impacto monetario de las mermas

### **SC-HU16-01 — Reabastecimiento de Lote con Proveedor y Costo (ADMIN)**

Dado que el Administrador registra un reabastecimiento (ENTRY) de "Crema de Leche" (supply\_id="cream-101")  
  Y el payload contiene: quantity=50.00, batch\_code="L-CREM-2026-01", expiration\_date="2026-02-15", unit\_cost=4.20, vendor\_name="Distribuidora Lácteos Ayacucho"  
Cuando realiza POST /api/v1/supplies/cream-101/batches  
Entonces el sistema persiste el lote con stock\_actual=50.00, unit\_cost=4.20, y vendor\_name  
  Y guarda en PostgreSQL y Redis un movimiento de tipo ENTRY con:  
      { quantity: 50.00, unit\_cost: 4.20, total\_movement\_cost: 50.00 \* 4.20 \= 210.00 }  
  Y retorna HTTP 201 Created

### **SC-HU16-02 — Obtención del Valor Financiero Activo del Almacén**

Dado que existen múltiples lotes activos en el almacén con diferentes cantidades y costos unitarios  
Cuando el Administrador consulta GET /api/v1/dashboard/financials  
Entonces el sistema calcula el valor total de los activos usando la sumatoria ponderada:  
    $$V\_{total} \= \\sum\_{i=1}^{N} (stock\\\_actual\_{i} \\times unit\\\_cost\_{i})$$  
  Y calcula de forma paralela el costo total acumulado por mermas (WASTE) en el periodo de tiempo consultado:  
    $$Loss\_{total} \= \\sum\_{j=1}^{M} (quantity\\\_wasted\_{j} \\times unit\\\_cost\\\_batch\_{j})$$  
  Y retorna HTTP 200 OK con el desglose de los activos valorizados de la pastelería

## **HU-17: Registro de Producción y Stock de Productos Terminados**

**Como** Administrador o Personal de Cocina (STAFF)

**Quiero** que al producir una receta el producto terminado se registre como stock (guardado
en refrigeración) y quede constancia auditable de cada corrida de producción

**Para** poder sostener pedidos de días de alta demanda con producto elaborado por anticipado y
saber en todo momento cuánto se produjo, quién lo produjo y cuándo

### **Contexto de negocio**

La pastelería produce tortas y las **almacena en la refrigeradora** para venderlas después. En
días de alta demanda (p. ej. 100 pedidos de torta de chocolate) no alcanzan a producir en el
momento, pero usan lo producido días antes. Por eso el producto terminado **es inventario**:
tiene stock, ubicación (REF), vencimiento y se descuenta al venderse. Hasta ahora `produce`
descontaba los insumos pero **no dejaba registro de lo producido** — este es el vacío que HU-17
cierra.

### **Modelo**

* Un **producto terminado** es un `supply_item` con `item_type = FINISHED_PRODUCT` (reutiliza
  stock, lotes FIFO, vencimiento, movimientos y valorización de los insumos), pero **no se
  registra como insumo**: se gestiona en su propia sección "Productos terminados" (el listado de
  insumos filtra `item_type = INGREDIENT`).
* La **receta crea automáticamente** su producto terminado: al definir la receta se indica
  `product_name`, `product_location_id` (refrigeradora) y `shelf_life_days`; el sistema da de alta
  el producto (bajo la categoría "Productos terminados") y lo enlaza vía `produces_supply_item_id`.
  No hay que registrarlo por separado.
* Cada producción se asienta en la tabla inmutable `production_runs`.

### **SC-HU17-01 — Producción registra stock de producto terminado y corrida (ADMIN/STAFF)**

Dado que la receta "Torta de Chocolate" fue creada con producto terminado (auto-creado en REF-01,
vida útil 4 días) y sus ingredientes tienen stock suficiente  
  Y el usuario autenticado tiene rol STAFF  
Cuando realiza POST /api/v1/production/produce con { recipe_id, quantity: 10 }  
Entonces el sistema, en una única transacción atómica:  
  \- descuenta los ingredientes por FIFO (registra EXIT por ingrediente)  
  \- crea un lote del producto terminado con stock\_actual=10 y expiration\_date = hoy + 4 días  
  \- incrementa el stock del producto terminado en +10 (movimiento ENTRY)  
  \- inserta un registro en production\_runs: { recipe\_id, product\_supply\_item\_id, quantity\_produced=10, product\_batch\_id, total\_ingredient\_cost, performed\_by, created\_at }  
  Y retorna HTTP 201 con el id de la corrida y el nuevo stock del producto

### **SC-HU17-02 — Consulta del historial de producción**

Dado que se han registrado varias corridas de producción  
Cuando ADMIN consulta GET /api/v1/production/history?page=1\&limit=20  
Entonces retorna HTTP 200 con la lista descendente por fecha, incluyendo por corrida:  
  { production\_id, recipe\_name, product\_name, quantity\_produced, total\_ingredient\_cost, performed\_by\_email, created\_at }

### **SC-HU17-03 — Venta desde el colchón de producción (FIFO por vencimiento)**

Dado que el producto terminado "Torta de Chocolate" tiene lotes de días previos en refrigeración  
Cuando STAFF registra una salida (EXIT) del producto para atender pedidos  
Entonces el sistema consume primero los lotes más próximos a vencer (FIFO)  
  Y actualiza el stock del producto terminado  
  Y no requiere ninguna mecánica nueva: reutiliza el consumo FIFO de HU-13

### **SC-HU17-04 — Aborto atómico deja el inventario intacto**

Dado que a un ingrediente le falta stock para la cantidad solicitada  
Cuando se intenta producir  
Entonces se hace ROLLBACK total (HU-15-02)  
  Y NO se crea lote de producto terminado, NI movimiento ENTRY, NI registro en production\_runs

