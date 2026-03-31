<div align="center">

# 🤖 AI Financial Copilot

**Upload bank statements. Chat with AI. Master your finances.**

[![Angular](https://img.shields.io/badge/Angular-19-dd0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq_AI-Llama_3.3-f55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-06b6d4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

A full-stack AI-powered web app that extracts transactions from bank statement PDFs and lets you chat with an AI assistant about your finances — complete with interactive dashboards and smart insights.

</div>

---

## 📸 Screenshots

### Upload Statement
<img src="screenshots/upload file.png" alt="Upload Page" width="100%" />

### AI Chat
<img src="screenshots/AI Chat.png" alt="AI Chat" width="100%" />

### Financial Dashboard
<img src="screenshots/Dashboard 1.png" alt="Dashboard" width="100%" />
<img src="screenshots/Dashboard 2.png" alt="Dashboard" width="100%" />
<img src="screenshots/Dashboard 3.png" alt="Dashboard" width="100%" />

### Transactions
<img src="screenshots/Transactions.png" alt="Transactions" width="100%" />
<img src="screenshots/Excel.png" alt="Transactions" width="100%" />
---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **PDF Upload** | Drag-and-drop bank statement upload with auto-parsing |
| 🤖 **AI Chatbot** | RAG-powered chat using Groq AI (Llama 3.3 70B) |
| 📊 **Dashboard** | Interactive Chart.js charts — doughnut, bar, line |
| 📋 **Transactions** | Searchable, filterable table with CSV export |
| 🌗 **Dark/Light Mode** | Persistent theme toggle |
| ⚠️ **Unusual Spending** | Auto-detects outlier transactions |
| 📝 **Logging** | Request IDs, timestamps, execution timing |
| 🇮🇳 **Indian Banks** | Supports Kotak, SBI, HDFC, ICICI statement formats |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Angular 19, Tailwind CSS v4, Chart.js |
| **Backend** | Python, FastAPI, Pydantic |
| **AI/LLM** | Groq API, Llama 3.3 70B Versatile |
| **PDF Parsing** | pdfplumber |
| **Architecture** | RAG (Retrieval-Augmented Generation) |

---

## 📁 Project Structure

```
New-Finance-Helper/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Environment config
│   │   ├── logger.py                # Logging system
│   │   ├── models.py                # Pydantic schemas
│   │   ├── pdf_parser.py            # PDF text extraction
│   │   ├── transaction_processor.py # Text → structured data
│   │   ├── rag_engine.py            # RAG + Groq AI chatbot
│   │   ├── insights.py              # Financial analytics
│   │   └── routes/
│   │       ├── upload.py            # POST /upload-pdf
│   │       ├── transactions.py      # GET /transactions
│   │       ├── chat.py              # POST /chat
│   │       └── insights.py          # GET /insights
│   ├── requirements.txt
│   └── .env.example
├── frontend/                        # Angular 19 app
│   └── src/app/
│       ├── pages/
│       │   ├── upload/              # PDF upload page
│       │   ├── chat/                # AI chatbot page
│       │   ├── dashboard/           # Financial dashboard
│       │   └── transactions/        # Transactions table
│       └── services/
│           ├── api.service.ts       # HTTP client
│           └── theme.service.ts     # Dark/light mode
├── screenshots/
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Groq API Key** — [Get one free →](https://console.groq.com)

### 1️⃣ Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

> ⚠️ **Edit `backend/.env`** and replace `gsk_your_key_here` with your actual Groq API key.

```bash
# Start the server
uvicorn app.main:app --reload --port 8000
```

### 2️⃣ Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
ng serve
```

### 3️⃣ Open the App

```
http://localhost:4200
```

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | — | Your Groq API key |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | AI model to use |
| `CORS_ORIGINS` | No | `http://localhost:4200` | Allowed frontend origins |

---

