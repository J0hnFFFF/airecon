"""Unified AI Client for AIRecon, supporting Ollama, OpenAI, Anthropic, Google, and DeepSeek."""

from __future__ import annotations

import logging
import json
import asyncio
from typing import Any, AsyncIterator, Protocol

import ollama
import openai
import anthropic
# genai is not always available or namespaced differently, but we checked it exists
import google.generativeai as genai
from .config import get_config

logger = logging.getLogger("airecon.ai_client")

# ── Retry helper for cloud providers ────────────────────────────────────────
# Cloud APIs (OpenAI, Anthropic, DeepSeek) can return transient errors:
#   429 Too Many Requests — rate limit
#   500/503 — server-side overload
# Without retries the whole Agent session would crash on a transient blip.
_CLOUD_RETRY_ATTEMPTS = 3
_CLOUD_RETRY_BASE_DELAY = 1.0   # seconds; doubles each attempt (1s → 2s → 4s)
_CLOUD_RETRIABLE_CODES = {429, 500, 502, 503, 504}


async def _cloud_retry(coro_fn, *args, **kwargs):
    """Call an async callable up to _CLOUD_RETRY_ATTEMPTS times with exponential back-off.

    On a retriable error (rate limit, server error) we wait and retry.
    On a non-retriable error (auth, bad request, etc.) we raise immediately.
    """
    delay = _CLOUD_RETRY_BASE_DELAY
    for attempt in range(_CLOUD_RETRY_ATTEMPTS):
        try:
            return await coro_fn(*args, **kwargs)
        except openai.RateLimitError as e:
            if attempt < _CLOUD_RETRY_ATTEMPTS - 1:
                logger.warning(f"OpenAI rate limited — retrying in {delay:.0f}s (attempt {attempt+1}/{_CLOUD_RETRY_ATTEMPTS})")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise
        except openai.APIStatusError as e:
            if e.status_code in _CLOUD_RETRIABLE_CODES and attempt < _CLOUD_RETRY_ATTEMPTS - 1:
                logger.warning(f"OpenAI API error {e.status_code} — retrying in {delay:.0f}s (attempt {attempt+1}/{_CLOUD_RETRY_ATTEMPTS})")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise
        except anthropic.RateLimitError as e:
            if attempt < _CLOUD_RETRY_ATTEMPTS - 1:
                logger.warning(f"Anthropic rate limited — retrying in {delay:.0f}s (attempt {attempt+1}/{_CLOUD_RETRY_ATTEMPTS})")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise
        except anthropic.APIStatusError as e:
            if e.status_code in _CLOUD_RETRIABLE_CODES and attempt < _CLOUD_RETRY_ATTEMPTS - 1:
                logger.warning(f"Anthropic API error {e.status_code} — retrying in {delay:.0f}s (attempt {attempt+1}/{_CLOUD_RETRY_ATTEMPTS})")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise


class AIClient(Protocol):
    """Unified interface for all AI providers."""
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        options: dict[str, Any] | None = None,
        think: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        ...

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        ...

    @property
    def supports_thinking(self) -> bool:
        ...

    @property
    def supports_native_tools(self) -> bool:
        ...

    async def close(self) -> None:
        ...

    async def health_check(self) -> bool:
        ...

    async def unload_model(self) -> None:
        ...

class OllamaProvider:
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.client = ollama.AsyncClient(host=base_url)
        self._supports_thinking = True 
        self._supports_native_tools = True

    @property
    def supports_thinking(self) -> bool: return self._supports_thinking

    @property
    def supports_native_tools(self) -> bool: return self._supports_native_tools

    async def chat_stream(self, messages, tools=None, options=None, think=False) -> AsyncIterator[dict[str, Any]]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": get_config().ollama_keep_alive,
        }
        if think: kwargs["think"] = think
        if tools: kwargs["tools"] = tools
        if options: kwargs["options"] = options

        async for chunk in await self.client.chat(**kwargs):
            if hasattr(chunk, "model_dump"):
                yield chunk.model_dump()
            else:
                yield dict(chunk)

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        response = await self.client.chat(model=self.model, messages=messages, stream=False)
        return response.message.content or ""

    async def close(self): pass
    async def health_check(self) -> bool:
        try:
            await self.client.list()
            return True
        except: return False
    async def unload_model(self) -> None:
        try: await self.client.generate(model=self.model, prompt="", keep_alive=0)
        except: pass

class OpenAIProvider:
    def __init__(self, api_key: str, model: str, base_url: str):
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def supports_thinking(self) -> bool: return "o1" in self.model or "o3" in self.model
    @property
    def supports_native_tools(self) -> bool: return True

    async def chat_stream(self, messages, tools=None, options=None, think=False) -> AsyncIterator[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if tools: kwargs["tools"] = tools

        # Wrap creation in retry helper — handles 429 / 5xx transparently
        response = await _cloud_retry(self.client.chat.completions.create, **kwargs)
        async for chunk in response:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            yield {
                "message": {
                    "content": delta.content or "",
                    "tool_calls": [{"function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in delta.tool_calls] if delta.tool_calls else None
                }
            }

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        response = await _cloud_retry(
            self.client.chat.completions.create,
            model=self.model, messages=messages, stream=False
        )
        return response.choices[0].message.content or ""

    async def close(self): pass
    async def health_check(self) -> bool: return True
    async def unload_model(self) -> None: pass

class AnthropicProvider:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    @property
    def supports_thinking(self) -> bool: return "claude-3-5" in self.model
    @property
    def supports_native_tools(self) -> bool: return True

    async def chat_stream(self, messages, tools=None, options=None, think=False) -> AsyncIterator[dict[str, Any]]:
        anthropic_messages = []
        system_prompt = ""
        for m in messages:
            if m["role"] == "system": system_prompt += m["content"] + "\n"
            else: anthropic_messages.append(m)

        anthropic_tools = []
        if tools:
            for t in tools:
                anthropic_tools.append({
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"]
                })

        async def _do_stream():
            return self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
                messages=anthropic_messages,
                tools=anthropic_tools if anthropic_tools else anthropic.NOT_GIVEN
            )

        # Build a stream context with retry on rate-limit / server errors
        stream_ctx = await _cloud_retry(_do_stream)
        async with stream_ctx as stream:
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield {"message": {"content": event.delta.text}}
                elif event.type == "content_block_stop":
                    if event.content_block.type == "tool_use":
                        yield {
                            "message": {
                                "tool_calls": [{
                                    "function": {
                                        "name": event.content_block.name,
                                        "arguments": json.dumps(event.content_block.input)
                                    }
                                }]
                            }
                        }

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        anthropic_messages = [m for m in messages if m["role"] != "system"]
        system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")

        response = await _cloud_retry(
            self.client.messages.create,
            model=self.model,
            system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
            messages=anthropic_messages,
            max_tokens=4096
        )
        return response.content[0].text

    async def close(self): pass
    async def health_check(self) -> bool: return True
    async def unload_model(self) -> None: pass

def get_ai_client() -> AIClient:
    cfg = get_config()
    provider = cfg.ai_provider.lower()
    
    if provider == "ollama":
        return OllamaProvider(cfg.ollama_model, cfg.ollama_url)
    elif provider == "openai":
        return OpenAIProvider(cfg.openai_api_key, cfg.openai_model, cfg.openai_api_base)
    elif provider == "anthropic":
        return AnthropicProvider(cfg.anthropic_api_key, cfg.anthropic_model)
    elif provider == "deepseek":
        return OpenAIProvider(cfg.deepseek_api_key, cfg.deepseek_model, cfg.deepseek_api_base)
    elif provider == "google":
        # Google SDK implementation could be added here
        raise NotImplementedError("Google Gemini provider implementation pending")
    else:
        return OllamaProvider(cfg.ollama_model, cfg.ollama_url)
    """Unified interface for all AI providers."""
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        options: dict[str, Any] | None = None,
        think: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        ...

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        ...

    @property
    def supports_thinking(self) -> bool:
        ...

    @property
    def supports_native_tools(self) -> bool:
        ...

    async def close(self) -> None:
        ...

    async def health_check(self) -> bool:
        ...

    async def unload_model(self) -> None:
        ...

class OllamaProvider:
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.client = ollama.AsyncClient(host=base_url)
        self._supports_thinking = True 
        self._supports_native_tools = True

    @property
    def supports_thinking(self) -> bool: return self._supports_thinking

    @property
    def supports_native_tools(self) -> bool: return self._supports_native_tools

    async def chat_stream(self, messages, tools=None, options=None, think=False) -> AsyncIterator[dict[str, Any]]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": get_config().ollama_keep_alive,
        }
        if think: kwargs["think"] = think
        if tools: kwargs["tools"] = tools
        if options: kwargs["options"] = options

        async for chunk in await self.client.chat(**kwargs):
            if hasattr(chunk, "model_dump"):
                yield chunk.model_dump()
            else:
                yield dict(chunk)

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        response = await self.client.chat(model=self.model, messages=messages, stream=False)
        return response.message.content or ""

    async def close(self): pass
    async def health_check(self) -> bool:
        try:
            await self.client.list()
            return True
        except: return False
    async def unload_model(self) -> None:
        try: await self.client.generate(model=self.model, prompt="", keep_alive=0)
        except: pass

class OpenAIProvider:
    def __init__(self, api_key: str, model: str, base_url: str):
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def supports_thinking(self) -> bool: return "o1" in self.model or "o3" in self.model
    @property
    def supports_native_tools(self) -> bool: return True

    async def chat_stream(self, messages, tools=None, options=None, think=False) -> AsyncIterator[dict[str, Any]]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if tools: kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        async for chunk in response:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            yield {
                "message": {
                    "content": delta.content or "",
                    "tool_calls": [{"function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in delta.tool_calls] if delta.tool_calls else None
                }
            }

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        response = await self.client.chat.completions.create(model=self.model, messages=messages, stream=False)
        return response.choices[0].message.content or ""

    async def close(self): pass
    async def health_check(self) -> bool: return True
    async def unload_model(self) -> None: pass

class AnthropicProvider:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    @property
    def supports_thinking(self) -> bool: return "claude-3-5" in self.model
    @property
    def supports_native_tools(self) -> bool: return True

    async def chat_stream(self, messages, tools=None, options=None, think=False) -> AsyncIterator[dict[str, Any]]:
        anthropic_messages = []
        system_prompt = ""
        for m in messages:
            if m["role"] == "system": system_prompt += m["content"] + "\n"
            else: anthropic_messages.append(m)

        anthropic_tools = []
        if tools:
            for t in tools:
                anthropic_tools.append({
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"]
                })

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
            messages=anthropic_messages,
            tools=anthropic_tools if anthropic_tools else anthropic.NOT_GIVEN
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield {"message": {"content": event.delta.text}}
                elif event.type == "content_block_stop":
                    if event.content_block.type == "tool_use":
                        yield {
                            "message": {
                                "tool_calls": [{
                                    "function": {
                                        "name": event.content_block.name,
                                        "arguments": json.dumps(event.content_block.input)
                                    }
                                }]
                            }
                        }

    async def complete(self, messages: list[dict[str, Any]]) -> str:
        anthropic_messages = [m for m in messages if m["role"] != "system"]
        system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
        response = await self.client.messages.create(
            model=self.model,
            system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
            messages=anthropic_messages,
            max_tokens=4096
        )
        return response.content[0].text

    async def close(self): pass
    async def health_check(self) -> bool: return True
    async def unload_model(self) -> None: pass

def get_ai_client() -> AIClient:
    cfg = get_config()
    provider = cfg.ai_provider.lower()
    
    if provider == "ollama":
        return OllamaProvider(cfg.ollama_model, cfg.ollama_url)
    elif provider == "openai":
        return OpenAIProvider(cfg.openai_api_key, cfg.openai_model, cfg.openai_api_base)
    elif provider == "anthropic":
        return AnthropicProvider(cfg.anthropic_api_key, cfg.anthropic_model)
    elif provider == "deepseek":
        return OpenAIProvider(cfg.deepseek_api_key, cfg.deepseek_model, cfg.deepseek_api_base)
    elif provider == "google":
        # Google SDK implementation could be added here
        raise NotImplementedError("Google Gemini provider implementation pending")
    else:
        return OllamaProvider(cfg.ollama_model, cfg.ollama_url)
