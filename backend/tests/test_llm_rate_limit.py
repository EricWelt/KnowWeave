"""LLM 客户端限流测试：429 感知重试 + 全局最小间隔。"""
import pytest

from backend import config
from backend.agent.llm_client import (
    LLMClient,
    _build_provider_config,
    _extract_retry_after_seconds,
    _is_rate_limit,
)


def test_extract_retry_after_from_message():
    e = Exception("Error code: 429 - please try again after 7 seconds")
    assert _extract_retry_after_seconds(e) == 7.0


def test_extract_retry_after_none():
    e = Exception("timeout")
    assert _extract_retry_after_seconds(e) is None


def test_is_rate_limit():
    assert _is_rate_limit(Exception("Error code: 429 - rate_limit_reached_error"))
    assert _is_rate_limit(Exception("engine_overloaded_error"))
    assert not _is_rate_limit(Exception("Connection timed out"))
    assert not _is_rate_limit(Exception("invalid json"))


async def test_chat_retries_on_rate_limit(monkeypatch):
    """429 时应按服务端建议等待后重试，最终成功。"""
    monkeypatch.setattr(config, "LLM_MIN_INTERVAL", 0)  # 关闭全局节流
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(s)

    monkeypatch.setattr("backend.agent.llm_client.asyncio.sleep", fake_sleep)

    client = LLMClient(
        api_key="test", base_url="http://test", model="m", max_retries=2
    )
    client.min_interval = 0.0  # 测试中关闭节流
    calls = {"n": 0}

    class FakeMsg:
        content = "ok"

    class FakeChoice:
        message = FakeMsg()

    class FakeResp:
        choices = [FakeChoice()]

    async def fake_create(**kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise Exception("Error code: 429 - please try again after 2 seconds")
        return FakeResp()

    client._client.chat.completions.create = fake_create
    result = await client.chat([{"role": "user", "content": "hi"}])
    assert result == "ok"
    assert calls["n"] == 3
    # 限流退避应 >= 解析到的等待时间（+1 余量）
    assert len(sleeps) == 2
    assert all(s >= 3 for s in sleeps)


async def test_chat_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr(config, "LLM_MIN_INTERVAL", 0)

    async def fake_sleep(s):
        pass

    monkeypatch.setattr("backend.agent.llm_client.asyncio.sleep", fake_sleep)

    client = LLMClient(
        api_key="test", base_url="http://test", model="m", max_retries=1
    )
    client.min_interval = 0.0

    async def fake_create(**kwargs):
        raise Exception("Error code: 429 - rate_limit_reached_error")

    client._client.chat.completions.create = fake_create
    with pytest.raises(RuntimeError, match="最终失败"):
        await client.chat([{"role": "user", "content": "hi"}])

# ==================== 模型注册表 ====================


def test_registry_resolves_minimax_m3(monkeypatch):
    monkeypatch.setattr(config, "LLM_MODEL", "minimax-m3")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    cfg = _build_provider_config()
    assert cfg["model"] == "minimaxai/minimax-m3"
    assert "integrate.api.nvidia.com" in cfg["base_url"]
    assert cfg["api_key"] == "nvapi-test"


def test_registry_resolves_moonshot_128k(monkeypatch):
    monkeypatch.setattr(config, "LLM_MODEL", "moonshot-128k")
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-test")
    cfg = _build_provider_config()
    assert cfg["model"] == "moonshot-v1-128k"
    assert cfg["min_interval"] == 21  # Kimi 低 RPM 账户的预算


def test_registry_unknown_model_raises(monkeypatch):
    monkeypatch.setattr(config, "LLM_MODEL", "no-such-model")
    with pytest.raises(ValueError, match="no-such-model"):
        _build_provider_config()


def test_explicit_provider_still_works(monkeypatch):
    # 向后兼容：显式 provider 参数走旧逻辑
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-test")
    cfg = _build_provider_config("moonshot")
    assert cfg["provider"] == "moonshot"
    assert cfg["model"] == config.MOONSHOT_MODEL
async def test_429_without_retry_info_bounded_backoff(monkeypatch):
    """NVIDIA 格式 429（无 Retry-After）→ 短退避而非 31s，快速失败。"""
    monkeypatch.setattr(config, "LLM_MIN_INTERVAL", 0)
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(s)

    monkeypatch.setattr("backend.agent.llm_client.asyncio.sleep", fake_sleep)

    client = LLMClient(
        api_key="test", base_url="http://test", model="m", max_retries=2
    )
    client.min_interval = 0.0

    async def fake_create(**kwargs):
        raise Exception(
            "Error code: 429 - {'status': 429, 'title': 'Too Many Requests'}"
        )

    client._client.chat.completions.create = fake_create
    with pytest.raises(RuntimeError):
        await client.chat([{"role": "user", "content": "hi"}])
    # 每次重试等待 <= 10s（而非 31s/60s）
    assert sleeps and all(s <= 10 for s in sleeps)

def test_registry_resolves_glm52(monkeypatch):
    """默认模型 glm-5.2（NVIDIA）应正确解析。"""
    monkeypatch.setattr(config, "LLM_MODEL", "glm-5.2")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    cfg = _build_provider_config()
    assert cfg["model"] == "z-ai/glm-5.2"
    assert "integrate.api.nvidia.com" in cfg["base_url"]

def test_registry_resolves_qwen_coder_30b(monkeypatch):
    """默认模型 qwen3-coder-30b（ModelScope）应正确解析。"""
    monkeypatch.setattr(config, "LLM_MODEL", "qwen3-coder-30b")
    monkeypatch.setenv("MODELSCOPE_API_KEY", "ms-test")
    cfg = _build_provider_config()
    assert cfg["model"] == "Qwen/Qwen3-Coder-30B-A3B-Instruct"
    assert "modelscope" in cfg["base_url"]
    assert cfg["min_interval"] == 1.0
