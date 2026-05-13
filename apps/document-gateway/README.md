# document-gateway
Сервис документов: создание, обновление, удаление документов.

## Запуск

1. Запустить PostgreSQL
2. Запустить Redis
3. Запустить:

```bash
pyenv install 3.12
poetry install
poetry run uvicorn src.fastapi_app:app --port 8002
```

API доступен по адресу: <http://localhost:8002>

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