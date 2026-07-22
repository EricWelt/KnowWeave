"""LLM 客户端：统一封装 OpenAI SDK 兼容接口。

支持双 provider（config.LLM_PROVIDER 切换）：
- moonshot:  base_url=https://api.moonshot.cn/v1
- modelscope: base_url=https://api-inference.modelscope.cn/v1/

设计要点：
- 项目中**只有这个模块**直接调用 OpenAI SDK；
- 用 AsyncOpenAI（非阻塞，适合 async 路由）；
- 每次调用传入完整 messages（状态由 engine 管理，不依赖 SDK 会话）；
- timeout=60s，失败重试 max_retries 次；
- **限流感知（真实踩坑）**：Moonshot 免费账户 org max RPM 很小（如 3 次/分钟），
  ReAct 一次会话要连发 5-15 次调用必然触发 429。对策：
  1) 解析 429 的 Retry-After / 错误消息里的等待秒数并真正等待；
  2) 全局最小调用间隔（LLM_MIN_INTERVAL，默认 21s ≈ 3 RPM 预算）主动限速。
"""
import asyncio
import logging
import os
import re
import time
from threading import Lock

from .. import config

logger = logging.getLogger(__name__)

# 账户级 RPM 预算的全局节流状态：按 api_key 分别计数（不同 provider 互不影响）
_ratelimit_lock = Lock()
_last_request_ts_by_key: dict[str, float] = {}


def _build_provider_config(provider: str | None = None) -> dict:
    """解析 LLM 连接配置。

    优先顺序：
    1. 显式传入 provider（向后兼容，极少用）→ 走旧逻辑；
    2. config.LLM_MODEL（模型注册表名称，如 "minimax-m3"）→ 取注册表项；
    3. 兜底：config.LLM_PROVIDER 的旧逻辑。
    返回 dict：{provider, api_key, base_url, model, min_interval}
    """
    if provider is not None:
        if provider == "moonshot":
            return {
                "provider": "moonshot",
                "api_key": config.MOONSHOT_API_KEY,
                "base_url": config.MOONSHOT_BASE_URL,
                "model": config.MOONSHOT_MODEL,
                "min_interval": config.LLM_MIN_INTERVAL,
            }
        if provider == "modelscope":
            return {
                "provider": "modelscope",
                "api_key": config.MODELSCOPE_API_KEY,
                "base_url": config.MODELSCOPE_BASE_URL,
                "model": config.MODELSCOPE_MODEL,
                "min_interval": config.LLM_MIN_INTERVAL,
            }
        raise ValueError(f"未知 LLM_PROVIDER: {provider}")

    # 模型注册表（推荐）
    name = config.LLM_MODEL
    entry = config.LLM_MODELS.get(name)
    if entry is None:
        raise ValueError(
            f"未知 LLM_MODEL: {name!r}，可用: {sorted(config.LLM_MODELS)}"
        )
    return {
        "provider": name,
        "api_key": os.environ.get(entry["api_key_env"], ""),
        "base_url": entry["base_url"],
        "model": entry["model"],
        "min_interval": (
            config.LLM_MIN_INTERVAL
            if config.LLM_MIN_INTERVAL > 0
            else entry.get("min_interval", 0)
        ),
    }


def _extract_retry_after_seconds(error: Exception) -> float | None:
    """从限流错误中解析建议等待秒数：优先 Retry-After 头，其次错误消息。"""
    resp = getattr(error, "response", None)
    if resp is not None:
        headers = getattr(resp, "headers", None) or {}
        ra = headers.get("Retry-After")
        if ra:
            try:
                return float(ra)
            except (TypeError, ValueError):
                pass
    m = re.search(
        r"please try again after\s+([\d.]+)\s*seconds?",
        str(error),
        re.IGNORECASE,
    )
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _is_rate_limit(error: Exception) -> bool:
    """是否限流/过载类错误（429 / rate_limit / overloaded）。"""
    text = str(error).lower()
    return "429" in text or "rate_limit" in text or "overloaded" in text


def _error_diagnostic(error: Exception) -> str:
    """从 SDK 异常中提取诊断信息（状态码 + 限流头 + 响应体片段）。

    真实踩坑：NVIDIA 返回 RFC9457 格式 429（{'status':429,'title':'Too Many
    Requests'}），不带 Retry-After；是否有 x-ratelimit-* 头是判断
    「配额耗尽」还是「账户级限流」的关键线索，必须打进日志。
    """
    resp = getattr(error, "response", None)
    if resp is None:
        return str(error)[:300]
    try:
        status = getattr(resp, "status_code", None) or resp.status
    except Exception:  # noqa: BLE001
        status = "?"
    headers = getattr(resp, "headers", None) or {}
    rl_headers = {
        k: v
        for k, v in headers.items()
        if "ratelimit" in k.lower()
        or k.lower() in ("retry-after", "x-ratelimit-limit", "x-ratelimit-remaining")
    }
    try:
        body = getattr(resp, "text", "") or ""
    except Exception:  # noqa: BLE001
        body = ""
    return f"status={status} ratelimit_headers={rl_headers} body={body[:200]}"


async def _throttle(api_key: str, min_interval: float) -> None:
    """按 api_key 的最小调用间隔：确保相邻两次调用 >= min_interval 秒。

    锁内预留时间槽 + 单次 sleep（不用 while 自旋，避免时间不推进时死循环）。
    """
    if min_interval <= 0:
        return
    global _last_request_ts_by_key
    with _ratelimit_lock:
        now = time.monotonic()
        last = _last_request_ts_by_key.get(api_key, 0.0)
        wait = max(0.0, last + min_interval - now)
        # 预留下一次最早调用时间（并发调用者据此排队）
        _last_request_ts_by_key[api_key] = max(now, last + min_interval)
    if wait > 0:
        await asyncio.sleep(wait)


class LLMClient:
    """OpenAI 兼容 chat.completions 的薄封装。"""

    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ):
        from openai import AsyncOpenAI

        cfg = _build_provider_config(provider)
        self.provider = cfg["provider"]
        self.model = model or cfg["model"]
        self.temperature = (
            config.LLM_TEMPERATURE if temperature is None else temperature
        )
        self.timeout = config.LLM_TIMEOUT if timeout is None else timeout
        self.max_retries = config.LLM_MAX_RETRIES if max_retries is None else max_retries

        self._api_key = api_key or cfg["api_key"]
        self.min_interval = float(cfg.get("min_interval", config.LLM_MIN_INTERVAL))

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=base_url or cfg["base_url"],
            timeout=self.timeout,
        )

    async def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """调用 chat.completions 并返回 assistant 文本内容。失败抛异常。"""
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            # 每次调用前先遵守该账户的最小调用间隔（RPM 预算）
            await _throttle(self._api_key, self.min_interval)
            try:
                resp = await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=(
                        self.temperature if temperature is None else temperature
                    ),
                    max_tokens=max_tokens,
                )
                content = resp.choices[0].message.content
                if content is None:
                    raise RuntimeError("LLM 返回空内容")
                return content
            except Exception as e:  # noqa: BLE001 —— 网络/限流/格式错误统一重试
                last_error = e
                logger.warning(
                    "[llm] provider=%s attempt=%d 失败: %s",
                    self.provider, attempt + 1, _error_diagnostic(e),
                )
                if attempt < self.max_retries:
                    if _is_rate_limit(e):
                        # 限流：尊重服务端建议的等待时间；无建议时用短退避
                        # （长等待会让整个 Agent 会话拖到几分钟 → 前端连接被掐断，
                        #   且对 40 RPM 账户 min_interval 已做预算，无需长等）
                        wait = _extract_retry_after_seconds(e)
                        if wait is None:
                            wait = 2.0 ** attempt  # 1s, 2s …
                        wait = max(wait + 1.0, self.min_interval)
                        wait = min(wait, 10.0)  # 单次重试等待上限 10s，快速失败
                    else:
                        wait = 2 ** attempt  # 指数退避
                    await asyncio.sleep(wait)
        raise RuntimeError(f"LLM 调用最终失败: {last_error}") from last_error

    async def chat_json(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> object:
        """调用并防御性解析 JSON（planner/create_quiz 复用）。"""
        from .json_utils import parse_json_defensive

        text = await self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        return parse_json_defensive(text)