# ── Stage 1: Build frontend ──
FROM node:20-bookworm AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


# ── Stage 2: Python production runtime ──
FROM python:3.11-slim-bookworm AS runner

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    tesseract-ocr \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend + app files
COPY backend/ ./backend/
COPY start.sh .
COPY .env.example .
COPY uploads/ ./uploads/
COPY outputs/ ./outputs/

# Copy frontend build from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Make startup script executable
RUN chmod +x start.sh

# Cloud Run port
ENV PORT=8080

EXPOSE 8080

# Start application
CMD ["./start.sh"]