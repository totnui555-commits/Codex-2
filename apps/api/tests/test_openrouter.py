from agents import OpenAIChatCompletionsModel
from company_os.providers import research_credentials_configured, research_model_adapter
from company_os.settings import settings


def test_openrouter_uses_chat_adapter_without_direct_openai_key(monkeypatch):
    s = settings()
    monkeypatch.setattr(s, "model_provider", "openrouter")
    monkeypatch.setattr(s, "openrouter_api_key", "unit-test-only-not-a-real-key")
    monkeypatch.setattr(s, "research_model", "openai/gpt-4.1-mini")
    monkeypatch.setattr(s, "openai_api_key", "")
    assert research_credentials_configured()
    assert isinstance(research_model_adapter(), OpenAIChatCompletionsModel)


def test_unknown_provider_denied(monkeypatch):
    monkeypatch.setattr(settings(), "model_provider", "unapproved")
    assert not research_credentials_configured()


async def test_provider_billing_captures_response_cost_without_prompt_or_key():
    import httpx
    from company_os.providers import collect_provider_billing

    response = httpx.Response(
        200,
        json={
            "id": "generation-test",
            "model": "openai/gpt-4.1-mini",
            "usage": {"cost": 0.0005},
            "choices": [{"message": {"content": "private response"}}],
        },
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    billing = []
    await collect_provider_billing(response, billing)
    assert billing == [
        {"request_id": "generation-test", "model": "openai/gpt-4.1-mini", "cost_usd": "0.0005"}
    ]


def test_openrouter_codex_uses_scoped_gateway_provider_endpoint(monkeypatch):
    from company_os.providers import coding_provider_endpoint

    monkeypatch.setattr(settings(), "codex_provider", "openrouter")
    monkeypatch.setattr(settings(), "openrouter_api_key", "test-only")
    assert coding_provider_endpoint() == ("https://openrouter.ai/api/v1/responses", "test-only")
