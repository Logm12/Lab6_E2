from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    endpoint: str
    api_key: str
    model_name: str
    embed_model_name: str
    embed_dim: int
    router_mode: str
    router_model: str
    elicitation_mode: str
    elicitation_model: str
    off_topic_mode: str
    off_topic_model: str
    synthesizer_mode: str
    synthesizer_model: str
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str
    qdrant_timeout_s: float
    timeout_s: float
    openrouter_site_url: str
    openrouter_site_name: str


def _env(key: str, default: str = "") -> str:
    v = os.getenv(key)
    return default if v is None else str(v)


def _env_opt(key: str) -> Optional[str]:
    v = os.getenv(key)
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _strip_quotes(v: str) -> str:
    s = v.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"'}:
        return s[1:-1]
    return s


def _load_dotenv_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[len("export ") :].strip()
        if "=" not in s:
            continue
        key, value = s.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _strip_quotes(value)


def _load_dotenv_if_present() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        load_dotenv = None

    config_path = Path(__file__).resolve()
    repo_root = config_path.parents[3]
    candidates = [
        repo_root / ".env",
        repo_root / "backend" / ".env",
    ]
    for p in candidates:
        if not p.exists() or not p.is_file():
            continue
        if load_dotenv is not None:
            try:
                load_dotenv(dotenv_path=str(p), override=False)
                return
            except Exception:
                pass
        _load_dotenv_file(p)
        return


def get_settings() -> Settings:
    _load_dotenv_if_present()
    endpoint = _env("ENDPOINT", "https://api.openai.com/v1").rstrip("/")
    api_key = _env("OPENAI_API_KEY") or _env("OPENROUTER_API_KEY")
    model_name = _env("MODEL_NAME", "gpt-5.1-mini")
    embed_model_name = _env("EMBED_MODEL_NAME") or _env("EMBEDDING_MODEL") or "text-embedding-3-small"
    embed_dim = int(_env("EMBED_DIM", "256"))
    router_mode = (_env_opt("VINFAST_ROUTER_MODE") or ("llm" if api_key else "heuristic")).lower()
    router_model = _env("VINFAST_ROUTER_MODEL") or model_name
    elicitation_mode = (_env_opt("VINFAST_ELICITATION_MODE") or ("llm" if api_key else "heuristic")).lower()
    elicitation_model = _env("VINFAST_ELICITATION_MODEL") or model_name
    off_topic_mode = (_env_opt("VINFAST_OFFTOPIC_MODE") or ("llm" if api_key else "heuristic")).lower()
    off_topic_model = _env("VINFAST_OFFTOPIC_MODEL") or model_name
    synthesizer_mode = (_env_opt("VINFAST_SYNTHESIZER_MODE") or ("llm" if api_key else "heuristic")).lower()
    synthesizer_model = _env("VINFAST_SYNTHESIZER_MODEL") or model_name
    qdrant_url = _env("QDRANT_URL", "http://localhost:6333").rstrip("/")
    qdrant_api_key = _env("QDRANT_API_KEY")
    qdrant_collection = _env("QDRANT_COLLECTION", "vinfast_corpus")
    qdrant_timeout_s = float(_env("QDRANT_TIMEOUT_S", "2"))
    timeout_s = float(_env("LLM_TIMEOUT_S", "20"))
    openrouter_site_url = _env("OPENROUTER_SITE_URL")
    openrouter_site_name = _env("OPENROUTER_SITE_NAME")
    return Settings(
        endpoint=endpoint,
        api_key=api_key,
        model_name=model_name,
        embed_model_name=embed_model_name,
        embed_dim=embed_dim,
        router_mode=router_mode,
        router_model=router_model,
        elicitation_mode=elicitation_mode,
        elicitation_model=elicitation_model,
        off_topic_mode=off_topic_mode,
        off_topic_model=off_topic_model,
        synthesizer_mode=synthesizer_mode,
        synthesizer_model=synthesizer_model,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
        qdrant_collection=qdrant_collection,
        qdrant_timeout_s=qdrant_timeout_s,
        timeout_s=timeout_s,
        openrouter_site_url=openrouter_site_url,
        openrouter_site_name=openrouter_site_name,
    )


settings = get_settings()
