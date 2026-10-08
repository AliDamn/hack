# ClaimAI — Card Disputes, Automated (local)

Локальная копия https://rulebookrag.higgsfield.app/.

- **backend/** — FastAPI + SQLAlchemy 2.0, PostgreSQL (в Docker) или SQLite (без Docker)
- **frontend/** — React 18 + Vite (JavaScript), в Docker раздаётся через nginx
- **docker-compose.yml** — db + backend + frontend

## LLM (OpenAI)

Решения генерирует LLM через OpenAI API (`backend/app/llm.py`). Нужен ключ с https://platform.openai.com/api-keys:

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini   # необязательно
```

Если ключа нет или API недоступен, `/analyze` вернёт 502 с описанием ошибки.

## Запуск через Docker

```bash
docker compose up --build
```

- Сайт: http://localhost:8080
- API docs (Swagger): http://localhost:8000/docs

## Запуск без Docker

```bash
# backend (SQLite)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend (в другом терминале)
cd frontend
npm install
npm run dev        # http://localhost:5173, /api проксируется на :8000
```

## API

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/health` | Проверка |
| GET | `/api/cases` | Список кейсов (id, chip) |
| GET | `/api/cases/{id}` | Жалоба + транзакции |
| POST | `/api/cases/{id}/analyze` | Решение LLM; пишет запись в audit log |
| GET | `/api/audit` | Журнал аудита (operator_id, время, решение) |

Демо-кейсы (DSP-0847, 0846, 0844, 0841) засеваются в БД при первом старте — см. `backend/app/seed.py`.
