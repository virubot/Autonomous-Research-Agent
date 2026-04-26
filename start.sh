#!/bin/bash

# Load environment variables
if [ -f node-backend/.env ]; then
  export $(grep -v '^#' node-backend/.env | xargs)
fi

echo "🚀 Starting AI Research Assistant..."


echo "⚙️ Starting Backend..."
uvicorn backend.main:app --reload &

echo "🧩 Starting Node API..."
(cd node-backend && npm start) &

echo "🎨 Starting Frontend..."
cd frontend
npm run dev
