# document-gateway
# TODO: update readme
Сервис документов: создание, обновление, удаление документов.

## Запуск

1. Запустить PostgreSQL
2. Запустить Redis
3. Запустить:

```bash
poetry install
poetry run alembic upgrade head 
poetry run uvicorn src.cli.fastapi_app:app --reload --port 8002
```

API доступен по адресу: <http://localhost:8002>

## Структура

## Структура

```text
document-gateway
├── src/
│   ├── domains/          # модель Document, интерфейсы, сервис
│   ├── dto/              # команды и события
│   ├── gateway/          # схемы для FastAPI
│   ├── infrastructure/   # ORM, UoW, middleware
│   └── cli/              # fastapi_app и demo_app
└── README.md
```

## Возможности

Создание нового документа
Получение списка и профиля
Обновление документа
Удаление документа

## Observability

Логи → Logstash
Метрики → Prometheus /metrics
Аудит операций

---