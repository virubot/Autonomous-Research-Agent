**AI Research Assistant 🚀**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-v18+-68a063.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![Groq](https://img.shields.io/badge/Powered_by-Groq-orange.svg)](https://groq.com/)
[![Puppeteer](https://img.shields.io/badge/PDF_Engine-Puppeteer-blue.svg)](https://pptr.dev/)

**Agent** is a state-of-the-art, multi-service autonomous agent designed to generate professional, high-fidelity IEEE-style research papers. By orchestrating a hybrid backend (FastAPI + Node.js) and a modern React frontend, it transforms a single topic into a complete, print-ready academic document with zero manual formatting required.

---

## 📖 Table of Contents
- [✨ Key Features](#-key-features)
- [🏗 Architecture](#-architecture)
- [🛠 Tech Stack](#-tech-stack)
- [🚀 Quick Start](#-quick-start)
- [📂 Project Structure](#-project-structure)
- [🔧 API Endpoints](#-api-endpoints)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)

---

## ✨ Key Features

- 🏛 **Academic Typesetting**: Automatic 2-column layout conforming strictly to IEEE conference standards.
- 🤖 **Multi-Agent Pipeline**: Sophisticated content generation across Abstract, Introduction, Methodology, Architecture, Results, and Conclusion.
- 📊 **Dynamic Diagrams**: Generates **Mermaid.js** flowcharts and system architectures based on your topic.
- 📐 **Scientific Precision**: Full **MathJax** integration for rendering complex mathematical equations.
- 📑 **IEEE References**: Automatically generates and formats academic references in IEEE style.
- ⚡ **Turbocharged LLMs**: Powered by **Groq** (Llama 3.1) for lightning-fast content synthesis.
- 🎨 **Modern Dashboard**: Sleek, responsive React UI built with TailwindCSS and Shadcn/UI components.

---

## 🏗 Architecture

Virubot employs a distributed architecture to handle the complex requirements of research paper generation:

1.  **Frontend (React/Vite)**: A high-performance UI for topic input, real-time generation monitoring, and PDF previewing.
2.  **Node API (Express)**: The primary orchestrator. It manages LLM streaming, handles Mermaid/MathJax rendering via Puppeteer, and manages file persistence.
3.  **Research Backend (FastAPI)**: Handles heavy-duty data processing, research analysis, and complex agentic workflows using RAG.

---

## 🛠 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite, TailwindCSS, Shadcn/UI, TypeScript |
| **Orchestration** | Node.js, Express |
| **Research Engine** | Python 3.10+, FastAPI, Uvicorn |
| **LLM Engine** | Groq API (Llama 3.1 70B/8B), OpenAI SDK |
| **PDF Rendering** | Puppeteer (Headless Chrome), HTML5, CSS3 |
| **Visualization** | Mermaid.js, MathJax |

---

## 🚀 Quick Start

### 1. Prerequisites
- **Node.js** (v18 or higher)
- **Python** (v3.10 or higher)
- **Groq API Key** (Get one at [console.groq.com](https://console.groq.com))

### 2. Installation

Clone the repository and install dependencies for all modules:

```bash
git clone https://github.com/virubot/ResearchPaper_Agent.git
cd ResearchPaper_Agent

# Setup Node Backend
cd node-backend && npm install

# Setup Frontend
cd ../frontend && npm install

# Setup Research Backend (Python)
cd ..
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the `node-backend/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
PORT=5001
```

### 4. Running the Application

Simply run the startup script from the root directory:

```bash
chmod +x start.sh
./start.sh
```

The application will be available at:
- **Frontend**: `http://localhost:5173`
- **Node API**: `http://localhost:5001`
- **Research API**: `http://localhost:8000`

---

## 📂 Project Structure

```text
.
├── frontend/             # React + Vite application (UI/UX)
├── node-backend/         # Express API & Puppeteer Rendering
│   ├── services/         # LLM orchestration & PDF logic
│   ├── routes/           # API Endpoints
│   └── utils/            # IEEE Templates & CSS
├── backend/              # FastAPI Research Engine (RAG/Logic)
├── generated_pdfs/       # Saved research papers
├── start.sh              # Unified startup script
└── requirements.txt      # Python dependencies
```

---

## 🔧 API Endpoints (Node Backend)

### `POST /api/paper/generate`
Generates a complete research paper based on the provided topic.

**Request Body:**
```json
{
  "topic": "The Impact of Quantum Computing on Modern Cryptography"
}
```

**Response:**
```json
{
  "paper": "<html>...</html>",
  "title": "Quantum Computing...",
  "wordCount": 2850,
  "pageCount": 6
}
```

---

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Built with ❤️ by <strong>Virubot</strong> and the Open Source Community
</p>
