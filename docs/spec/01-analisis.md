# Fase 1 — Análisis

> **Artefacto SDD:** Fase de **Análisis** del ciclo de vida. Responde *qué problema resolvemos,
> para quién y bajo qué restricciones*, antes de cualquier decisión técnica. Es la entrada del
> `03-plan.md` (Diseño).

---

## 1. Problema

Las pastelerías gestionan inventario heterogéneo —insumos **perecederos** (harinas, lácteos,
frutas), **herramientas** de cocina y **útiles de limpieza**— habitualmente en cuadernos o
planillas. Esto genera:

- Mermas por vencimiento no controlado (no se consume primero lo que expira antes).
- Quiebres de stock sorpresivos que detienen la producción.
- Falta de trazabilidad: no se sabe *quién* movió *qué* ni *cuándo*, lo que impide auditar
  pérdidas o errores humanos.
- Imposibilidad de valorizar financieramente el inventario ni medir el costo de las mermas.

## 2. Objetivo

Construir un MVP web que centralice el inventario de una pastelería con **control de acceso por
roles (RBAC)**, **auditoría inmutable** de todos los movimientos, **control de lotes FIFO** por
fecha de vencimiento y **alertas en tiempo real** de stock crítico, dejando los datos
**listos para análisis OLAP**.

## 3. Alcance

### 3.1 Dentro del alcance (MVP)

- Autenticación JWT y gestión de usuarios con tres roles (SUPERADMIN, ADMIN, STAFF).
- Categorías dinámicas con caché Redis (cache-first).
- Ubicaciones físicas rotuladas con código validado.
- CRUD de insumos, listado con filtros y paginación cacheada.
- Movimientos de inventario: `ENTRY`, `EXIT`, `WASTE`, `ADJUSTMENT` con historial inmutable.
- Control de lotes con vencimiento y consumo FIFO automático.
- Producción por recetas (BOM) con descuento atómico de ingredientes.
- Conciliación de stock físico vs. registrado.
- Dashboard de KPIs y valorización financiera.
- Exportación desnormalizada (CSV/Excel) OLAP-ready.
- Alertas en tiempo real vía WebSockets + Redis Pub/Sub.

### 3.2 Fuera del alcance (MVP)

- App móvil nativa, multi-tenant/multi-sucursal, integración con proveedores externos por API,
  facturación electrónica, pipeline OLAP real (solo se deja el export listo para ETL).

## 4. Stakeholders y actores

| Actor | Interés / responsabilidad |
|---|---|
| **SUPERADMIN** (dueño/gerente) | Cuentas de usuario, auditoría global, parametrización del sistema |
| **ADMIN** (jefe de cocina/almacén) | Categorías, insumos, ubicaciones, reabastecimientos, conciliación |
| **STAFF** (pasteleros, limpieza) | Registrar consumos (EXIT) y mermas (WASTE); producir recetas |
| **Docente evaluador** | Verifica aplicación de SDD y funcionamiento desplegado |

## 5. Requisitos funcionales (RF)

Cada RF se materializa en una o más Historias de Usuario en `docs/user-stories.md`.

| RF | Descripción | HU |
|---|---|---|
| RF-01 | Crear categorías dinámicas cache-first | HU-01 |
| RF-02 | Registrar consumo de insumos (STAFF) con alerta de stock | HU-02 |
| RF-03 | Gestionar ubicaciones físicas con código normalizado | HU-03 |
| RF-04 | Autenticar usuarios y emitir JWT con rol | HU-04 |
| RF-05 | CRUD de insumos | HU-05 |
| RF-06 | Listar insumos con filtros y paginación cacheada | HU-06 |
| RF-07 | Consultar historial de movimientos (auditoría) | HU-07 |
| RF-08 | Dashboard de KPIs en tiempo real | HU-08 |
| RF-09 | Reabastecer insumos (ENTRY, ADMIN) | HU-09 |
| RF-10 | Gestionar usuarios y trazabilidad global (SUPERADMIN) | HU-10 |
| RF-11 | Conciliar y ajustar inventario (ADJUSTMENT) | HU-11 |
| RF-12 | Exportar reportes desnormalizados OLAP-ready | HU-12 |
| RF-13 | Controlar lotes y vencimientos con consumo FIFO | HU-13 |
| RF-14 | Emitir alertas en tiempo real (WebSockets) | HU-14 |
| RF-15 | Producir recetas con descuento atómico (BOM) | HU-15 |
| RF-16 | Gestionar proveedores y valorizar el inventario | HU-16 |
| RF-17 | Registrar la producción y llevar stock de productos terminados (colchón para alta demanda) | HU-17 |

## 6. Requisitos no funcionales (RNF)

| RNF | Categoría | Criterio verificable |
|---|---|---|
| RNF-01 | Seguridad | Contraseñas con Bcrypt; JWT firmado; rate limiting (≥5 fallos/15 min bloquea IP 900 s) |
| RNF-02 | Seguridad | RBAC en 3 capas: router (`require_roles`), servicio, BD (constraints/FK) |
| RNF-03 | Integridad | Stock nunca negativo e historial inmutable, garantizados también por la BD |
| RNF-04 | Rendimiento | Lecturas de catálogo/listados servidas desde Redis (cache-first) |
| RNF-05 | Disponibilidad | Modo degradado: si Redis cae, la operación persiste en PostgreSQL |
| RNF-06 | Mantenibilidad | Arquitectura limpia por capas + SOLID; dominio sin dependencias externas |
| RNF-07 | Calidad | Cobertura de pruebas ≥ 80 % |
| RNF-08 | Portabilidad | Entorno reproducible vía Docker Compose (4 servicios) |
| RNF-09 | Analítica | Export plano desnormalizado listo para ingestión OLAP (PowerBI/ClickHouse) |
| RNF-10 | Tiempo real | Propagación de alertas por WebSocket en milisegundos vía Pub/Sub |

## 7. Reglas de negocio críticas

Ver `00-constitution.md` Artículo IV. En resumen: patrón de `LocationCode`, inmutabilidad de
`movement_history`, stock no negativo, RBAC de movimientos y estrategia cache-first.

## 8. Supuestos y restricciones

- **Stack obligatorio** (impuesto por el curso): FastAPI + SQLAlchemy 2.0 async + asyncpg,
  Next.js 15, PostgreSQL 16, Redis 7, Docker Compose.
- Operación en un solo local (single-tenant) para el MVP.
- Despliegue local/demostrativo; no se exige alta disponibilidad productiva.

## 9. Riesgos y mitigaciones

| ID | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| R-01 | Caída de Redis detiene operaciones | Alto | Modo degradado con fallback a PostgreSQL (HU-01 SC-04) |
| R-02 | Condiciones de carrera en el stock | Alto | Lock pesimista + transacción atómica en consumo/producción |
| R-03 | Pérdida de trazabilidad por edición del historial | Alto | Historial inmutable + `ondelete=RESTRICT` en BD |
| R-04 | Consumo de lote vencido antes que el próximo a vencer | Medio | Algoritmo FIFO por `expiration_date` (HU-13) |
| R-05 | Escalada de privilegios de STAFF | Alto | RBAC en 3 capas y pruebas de denegación (403) por HU |
| R-06 | Deriva entre spec y código ("app hecha con IA") | Alto | Matriz de trazabilidad `06-traceability.md` cerrada |

## 10. Criterios de aceptación de la fase

- [x] Problema, alcance y actores definidos.
- [x] 16 RF mapeados a HU con escenarios BDD.
- [x] 10 RNF con criterios verificables.
- [x] Riesgos identificados con mitigación.
- [x] Salida lista para la fase de Diseño (`03-plan.md`).
