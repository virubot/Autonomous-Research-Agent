#!/bin/bash
set -e

# Load environment from project root .env
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Ensure Homebrew lib path is accessible on macOS for Weasyprint (Pango)
if [[ "$OSTYPE" == "darwin"* ]]; then
  export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH"
  export PATH="/Library/TeX/texbin:$PATH"
fi

# Detect and activate virtual environment
if [ -d ".venv_runtime" ]; then
  echo "🐍 Activating .venv_runtime virtual environment…"
  source .venv_runtime/bin/activate
elif [ -d ".venv" ]; then
  echo "🐍 Activating .venv virtual environment…"
  source .venv/bin/activate
fi


echo "🚀 Starting Autonomous Research Assistant…"
echo ""

# ── Validate critical environment ──
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
  echo "⚠️  GOOGLE_CLOUD_PROJECT is not set. Vertex AI calls will fail."
fi

# ── Start FastAPI backend ──
echo "⚙️  Starting FastAPI backend (port 8000)…"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ── Start Vite frontend ──
echo "🎨 Starting Vite frontend (port 5173)…"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "✅ All services started."
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   Health:   http://localhost:8000/"
echo "   MCP:      http://localhost:8000/mcp/health"
echo ""
echo "Press Ctrl+C to stop all services."

# Trap to kill all child processes on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM EXIT

wait
