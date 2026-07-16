-- ═══════════════════════════════════════════════════════════════
--  PastryStock Manager — Inicialización de Base de Datos
--  Este script crea los ENUMs de dominio que Alembic no gestiona.
--  Se ejecuta automáticamente al primer arranque de PostgreSQL.
-- ═══════════════════════════════════════════════════════════════

-- Roles RBAC del sistema
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('SUPERADMIN', 'ADMIN', 'STAFF');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Unidades de medida para insumos
DO $$ BEGIN
    CREATE TYPE unit_measure AS ENUM (
        'KG', 'GR', 'L', 'ML', 'UNIT', 'PKG', 'BOX', 'DOZEN'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Tipos de movimiento de inventario (inmutables por diseño de auditoría)
DO $$ BEGIN
    CREATE TYPE movement_type AS ENUM (
        'ENTRY',           -- Ingreso de nuevo stock
        'EXIT',            -- Consumo o retiro
        'ADJUSTMENT_ADD',  -- Ajuste positivo (solo ADMIN+)
        'ADJUSTMENT_SUB',  -- Ajuste negativo (solo ADMIN+)
        'WASTE',           -- Merma o descarte
        'TRANSFER'         -- Traslado entre ubicaciones
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Tipos de ubicación física en la pastelería
DO $$ BEGIN
    CREATE TYPE location_type AS ENUM (
        'SHELF',        -- Estante (EST-XX o EST-XX-FX)
        'REFRIGERATOR', -- Refrigeradora (REF-XX)
        'FREEZER',      -- Congeladora (FRZ-XX)
        'CABINET',      -- Armario (CAB-XX)
        'COUNTER',      -- Mostrador (CON-XX)
        'WAREHOUSE'     -- Almacén general (ALM-XX)
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Extensión para UUID v4
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Índice de texto completo para búsqueda de insumos (opcional, útil en UI)
-- Se activa cuando las tablas existan (Alembic las crea después)
