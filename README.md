# Autonomous Research Agent

> An advanced, AI-powered multi-agent system for autonomous academic research, literature review, and publication-ready paper generation.

---

## 🚀 Overview

The **Autonomous Research Agent** is a cutting-edge, production-grade AI system designed to automate the end-to-end academic research lifecycle. Built for researchers, academics, and developers, it transforms simple prompts or uploaded documents into highly structured, publication-ready research papers (IEEE, APA, ACM).

By leveraging a sophisticated multi-agent architecture powered by Google's Vertex AI (Gemini 2.5), the system autonomously plans research steps, executes web searches, extracts data from PDFs and images via OCR, synthesizes information, and compiles high-fidelity LaTeX PDFs.

---

## ✨ Features

### 🤖 AI & Multi-Agent System
- **Autonomous Reasoning:** Dynamic step-by-step planning and execution using the `AgentExecutor` and `planner`.
- **Model Context Protocol (MCP):** Fully integrated MCP server allowing the agent to dynamically discover and use external tools.
- **Vertex AI Integration:** Powered by Google's state-of-the-art Gemini 2.5 Flash and Lite models with robust error recovery and fallback mechanisms.

### 📚 Research & Document Analysis
- **Deep Web Search:** Integrated DuckDuckGo search for real-time context gathering and citation discovery.
- **Advanced Document Parsing:** Robust extraction of text from uploaded PDFs (`pypdf`).
- **Optical Character Recognition (OCR):** Image text extraction using `pytesseract` and `Pillow`.
- **Unified Memory Store:** Persistent SQLite databases (`agent_memory.db`, `agent_events.db`, `pdf_files.db`) for retaining research context across sessions.

### 📝 Academic Paper Generation
- **Publication-Ready Output:** High-fidelity LaTeX pipeline producing visually authentic, conference-ready PDFs.
- **Template Support:** Native support for IEEE, APA, and ACM formatting standards.
- **Automated Citations:** Intelligent bibliography management preventing JSON leakage and ensuring accurate academic referencing.

### 💻 UI/UX & Dashboard
- **Modern Architecture:** Sleek, responsive React frontend built with Vite.
- **Premium Design:** Utilizing Tailwind CSS, Shadcn UI, Radix UI, and Framer Motion for a fluid, "Obsidian-like" intelligence experience.
- **Real-Time Rendering:** Live Markdown rendering and Mermaid diagram support within the conversational interface.

### ☁️ Infrastructure & Integrations
- **Google Drive Integration:** Automated uploading of generated papers and assets to Google Drive.
- **FastAPI Backend:** High-performance, asynchronous Python backend.

---

## 🧠 How It Works

1. **User Request:** The user provides a research topic, prompt, or uploads source material (PDFs/Images) via the React dashboard.
2. **Task Planning:** The `AgentExecutor` on the FastAPI backend analyzes the request and generates a multi-step research plan.
3. **Information Gathering:** The agent invokes MCP tools to perform web searches (`web_search`), extract document data (`extract_pdf`, `extract_image`), and stores findings in the SQLite `agent_memory.db`.
4. **Synthesis:** The AI synthesizes the gathered literature, structuring the content according to strict academic guidelines and depth requirements.
5. **LaTeX Compilation:** The structured data is passed through the `pdf_generator`, which maps it to specific templates (IEEE/APA/ACM) and securely compiles it into a PDF using LaTeX.
6. **Delivery:** The final PDF is served to the frontend for viewing/download or automatically exported to Google Drive.

---

## 🏗️ Tech Stack

### Frontend
| Technology | Description |
|---|---|
| **React 18 & Vite** | Blazing fast, modern UI framework and bundler. |
| **Tailwind CSS** | Utility-first CSS framework for rapid styling. |
| **Shadcn UI & Radix** | Accessible, customizable headless components. |
| **Framer Motion** | Fluid animations and page transitions. |
| **React Markdown** | Real-time markdown and Mermaid diagram rendering. |

### Backend
| Technology | Description |
|---|---|
| **FastAPI & Uvicorn** | High-performance, async Python web framework. |
| **Google Vertex AI** | LLM provider (Gemini 2.5 Flash/Lite). |
| **Pydantic** | Strict data validation and settings management. |
| **SQLite** | Lightweight, persistent vector/memory storage. |

### Document & AI Processing
| Technology | Description |
|---|---|
| **LaTeX (pdfLaTeX)** | Professional academic document compilation. |
| **Tesseract & Pillow** | OCR and image processing pipeline. |
| **PyPDF** | Robust PDF parsing and text extraction. |
| **DuckDuckGo Search** | Real-time web search and citation fetching. |

---

## 📂 Project Structure

```bash
/
├── backend/                  # FastAPI Backend Application
│   ├── agent/                # Multi-agent logic, planner, memory, and executor
│   ├── mcp/                  # Model Context Protocol server implementation
│   ├── routes/               # API endpoints (generation, uploads)
│   ├── services/             # Core business logic
│   ├── paper_templates/      # LaTeX templates (IEEE, APA, ACM)
│   ├── tools/                # Agent tools (search, OCR, PDF extraction)
│   ├── utils/                # Configuration and shared utilities
│   └── main.py               # Application entry point
├── frontend/                 # React + Vite Frontend Application
│   ├── src/
│   │   ├── components/       # Reusable UI components (Shadcn)
│   │   ├── pages/            # Main application views/dashboard
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utility functions
│   │   ├── App.tsx           # Main application component
│   │   └── main.tsx          # React DOM entry
│   ├── package.json          # Frontend dependencies
│   └── tailwind.config.ts    # Styling configuration
├── start.sh                  # Unified startup script for both services
├── requirements.txt          # Python backend dependencies
└── .env.example              # Environment variables template
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- LaTeX distribution (`texlive` or `mactex` for compiling PDFs)
- Tesseract OCR (for image extraction)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/autonomous-research-agent.git
cd autonomous-research-agent
```

2. **Configure Environment:**
Copy the example environment file and add your Google Cloud credentials.
```bash
cp .env.example .env
```

3. **Install Dependencies:**
The startup script handles the virtual environment, but you can manually install:
```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

4. **Run the Application:**
Use the provided bash script to start both the FastAPI backend and Vite frontend concurrently.
```bash
./start.sh
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
