# ═══════════════════════════════════════════════
#  Frontend — Next.js 15
#  Multi-stage: development | production
# ═══════════════════════════════════════════════

# ── Imagen base ─────────────────────────────────
FROM node:22-alpine AS base

ENV PNPM_HOME="/pnpm" \
    PATH="$PNPM_HOME:$PATH"

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# ── Stage: dependencias ─────────────────────────
FROM base AS deps

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# ── Stage: desarrollo (hot-reload) ─────────────
FROM base AS development

# Instalamos dependencias en la imagen para que el volumen anónimo
# /app/node_modules del compose las preserve al montar el código fuente.
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

EXPOSE 3000

CMD ["pnpm", "dev"]

# ── Stage: builder de producción ────────────────
FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* se incrusta en el bundle en tiempo de build: debe llegar como
# build-arg (Railway lo inyecta desde las variables del servicio). Sin esto, el
# navegador (imágenes y WebSocket de alertas) apuntaría a localhost en producción.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

ENV NEXT_TELEMETRY_DISABLED=1

RUN pnpm build

# ── Stage: producción (imagen mínima) ───────────
FROM node:22-alpine AS production

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
