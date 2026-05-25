# ── Stage 1: Build the frontend static assets ──
FROM node:20-bookworm AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Production Python runtime ──
FROM python:3.11-slim-bookworm AS runner
WORKDIR /app

# Install system dependencies for LaTeX compiling and OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and startup scripts
COPY backend/ ./backend/
COPY start.sh .

# Copy built frontend assets from Stage 1 builder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN chmod +x start.sh

ENV PORT=8080
EXPOSE 8080

CMD ["./start.sh"]