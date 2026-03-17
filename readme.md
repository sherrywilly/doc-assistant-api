# 📄 AI Document Assistant API

A production-ready AI-powered API that lets you upload any PDF and ask questions about it in plain English. Built with FastAPI, LangChain, ChromaDB, and Google Gemini.

## 🚀 Live Demo
[Add your Railway link here]

## 💡 How It Works
```
User uploads PDF
      ↓
Document split into chunks
      ↓
Chunks converted to vectors (embeddings)
      ↓
Vectors stored in ChromaDB
      ↓
User asks a question
      ↓
ChromaDB finds most relevant chunks
      ↓
Gemini answers based on context only
      ↓
Answer returned to user
```

## 🧠 Why RAG?
Traditional approaches send entire documents to the LLM every query — expensive and slow. This project uses Retrieval Augmented Generation (RAG) to retrieve only the most relevant chunks, reducing token costs by up to 100x while improving answer accuracy.

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI |
| AI Orchestration | LangChain |
| Vector Store | ChromaDB |
| LLM | Google Gemini |
| Frontend | Streamlit |
| Deployment | Railway |

## ⚙️ Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/sherrywilly/doc-assistant-api
cd doc-assistant-api
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your-key-here
```

### 4. Run the API
```bash
uvicorn app.main:app --reload
```

### 5. Run the frontend
```bash
streamlit run frontend.py
```

## 📡 API Endpoints

### Upload a document
```
POST /api/v1/upload/{doc_id}
Content-Type: multipart/form-data
Body: file (PDF)
```

### Ask a question
```
POST /api/v1/ask/{doc_id}
Params: question (string)
```

## 📁 Project Structure
```
doc-assistant-api/
├── app/
│   ├── main.py
│   ├── routes/
│   │   └── document.py
│   ├── services/
│   │   └── rag.py
│   └── core/
│       └── config.py
├── frontend.py
├── requirements.txt
├── Dockerfile
├── .env
├── .gitignore
└── README.md
```

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| GEMINI_API_KEY | Your Google Gemini API key |

## 🚀 Deployment

This project is deployed on Railway.
1. Push code to GitHub
2. Connect Railway to your repository
3. Add environment variables in Railway dashboard
4. Deploy ✅

## 👨‍💻 Author

**Sherry Wilson** — Python & AI Backend Developer
- LinkedIn: linkedin.com/in/sherry-wilson-python-dev
- GitHub: github.com/sherrywilly