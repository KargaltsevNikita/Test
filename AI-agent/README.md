# Safe Website AI Agent (Python MVP)

Этот проект — стартовый production-oriented шаблон для ИИ-агента на сайте.
Он умеет:

- отвечать на вопросы по базе знаний через RAG;
- искать свежую информацию в интернете как fallback;
- искать подходящие изображения;
- сохранять заявки менеджеру;
- отказывать на off-topic и unsafe запросы.

## Архитектура

```text
Frontend widget -> FastAPI -> LangGraph router
                                 ├─ Guardrails
                                 ├─ KB retriever (Qdrant)
                                 ├─ Web search tool
                                 ├─ Image search tool
                                 └─ Lead capture tool
```

## Что лежит в проекте

- `app/main.py` — FastAPI API
- `app/agent/graph.py` — граф агента
- `app/agent/nodes.py` — узлы графа
- `app/agent/guards.py` — guardrails и routing
- `app/rag/ingest.py` — индексация базы знаний
- `app/rag/retriever.py` — retrieval из Qdrant
- `app/tools/*` — инструменты
- `app/services/lead_store.py` — простое сохранение заявок
- `tests/test_guards.py` — базовые тесты

## 1. Установка

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните ключи в `.env`:
- `OPENAI_API_KEY`
- `BRAVE_SEARCH_API_KEY`
- `PIXABAY_API_KEY`

## 2. Подготовьте базу знаний

Создайте папку `knowledge_base/` и положите туда:
- `.txt`
- `.md`
- `.pdf`
- `.docx`

Пример:

```text
knowledge_base/
  ai_overview.md
  cyber_basics.pdf
  services.docx
```

## 3. Индексация базы знаний

```bash
python -m app.rag.ingest
```

## 4. Запуск API

```bash
uvicorn app.main:app --reload
```

Проверка:

- health: `GET /health`
- chat: `POST /chat`

## 5. Пример запроса

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session-1",
    "message": "Что такое RAG и где он полезен?",
    "user_name": "Александр",
    "user_email": "alex@example.com",
    "history": []
  }'
```

## 6. Как работает маршрут

1. `route_input` определяет intent и риск.
2. Для `kb` выполняется `retrieve_kb`.
3. Если KB уверенная — `answer_from_kb`.
4. Если KB слабая — `fallback_web_search` -> `answer_from_web`.
5. Для `image` выполняется поиск изображений.
6. Для `lead` сохраняется заявка.
7. Для `off_topic` и `unsafe` возвращается контролируемый отказ.

## 7. Что важно доработать перед production

1. Подключить нормальную CRM вместо файла `jsonl`.
2. Сделать auth/rate limiting.
3. Добавить red teaming и evals.
4. Заменить rule-based guardrails на гибрид rule + LLM policy.
5. Добавить reranker и quality benchmark для RAG.
6. Добавить observability: traces, latency, prompt versions.

## 8. Что можно улучшить быстро

- хранить историю диалога в Redis/PostgreSQL;
- добавить phone/company/consent в лиды;
- сделать allowlist веб-доменов;
- добавить citations в UI;
- внедрить human handoff.
