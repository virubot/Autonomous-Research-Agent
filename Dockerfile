# ── Stage 1: Build frontend ──
FROM node:20-bookworm AS frontend-builder

WORKDIR /app/frontend

# Install frontend dependencies
COPY frontend/package*.json ./

RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build production frontend
RUN npm run build


# ── Stage 2: Python production runtime ──
FROM python:3.11-slim-bookworm AS runner

WORKDIR /app

# Install Linux system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-lmodern \
    tesseract-ocr \
    ghostscript \
    pandoc \
    graphviz \
    imagemagick \
    poppler-utils \
    texlive-base \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-font-utils \
    texlive-pictures \
    texlive-publishers \
    texlive-science \
    texlive-bibtex-extra \
    texlive-extra-utils \
    lmodern \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and startup files
COPY backend/ ./backend/
COPY start.sh .
COPY .env .

# Create runtime folders
RUN mkdir -p uploads outputs generated_outputs

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Make startup script executable
RUN chmod +x start.sh

# Cloud Run port
ENV PORT=8080

EXPOSE 8080

# Start application
CMD ["./start.sh"]