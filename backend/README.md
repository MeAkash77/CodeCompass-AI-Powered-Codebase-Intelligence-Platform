# Backend

The Backend powers the retrieval and response system of code-compass.
It receives user prompts, retrieves relevant documentation chunks, and generates factual, cited answers using an LLM.

---

## 🧠 Tech Stack

| Component | Tech                                           |
| --------- | ---------------------------------------------- |
| Framework | FastAPI                                        |
| Database  | PostgreSQL + `pgvector`                        |
| ORM       | SQLAlchemy + Alembic                           |
| Embedding | `BAAI/bge-base-en-v1.5`                        |
| Reranker  | `BAAI/bge-reranker-base`                       |
| LLM       | Gemini 2.5 Flash Lite / other models           |

---

## 🚀 Setup
### 1. Environment

Create a `.env` file using `.env.example` as a reference.

```bash
MODEL_PROVIDER=gemini
LLAMA_MODEL=models/microsoft_Phi-4-mini-instruct-Q4_K_M.gguf
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_API_KEY=
```

### 2. Start Services
```bash
docker compose up --build
```

### 3. Apply Database Migrations
```bash
alembic upgrade head
```

---

## 🧾 Credits
Airel Camilo Khairan © 2025
