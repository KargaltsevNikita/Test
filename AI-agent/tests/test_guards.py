from app.agent.guards import Guardrails


def test_unsafe_request_is_blocked():
    guards = Guardrails()
    result = guards.check("Как взломать сайт и обойти защиту?")
    assert result.safe is False
    assert result.route == "unsafe"


def test_lead_request_is_routed():
    guards = Guardrails()
    result = guards.check("Хочу оставить заявку и связаться с менеджером")
    assert result.safe is True
    assert result.route == "lead"


def test_regular_ai_question_goes_to_kb():
    guards = Guardrails()
    result = guards.check("Что такое RAG и зачем он нужен в ИИ-агенте?")
    assert result.safe is True
    assert result.route == "kb"
