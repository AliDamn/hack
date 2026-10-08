import json
import os
import re

import httpx

OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))

SYSTEM_PROMPT = """Ты — движок ClaimAI для банковских споров по картам (чарджбэки). \
Тебе дают жалобу клиента и список транзакций. Примени правила платёжных сетей, \
политику банка и фрод-сигналы (3D-Secure, канал, время, дубликаты, серии операций) \
и прими решение. Пиши на русском.

Ответь СТРОГО одним JSON-объектом без пояснений и markdown, с полями:
{
  "type": "тип спора, например «Несанкционированная транзакция (фрод)»",
  "decision": "короткое решение, например «Автоматический возврат» или «Расследование»",
  "decision_class": "green (автоматическое решение в пользу клиента) | orange (нужно расследование) | red (отказ)",
  "risk": целое 0-100 (риск фрода),
  "confidence": целое 0-100 (уверенность в решении),
  "reasoning": "обоснование со ссылками на конкретные транзакции",
  "actions": ["список конкретных действий оператора"],
  "letter": "письмо клиенту: обращение, номер кейса, решение, следующие шаги, подпись службы"
}"""


class LLMError(Exception):
    pass


def _build_user_prompt(case_id: str, complaint: str, transactions: list[dict]) -> str:
    lines = [
        f"- {t['merchant']} | {t['amount']} | {t['date']} | аутентификация: {t['auth']} | канал: {t['channel']}"
        for t in transactions
    ]
    return f"Кейс: {case_id}\n\nЖалоба клиента:\n{complaint}\n\nТранзакции:\n" + "\n".join(lines)


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise LLMError("LLM did not return JSON")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise LLMError(f"LLM returned invalid JSON: {e}") from e


def _clamp(value, default: int) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return default


def _normalize(raw: dict) -> dict:
    try:
        decision_class = str(raw.get("decision_class", "orange")).lower()
        if decision_class not in {"green", "orange", "red"}:
            decision_class = "orange"
        actions = raw.get("actions") or []
        if isinstance(actions, str):
            actions = [actions]
        return {
            "type": str(raw["type"]),
            "decision": str(raw["decision"]),
            "decision_class": decision_class,
            "risk": _clamp(raw.get("risk"), 50),
            "confidence": _clamp(raw.get("confidence"), 50),
            "reasoning": str(raw["reasoning"]),
            "actions": [str(a) for a in actions],
            "letter": str(raw["letter"]),
        }
    except KeyError as e:
        raise LLMError(f"LLM response is missing field {e}") from e


def analyze_dispute(case_id: str, complaint: str, transactions: list[dict]) -> dict:
    token = os.getenv("OPENAI_API_KEY")
    if not token:
        raise LLMError("OPENAI_API_KEY is not set")

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(case_id, complaint, transactions)},
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
    }
    try:
        res = httpx.post(
            OPENAI_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=OPENAI_TIMEOUT,
        )
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise LLMError(f"OpenAI API {e.response.status_code}: {e.response.text[:300]}") from e
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        raise LLMError(f"OpenAI request failed: {e}") from e

    return _normalize(_extract_json(content))
