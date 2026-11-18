# Crawler

The Crawler scrapes and preprocesses technical documentation, converting it into clean, searchable chunks for semantic indexing.

---

## 🧠 Tech Stack

| Component       | Tech                             |
| --------------- | -------------------------------- |
| Framework       | Scrapy                           |
| HTML → Markdown | `html2text`                      |
| Text Splitter   | `RecursiveCharacterTextSplitter` |
| Embedding       | `BAAI/bge-base-en-v1.5`          |
| Storage         | PostgreSQL + `pgvector`          |

---

## 🚀 Setup
### 1. Add Target URLs

List documentation pages in: `urls.txt`

### 2. Run the Crawler
```bash
scrapy crawl doc_spider -a urls_file="./urls.txt" --loglevel=INFO
```

---

## 🧾 Credits
Airel Camilo Khairan © 2025
