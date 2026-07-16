---
title: "Seed idempotente"
tags: [seed, bootstrap, idempotencia, backend]
source_count: 2
---

# Seed idempotente

## Definición
Patrón para scripts de datos iniciales (bootstrap) que pueden ejecutarse múltiples veces
sin efectos duplicados. Antes de insertar, se comprueba la existencia del registro; si
existe, se omite o se concilia (p. ej. reactivar) en lugar de crear un duplicado.

## Fuentes que lo mencionan
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — script del admin inicial
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — `seed_demo.py`, escenario completo

## Perspectivas/decisiones
- `seed_admin.py` busca por email (`get_by_email`): si existe y está activo, no hace nada;
  si existe inactivo, lo reactiva; si no existe, lo crea.
- Parámetros por defecto desde `settings` con overrides por CLI (`--email`, `--password`,
  `--name`, `--role`), lo que permite reusar el mismo script para ADMIN o STAFF.
- Seguro para correr en cada arranque o despliegue sin ensuciar la base.

### La guarda del seed de datos
[[entidades/script-seed-demo]] añade un matiz importante: cuando el seed **consume stock**
(descuentos FIFO, mermas), la idempotencia no basta con "no dupliques filas" — hay que
impedir que una segunda corrida vuelva a descontar. La guarda elegida es la presencia del
**último registro que escribe** el bloque (la merma de huevos): si existe, el bloque entero
ya corrió. Comprobar un registro intermedio dejaría el escenario a medias si una corrida
anterior falló.

Además, no ofrece `--reset`: `movement_history` es inmutable por diseño, así que borrar
contradiría la auditoría.

## Contradicciones detectadas
Ninguna.
