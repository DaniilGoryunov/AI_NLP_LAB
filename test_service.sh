#!/bin/bash

BASE="http://localhost:8000"
SEP="────────────────────────────────────────"

echo ""
echo "$SEP"
echo "  1. Healthcheck"
echo "$SEP"
curl -s "$BASE/health" | python3 -m json.tool

echo ""
echo "$SEP"
echo "  2. SPAM example — fake prize"
echo "$SEP"
curl -s -X POST "$BASE/infer" \
  -H "Content-Type: application/json" \
  -d '{"message": "Congratulations! You have been selected for a $1000 gift card. Claim now: http://bit.ly/claim-prize"}' \
  | python3 -m json.tool

echo ""
echo "$SEP"
echo "  3. HAM example — OTP code"
echo "$SEP"
curl -s -X POST "$BASE/infer" \
  -H "Content-Type: application/json" \
  -d '{"message": "Your verification code is 847291. It expires in 5 minutes. Do not share it with anyone."}' \
  | python3 -m json.tool

echo ""
echo "$SEP"
echo "  4. SPAM example (Russian) — loan offer"
echo "$SEP"
curl -s -X POST "$BASE/infer" \
  -H "Content-Type: application/json" \
  -d '{"message": "Срочный займ до 100 000 руб без справок! Одобрение за 5 минут. Звоните: 8-800-555-00-11"}' \
  | python3 -m json.tool

echo ""
echo "$SEP"
echo "  5. HAM example (Russian) — delivery"
echo "$SEP"
curl -s -X POST "$BASE/infer" \
  -H "Content-Type: application/json" \
  -d '{"message": "Ваш заказ №48291 передан в доставку. Ожидайте курьера 22 апреля с 10:00 до 14:00."}' \
  | python3 -m json.tool

echo ""
echo "$SEP"
echo "  6. Proxy endpoint — direct Ollama passthrough"
echo "$SEP"
curl -s -X POST "$BASE/proxy" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2? Answer in one word.", "temperature": 0.0}' \
  | python3 -m json.tool

echo ""
echo "Done! Check Swagger UI at: $BASE/docs"
echo ""
