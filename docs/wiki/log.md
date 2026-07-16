# Log de Operaciones

<!-- Formato: ## [YYYY-MM-DD] operacion | Detalle -->
<!-- Parseable: grep "^## \[" log.md | tail -10 -->

## [2026-07-08] init | Wiki inicializada
- Estructura de carpetas creada (wiki/{fuentes,entidades,conceptos,sintesis}, raw/assets)
- Dominio: desarrollo del sistema PastryStock Manager
- CLAUDE.md, index.md y log.md configurados

## [2026-07-08] ingest | Sesión: Frontend Next.js 15 y seed de admin
- Fuente creada: fuentes/sesion-frontend-nextjs-y-seed-admin
- Entidades: pastrystock-manager, frontend-nextjs, script-seed-admin
- Conceptos: autenticacion-jwt-cookies-httponly, server-components-vs-server-actions, rbac, seed-idempotente
- 8 páginas en total, sin contradicciones detectadas

## [2026-07-08] ingest | Sesión: Completado del backend (16 historias de usuario)
- Fuente creada: fuentes/sesion-backend-completo-16-hu
- Entidad nueva: backend-pastrystock (+ actualizada pastrystock-manager)
- Conceptos nuevos: fifo-lotes-vencimiento, produccion-bom-transaccion-atomica,
  valorizacion-inventario, rate-limiting-redis, blacklist-jwt-redis,
  websockets-redis-pubsub, olap-export-desnormalizado, cache-first-paginacion
- Concepto actualizado: rbac (imposición backend + SUPERADMIN/ADMIN/STAFF por HU)
- 18 páginas en total; verificación E2E contra stack Docker; 48 tests unitarios en verde
- Nota de síntesis: posible diferencia transitoria stock-insumo vs suma-de-lotes tras conciliación

## [2026-07-08] update | HU-15: endpoint de dry-run / simulacro de stock
- Añadido POST /api/v1/production/simulate (solo lectura, no descuenta stock)
- Concepto actualizado: produccion-bom-transaccion-atomica
- +2 tests unitarios (50 en total); verificado E2E: viable/no-viable con déficit, stock intacto

## [2026-07-08] ingest | Sesión: Frontend — módulos avanzados y FontAwesome
- Fuente creada: fuentes/sesion-frontend-modulos-avanzados
- Concepto nuevo: iconos-fontawesome-nextjs
- Entidad actualizada: frontend-nextjs (15 rutas; nuevos módulos y componentes)
- Módulos UI: dashboard KPIs/financials, producción con dry-run, lotes FIFO+conciliación
  en detalle de insumo, usuarios+auditoría, reportes CSV, alertas WebSocket (AlertToaster)
- Verificación: tsc limpio, next build OK (15/15), render real + guards de rol STAFF
- 20 páginas en total
- Incidencia: la BD de desarrollo fue truncada por una corrida de pytest tests/integration
  (quedó fixture admin-*@test.local); re-sembrado el superadmin. No afectó el código frontend.

## [2026-07-08] ingest | Sesión: Recuperación de contraseñas y UX explicativa
- Fuente creada: fuentes/sesion-recuperacion-y-ux-modulos
- Concepto nuevo: recuperacion-contrasenas (reset admin + CLI + época de sesión con iat)
- Entidades actualizadas: backend-pastrystock, frontend-nextjs
- Backend: PATCH /users/{id}/password, scripts/reset_password.py, iat en JWT,
  token:valid_from:{user_id}; corregido bug de bloqueo de 60 min tras reset
- Frontend: componente ResetPassword en Usuarios + InfoBanner en los 8 módulos
- Verificación E2E: token viejo→401, re-login inmediato→200, STAFF→403; build OK
- 22 páginas en total

## [2026-07-08] ingest | Sesión: Perfil de usuario, tests y cobertura ≥80%
- Fuente creada: fuentes/sesion-perfil-y-cobertura-tests
- Concepto nuevo: gestion-perfil-usuario; actualizado: recuperacion-contrasenas
- Backend: PATCH /auth/me y /auth/me/password (self-service); test de login corregido a 401
- Frontend: página /profile (editar nombre + cambiar clave), enlace desde el sidebar
- Tests: nuevo tests/integration/test_advanced_api.py (16 casos); 88 passed; cobertura 81.8%
- 24 páginas en total
- Nota recurrente (3ª vez): pytest completo trunca la BD de desarrollo; re-sembrar superadmin

## [2026-07-08] ingest | Sesión: Avatar, PyJWT y aislamiento de la BD de tests
- Fuente creada: fuentes/sesion-avatar-pyjwt-y-test-db
- Conceptos nuevos: avatar-perfil-y-estaticos, aislamiento-bd-tests
- Backend: migración jose→PyJWT (0 warnings); avatar de perfil completado (migración 003
  aplicada, /auth/me/avatar, /static montado); login roto reparado
- Tests: aislados en `pastry_test` (scripts/setup_test_db.py + conftest); pytest ya NO
  toca la BD de desarrollo (verificado: superadmin sobrevive). 89 passed, cobertura 81.8%
- Frontend: AvatarForm + route handler /api/profile/avatar + avatar en sidebar; build OK (17 rutas)
- 27 páginas en total. Problema recurrente del truncado: RESUELTO.

## [2026-07-09] ingest | Sesión: Ajustes del sistema, branding, recorte de imágenes y paginación
- Fuente creada: fuentes/sesion-ajustes-branding-y-paginacion
- Entidad nueva: entidades/script-seed-demo
- Conceptos nuevos (8): configuracion-sistema-en-bd, temas-css-variables-tailwind,
  recorte-imagenes-1a1-y-aspecto, fondo-login-responsivo, paginacion-ui-searchparams,
  navegacion-responsiva-y-sidebar-fijo, hot-reload-docker-windows,
  cache-obsoleta-tras-cambio-de-schema
- Conceptos actualizados (4): avatar-perfil-y-estaticos (bug de cookie + recorte 1:1),
  iconos-fontawesome-nextjs (selector + lista blanca), seed-idempotente (guarda de consumo),
  cache-first-paginacion (settings + riesgo abierto)
- Entidades actualizadas (3): pastrystock-manager, backend-pastrystock, frontend-nextjs
- Backend: migraciones 004/005/006; SettingsService + SettingsRepository; app/core/uploads.py
  (Pillow 11.1.0); lista blanca de iconos; paginación del audit-log; UserRepository.list_all();
  /docs unificado con el nombre de la BD; expiration_alert_days migrado del entorno a la BD
- Frontend: /settings (5 formularios), MobileNav, Pagination, ImageCropper, IconPicker,
  temas por variables CSS, favicon desde el logo, footer dinámico, lib/format.ts
- Tests: 119 passed, cobertura 82.6%
- Hallazgos de infraestructura: WATCHPACK_POLLING (hot-reload muerto en Docker/Windows) y
  caché de Redis obsoleta tras cambio de schema (500 en GET /settings)
- Deuda registrada: getSupply() usa limit:100 y filtra en memoria; falta GET /supplies/{id}
- 37 páginas en total

## [2026-07-09] update | Limpieza de entorno y corrección de la medición de cobertura
- Concepto nuevo: conceptos/cobertura-y-greenlet-sqlalchemy
- Entidad actualizada: backend-pastrystock (cifras de cobertura)
- Limpieza: contenedor huérfano `compassionate_chaum` eliminado; directorio fantasma
  `frontend/C:/Program Files/Git/pnpm/store` eliminado (0 archivos, solo dirs vacíos)
- Diagnóstico: `pytest tests/integration` fallaba con 77.50%. La causa NO era falta de
  tests: coverage.py dejaba de trazar tras el primer `await` a la BD (greenlet de
  SQLAlchemy async). Un test de producción pasaba con el servicio "al 41%".
- Corrección: `[tool.coverage.run] concurrency = ["thread","greenlet"]` en pyproject.toml
  + exclusión de los `class ...(Protocol):` en el reporte
- Resultado sin escribir un solo test nuevo: integración 77.50% → 87.69%;
  suite completa 82.61% → 88.57%. 119 passed.
- Gaps reales restantes: endpoints/websocket.py y cache/pubsub_listener.py sin integración
- 38 páginas en total

## [2026-07-10] ingest | Formalización de la evidencia SDD (Spec Kit)
- Origen: exigencia del docente de evidenciar SDD en todo el ciclo de vida (no "app hecha con IA")
- Auditoría: evidencia SDD existía pero incompleta/dispersa; faltaban análisis, tareas,
  despliegue formal y matriz de trazabilidad (el hueco que distingue SDD real)
- Creada carpeta `docs/spec/` con 8 archivos (Spec Kit manual en .md): 00-constitution,
  01-analisis, 02-specification, 03-plan, 04-tasks (71 tareas / 12 bloques), 05-deployment,
  06-traceability (matriz cerrada para las 16 HU) y README índice
- Decisión: formalización honesta (refleja decisiones reales; sin cronograma ficticio)
- Verificación de fidelidad en código: seeds en `backend/scripts/seed_admin.py` y `seed_demo.py`;
  health check real `GET /health` en `app/main.py`
- Página nueva: fuentes/sesion-formalizacion-sdd-spec-kit; concepto nuevo:
  conceptos/spec-driven-development-spec-kit
- Entidad actualizada: pastrystock-manager (nueva aparición)
- 40 páginas en total

## [2026-07-10] ingest | HU-17: registro de producción y producto terminado
- Origen: el dueño reportó que producir no dejaba registro; el producto terminado debe ser
  inventario (se guarda en refri para vender luego, colchón de alta demanda)
- Cambio por SDD: spec primero (HU-17, 4 escenarios) → migración 007 → servicio → endpoint → frontend
- Backend: ItemType; supply_items.item_type; recipes.produces_supply_item_id + shelf_life_days;
  tabla inmutable production_runs; ProductionService fases 3-4 + GET /production/history
- Producto terminado = supply_item reutilizando lotes/FIFO/vencimiento/movimientos/valorización
- Verificación: migración aplicada a dev y pastry_test; suite 121 verde, cobertura 88%
  (nuevo unit test + integración end-to-end que produce contra Postgres real)
- De paso: corregidos 2 tests de reportes preexistentes que no contemplaban el BOM UTF-8 del CSV
- Páginas nuevas: fuentes/sesion-produccion-registro-y-producto-terminado;
  conceptos/producto-terminado-y-registro-de-produccion
- 42 páginas en total

## [2026-07-11] ingest | Refinamientos: UX de producto, auditoría legible y OLAP
- Feedback del usuario final tras usar HU-17
- Producto terminado: la receta lo AUTO-CREA (product_name/location/shelf_life) bajo categoría
  "Productos terminados"; sección propia + filtro item_type en GET /supplies; se quitó el toggle
  del alta de insumo. El dato sigue en supply_items (motor unificado)
- Auditoría (HU-10-03): resumen en español con insumo, unidad y motivo (join
  list_by_performer_with_context); badge de acción en español en el frontend
- OLAP (HU-12): export gana item_type, unit_cost, total_cost, notes
- Verificación: suite 121 verde, cobertura 88%; typecheck frontend limpio
- Página nueva: fuentes/sesion-refinamientos-ux-auditoria-y-olap; concepto
  producto-terminado-y-registro-de-produccion actualizado
- 43 páginas en total

## [2026-07-15] update | Deuda saldada: GET /supplies/{id} (detalle de insumo)
- Backend: SupplyService.get_detail (sin caché; 404 vía ItemNotFoundError ya mapeada);
  endpoint GET /supplies/{supply_id} accesible a cualquier usuario autenticado (igual que el listado)
- Frontend: getSupply(id) ahora llama directo a /supplies/{id} (antes: getSupplies limit:100 + find en memoria)
- Tests: +1 unit (TC-SVC-06, 404) y +2 integración (200 con STAFF, 404); suite 124 verde, cobertura 88%
- Verificación: tsc frontend limpio (exit 0)
- Concepto actualizado: cache-first-paginacion (nota de deuda saldada)
- 43 páginas en total (sin páginas nuevas)

## [2026-07-15] update | Lista de preparación (picking list) en el simulacro de producción
- Necesidad del dueño: al producir una receta, ver el resumen de insumos con cantidad y
  DÓNDE extraer cada uno (ubicación + lote), para no ubicarlos a mano
- Backend: SimulatedIngredient gana unit, location_code, location_type y batch_plan[]
  (BatchPickPlan: batch_code/expiration_date/take); BatchRepository.list_active_fifo
  (solo lectura); ProductionService inyecta LocationRepository y arma el plan FIFO en simulate()
- La ubicación vive en el supply_item (los lotes no la tienen); plan FIFO = misma lógica que
  _consume_ingredient pero sin lock ni descuento
- Frontend: ProduceWidget muestra columna "Ubicación" y el desglose "Extraer de: L-A −12 (vence…)"
  bajo cada ingrediente
- Tests: +1 unit (plan FIFO + ubicación) y +1 integración (E2E con 2 lotes); suite 126 verde,
  cobertura 88%; tsc frontend limpio
- Concepto actualizado: produccion-bom-transaccion-atomica
- 43 páginas en total (sin páginas nuevas)

## [2026-07-15] update | Fix 500 dev, datos de simulación con preparación y placeholders
- 500 en /dashboard: lo causó correr `next build` en el contenedor que ejecuta `next dev`
  (comparten el volumen anónimo /app/.next → chunks corruptos "Cannot find module './653.js'").
  Fix: recrear el contenedor con volúmenes anónimos frescos
  (`docker-compose up -d --force-recreate --renew-anon-volumes frontend`). NO usar `next build`
  en dev. Verificado: /login 200, /dashboard y /production 307 (redirect, sin 500)
- Datos de simulación: se limpió la BD de desarrollo (TRUNCATE de tablas de negocio, usuarios y
  ajustes intactos) y se regeneró con seed_demo (--cakes 4). seed_demo ahora crea, por cada torta,
  su corrida (production_runs) + lista de preparación (production_run_items) con desglose FIFO,
  para que el historial y el modal estrenen datos reales. Verificado E2E: historial=4,
  GET /production/{id}/preparation devuelve unidad/ubicación/lotes correctos
- UX: placeholders añadidos a los inputs de texto/número/clave vacíos en ~11 formularios
  (insumos, receta, categoría, ubicación, usuarios, lotes, consumo, conciliación, cambio de clave,
  movimientos, datos del negocio). Omitidos los precargados con defaultValue y los file/color/date
- tsc frontend limpio
- 43 páginas en total (sin páginas nuevas)

## [2026-07-15] update | 2ª receta demo que genera producto terminado (aparece en Productos)
- Necesidad: la demo no tenía nada en la sección de Productos (la receta existente no producía terminado)
- seed_demo: nueva categoría "Productos terminados", producto FINISHED_PRODUCT "Brownie de Chocolate
  (bandeja x12)" en REF-01, 2ª receta "Brownie de Chocolate" (produces_supply_item_id + shelf_life 5d,
  6 ingredientes) y 3 corridas ya producidas (_produce_product: descuento FIFO + lote con vencimiento +
  ENTRY + run items). Idempotente (guarda: product.current_stock>0)
- Verificado E2E: GET /supplies?item_type=FINISHED_PRODUCT → 1 producto stock 3; receta con produces=True;
  3 lotes FIFO con vencimiento; 3 production_runs con su lista de preparación
- 43 páginas en total (sin páginas nuevas)

## [2026-07-15] update | Unidades visibles + historial "cómo se hizo" (lista de preparación persistida)
- Feedback del dueño: (1) el simulacro no mostraba unidades ("¿0,25 de qué?"); (2) el historial
  de producción debe permitir ver en un modal cómo se fabricó cada corrida (insumo, cantidad,
  unidad, ubicación y de qué lotes salió); (3) la receta debe mostrar la unidad exacta, no "unidad"
- Backend: migración 008 + tabla/modelo production_run_items (SNAPSHOT inmutable por ingrediente:
  supply_name, unit, location_code, quantity_consumed, unit_cost, batch_breakdown JSONB);
  produce() asienta el snapshot; GET /production/{id}/preparation (ADMIN+) con ProductionRunNotFoundError→404
- Frontend: UNIT_ABBR + formatQuantityUnit; ProduceWidget muestra unidades; receta muestra unidad real
  del insumo (mapa supplyUnit); PreparationButton abre modal con la preparación histórica
- Tests: +2 unit (snapshot en produce, 404 de preparación) y +3 integración (snapshot E2E con lotes,
  404, STAFF 403); suite 130 verde, cobertura 89%; tsc frontend limpio
- Migración aplicada a dev y pastry_test (setup_test_db.py); conftest _TABLES incluye la tabla hija
- Concepto actualizado: produccion-bom-transaccion-atomica
- 43 páginas en total (sin páginas nuevas)
