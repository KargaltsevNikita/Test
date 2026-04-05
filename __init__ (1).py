"""Deterministic safety and routing checks.

We keep these checks simple and transparent. In production you can extend them
with an LLM-based policy classifier, but a deterministic baseline is easier to
review and test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.agent.state import RouteName


DOMAIN_KEYWORDS = {
    "ии",
    "ai",
    "ml",
    "llm",
    "rag",
    "агент",
    "кибербезопас",
    "информационн",
    "безопасност",
    "защита",
    "модель",
    "нейросет",
    "prompt",
    "langchain",
    "langgraph",
    "сайт",
    "заявк",
    "менеджер",
}

LEAD_KEYWORDS = {
    "оставить заявку",
    "связаться",
    "менеджер",
    "консультац",
    "перезвон",
    "зарегистрир",
    "demo",
    "демо",
}

IMAGE_KEYWORDS = {
    "картинк",
    "изображен",
    "иллюстрац",
    "фото",
    "покажи",
}

WEB_HINT_KEYWORDS = {
    "свеж",
    "новост",
    "последн",
    "latest",
    "today",
    "сегодня",
    "интернет",
    "веб",
}

UNSAFE_PATTERNS = [
    r"phishing",
    r"sql\s*injection",
    r"xss",
    r"ransomware",
    r"ddos",
    r"steal\s+password",
    r"украсть\s+данные",
    r"обойти\s+защит",
    r"взлома?ть",
    r"эксплойт",
    r"malware",
    r"кейлоггер",
    r"ботнет",
]


@dataclass(slots=True)
class GuardResult:
    safe: bool
    route: RouteName
    reason: str


class Guardrails:
    """Simple policy engine for the MVP."""

    def check(self, text: str) -> GuardResult:
        normalized = text.lower().strip()

        # 1) Reject clearly unsafe cyber-abuse requests.
        for pattern in UNSAFE_PATTERNS:
            if re.search(pattern, normalized):
                return GuardResult(safe=False, route="unsafe", reason=f"matched:{pattern}")

        # 2) Route commercial intent to lead capture.
        if any(keyword in normalized for keyword in LEAD_KEYWORDS):
            return GuardResult(safe=True, route="lead", reason="lead intent")

        # 3) Route image requests.
        if any(keyword in normalized for keyword in IMAGE_KEYWORDS):
            return GuardResult(safe=True, route="image", reason="image intent")

        # 4) Only allow domain-relevant traffic.
        if not any(keyword in normalized for keyword in DOMAIN_KEYWORDS):
            return GuardResult(safe=True, route="off_topic", reason="outside allowed domain")

        # 5) If the user explicitly asks for fresh/current info, prefer web fallback.
        if any(keyword in normalized for keyword in WEB_HINT_KEYWORDS):
            return GuardResult(safe=True, route="web", reason="freshness requested")

        # 6) Default route goes through knowledge base first.
        return GuardResult(safe=True, route="kb", reason="domain question")
