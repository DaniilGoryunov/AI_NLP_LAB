# Лабораторная работа №2 (NLP), вариант на 4

**Студент:** Горюнов Даниил  
**Группа:** М8О-408б-22
**Тема PoC:** классификация SMS на `SPAM/HAM` с помощью LLM

## Что реализовано

- Docker-контейнер с `Python + FastAPI + Ollama`.
- В контейнере автоматически поднимается сервер Ollama.
- Автоматически скачивается и используется модель `qwen2.5:0.5b`.
- FastAPI-сервис оборачивает LLM и отдает результат по HTTP.
- Есть отдельный скрипт для проверки сервиса снаружи контейнера.

## Соответствие требованиям задания (на 4)

1. **Docker-контейнер (Ubuntu/Python base image, не slim):** есть `Dockerfile`.  
2. **Ollama + Qwen2.5:0.5B внутри контейнера:** поднимается в `start.sh`, модель загружается `ollama pull qwen2.5:0.5b`.  
3. **Проверка запросов к Ollama из терминала:** приведена команда в разделе проверки.  
4. **FastAPI-обертка:** реализована в `app/main.py`.  
5. **Проброс порта наружу:** `docker-compose.yml` пробрасывает `8000` и `11434`.  
6. **Проверка LLM-сервиса:** есть `test_service.sh` и ручные `curl` примеры.  
7. **Docstring функций:** добавлены в Python-коде сервиса.

## Структура проекта

- `app/main.py` — FastAPI API и вызовы Ollama.
- `Dockerfile` — сборка образа.
- `docker-compose.yml` — запуск сервиса и проброс портов.
- `start.sh` — старт Ollama + загрузка модели + запуск FastAPI.
- `test_service.sh` — smoke-тест API снаружи контейнера.

## Эндпоинты

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/health` | Проверка состояния сервиса и доступности Ollama |
| `POST` | `/infer` | Основной endpoint: классификация SMS (`SPAM/HAM`) |
| `POST` | `/classify` | Совместимый алиас для `/infer` |
| `POST` | `/proxy` | Прямая отправка произвольного prompt в Ollama |

## Запуск

```bash
docker compose up --build
```

После старта сервис доступен по адресу:  
- API: `http://localhost:8000`  
- Swagger: `http://localhost:8000/docs`

## Проверка внутри контейнера (прямой запрос к Ollama)

```bash
docker exec -it spam-llm-service bash
curl http://localhost:11434/api/tags
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:0.5b",
    "prompt": "Ответь одним словом: привет.",
    "stream": false
  }'
```

## Проверка сервиса снаружи контейнера

```bash
chmod +x test_service.sh
./test_service.sh
```

Или вручную:

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/infer \
  -H "Content-Type: application/json" \
  -d '{"message":"Поздравляем! Вы выиграли 5000 рублей, перейдите по ссылке bit.ly/win"}'

curl -X POST http://localhost:8000/infer \
  -H "Content-Type: application/json" \
  -d '{"message":"Ваш код подтверждения: 384922. Никому его не сообщайте."}'
```

## Результаты

```text
$ ./test_service.sh

────────────────────────────────────────
  1. Healthcheck
────────────────────────────────────────
{
    "status": "ok",
    "ollama": "reachable",
    "loaded_models": [
        "qwen2.5:0.5b"
    ],
    "target_model": "qwen2.5:0.5b"
}

────────────────────────────────────────
  2. SPAM example — fake prize
────────────────────────────────────────
{
    "label": "SPAM",
    "confidence": 0.9,
    "reason": "Сообщение содержит признаки рекламного/мошеннического предложения с подозрительной ссылкой.",
    "model": "qwen2.5:0.5b"
}

────────────────────────────────────────
  3. HAM example — OTP code
────────────────────────────────────────
{
    "label": "HAM",
    "confidence": 0.92,
    "reason": "Сервисное сообщение с одноразовым кодом подтверждения, без рекламных признаков.",
    "model": "qwen2.5:0.5b"
}

────────────────────────────────────────
  4. SPAM example (Russian) — loan offer
────────────────────────────────────────
{
    "label": "SPAM",
    "confidence": 0.88,
    "reason": "Навязчивое коммерческое предложение займа, характерное для спам-рассылок.",
    "model": "qwen2.5:0.5b"
}

────────────────────────────────────────
  5. HAM example (Russian) — delivery
────────────────────────────────────────
{
    "label": "HAM",
    "confidence": 0.86,
    "reason": "Обычное сервисное уведомление о доставке заказа.",
    "model": "qwen2.5:0.5b"
}

────────────────────────────────────────
  6. Proxy endpoint — direct Ollama passthrough
────────────────────────────────────────
{
    "response": "4",
    "model": "qwen2.5:0.5b"
}
```
## Краткий вывод

Сервис корректно разворачивается в Docker, принимает HTTP-запросы и использует `qwen2.5:0.5b` через Ollama для классификации SMS. Инженерная часть задания на 4 выполнена: контейнеризация, API-обертка, тестирование и воспроизводимый запуск.
