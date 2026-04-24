import json
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="SMS Spam Classifier (Lab 2)",
    description="FastAPI-обертка над Ollama/Qwen2.5:0.5b для классификации SMS.",
    version="1.1.0",
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
REQUEST_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT_SEC", "60"))

SYSTEM_PROMPT = """Ты — классификатор SMS для оператора связи.
Определи, является ли сообщение спамом.

Классы:
- SPAM: реклама, фишинг, обещания призов, подозрительные ссылки, навязчивые офферы.
- HAM: личная переписка, OTP/коды, сервисные уведомления доставки/банка.

Верни СТРОГО JSON:
{
  "label": "SPAM" или "HAM",
  "confidence": число от 0.0 до 1.0,
  "reason": "краткое обоснование"
}
Без markdown и без дополнительного текста."""


class SMSRequest(BaseModel):
    """Входные данные для классификации SMS."""

    message: str = Field(..., min_length=1, description="Текст SMS для классификации")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "Поздравляем! Вы выиграли приз, перейдите по ссылке bit.ly/win"}
            ]
        }
    }


class ClassifyResponse(BaseModel):
    """Ответ классификатора SMS."""

    label: str
    confidence: float
    reason: str
    model: str


class ProxyRequest(BaseModel):
    """Вход для прямого проксирования запроса в Ollama."""

    prompt: str = Field(..., min_length=1)
    system: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.5)


class ProxyResponse(BaseModel):
    """Ответ прокси-эндпоинта."""

    response: str
    model: str


async def call_ollama(payload: dict) -> dict:
    """Отправляет запрос в Ollama и возвращает JSON-ответ сервера."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Превышено время ожидания ответа Ollama") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ошибка Ollama: {exc}") from exc


def parse_classification(raw_text: str) -> tuple[str, float, str]:
    """Извлекает label/confidence/reason из текстового ответа модели."""
    try:
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        parsed = json.loads(raw_text[start:end])
        label = str(parsed.get("label", "UNKNOWN")).upper().strip()
        if label not in {"SPAM", "HAM"}:
            label = "UNKNOWN"
        confidence = float(parsed.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
        reason = str(parsed.get("reason", "Модель не вернула обоснование")).strip()
        return label, round(confidence, 3), reason
    except (json.JSONDecodeError, ValueError, TypeError):
        return "UNKNOWN", 0.0, raw_text.strip() or "Пустой ответ модели"


@app.get("/health")
async def health() -> dict:
    """Проверяет доступность Ollama и список загруженных моделей."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
        return {"status": "ok", "ollama": "reachable", "loaded_models": models, "target_model": MODEL}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama недоступна: {exc}") from exc


@app.post("/infer", response_model=ClassifyResponse)
async def infer_sms(req: SMSRequest) -> ClassifyResponse:
    """Основной endpoint лабораторной: классификация SMS как SPAM/HAM."""
    payload = {
        "model": MODEL,
        "prompt": f"SMS:\n\"{req.message}\"",
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    ollama_json = await call_ollama(payload)
    raw_text = ollama_json.get("response", "")
    label, confidence, reason = parse_classification(raw_text)
    return ClassifyResponse(label=label, confidence=confidence, reason=reason, model=MODEL)


@app.post("/classify", response_model=ClassifyResponse)
async def classify_sms(req: SMSRequest) -> ClassifyResponse:
    """Совместимый алиас для /infer (оставлен для удобства тестов)."""
    return await infer_sms(req)


@app.post("/proxy", response_model=ProxyResponse)
async def proxy_to_ollama(req: ProxyRequest) -> ProxyResponse:
    """Проксирует произвольный prompt в Ollama для ручной проверки модели."""
    payload = {
        "model": MODEL,
        "prompt": req.prompt,
        "stream": False,
        "options": {"temperature": req.temperature},
    }
    if req.system:
        payload["system"] = req.system

    ollama_json = await call_ollama(payload)
    return ProxyResponse(response=ollama_json.get("response", ""), model=MODEL)
