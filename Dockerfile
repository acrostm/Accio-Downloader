# =============================================================
# Accio Downloader — All-in-One Image
# One container: Nginx (8080) → FastAPI (8000) + Next.js (3000)
# =============================================================

# ─── Stage 1: Build Next.js frontend ─────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm ci --prefer-offline

COPY frontend/ .
# Build with relative /api/v1 path (no env var needed at build time)
RUN npm run build

# ─── Stage 2: Final runtime image ───────────────────────────
FROM python:3.11-slim

# System dependencies: Nginx + ffmpeg + wget (healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for Next.js standalone server)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── Python backend ────────────────────────────────────────────
WORKDIR /app/backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/


# ── Next.js frontend (standalone build artifact) ───────────────
WORKDIR /app/frontend
COPY --from=frontend-builder /build/frontend/.next/standalone ./
COPY --from=frontend-builder /build/frontend/.next/static ./.next/static
COPY --from=frontend-builder /build/frontend/public ./public

# ── Nginx config ──────────────────────────────────────────────
COPY nginx.conf /etc/nginx/sites-enabled/default
# Remove default nginx config that may conflict
RUN rm -f /etc/nginx/sites-enabled/000-default 2>/dev/null || true

# ── Entrypoint ───────────────────────────────────────────────
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create data directory (will be overridden by volume mount)
RUN mkdir -p /data/downloads

# ── Expose single port ────────────────────────────────────────
EXPOSE 8080

ENV DATABASE_URL="sqlite:////data/sql_app.db"
ENV COOKIES_FILE="/data/cookies.txt"
ENV TEMP_DOWNLOAD_DIR="/data/downloads"
ENV CORS_ORIGINS="*"
ENV NODE_ENV="production"
ENV HOSTNAME="127.0.0.1"
ENV PORT="3000"

CMD ["/start.sh"]
