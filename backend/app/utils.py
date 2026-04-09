from __future__ import annotations

import json
import logging
import os
import sys
import re
import uuid
from pathlib import Path
from typing import Any, Optional


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    return project_root() / "data"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return int(value)
        s = str(value).strip()
        if not s:
            return None
        return int(float(s))
    except Exception:
        return None


_BUDGET_RE = re.compile(
    r"(?P<num>(?:\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?))\s*(?P<unit>tỷ|ty|trieu|triệu|m|tr|b|bn|vnd|đ|dong)?",
    flags=re.IGNORECASE,
)


def parse_budget_vnd(text: str) -> Optional[int]:
    matches = list(_BUDGET_RE.finditer(text))
    if not matches:
        return None
    best = None
    for m in matches:
        start = m.start("num")
        unit = (m.group("unit") or "").lower()
        if not unit and start > 0 and str(text[start - 1]).isalnum():
            continue
        raw_num = m.group("num").strip()
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", raw_num):
            raw = re.sub(r"[.,]", "", raw_num)
        else:
            raw = raw_num.replace(",", ".")
        try:
            num = float(raw)
        except ValueError:
            continue
        if unit in {"tỷ", "ty", "b", "bn"}:
            vnd = int(num * 1_000_000_000)
        elif unit in {"trieu", "triệu", "m", "tr"}:
            vnd = int(num * 1_000_000)
        elif unit in {"vnd", "đ", "dong"}:
            vnd = int(num)
        else:
            if num <= 20:
                vnd = int(num * 1_000_000_000)
            elif num <= 2000:
                vnd = int(num * 1_000_000)
            else:
                vnd = int(num)
        if best is None or vnd > best:
            best = vnd
    return best


def parse_seats(text: str) -> Optional[int]:
    m = re.search(r"(\d)\s*(?:chỗ|cho|seat|seats|người|nguoi)", text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def new_session_id() -> str:
    return uuid.uuid4().hex


_TRACE_LOGGER = logging.getLogger("app.trace")


def trace_enabled() -> bool:
    return os.environ.get("TRACE_STEPS", "1").strip() not in {"0", "false", "False", ""}


def debug_enabled(name: str) -> bool:
    v = os.environ.get(name, "").strip()
    return v in {"1", "true", "True", "yes", "YES", "y", "Y"}


def debug_print(flag: str, *args: Any) -> None:
    if debug_enabled(flag):
        try:
            print(*args, file=sys.stdout, flush=True)
        except Exception:
            pass



def trace_step(meta: dict[str, Any], *, step: str, data: dict[str, Any]) -> dict[str, Any]:
    trace = meta.get("trace")
    if not isinstance(trace, list):
        trace = []
    event: dict[str, Any] = {"step": step, **data}
    trace.append(event)
    meta["trace"] = trace
    if trace_enabled():
        try:
            _TRACE_LOGGER.info("%s", json.dumps(event, ensure_ascii=False))
        except Exception:
            _TRACE_LOGGER.info("%s", str(event))
        try:
            print(json.dumps({"trace": event}, ensure_ascii=False), file=sys.stdout, flush=True)
        except Exception:
            pass
    return meta


def extract_text_from_ui_message(msg: dict[str, Any]) -> str:
    parts = msg.get("parts")
    if isinstance(parts, list):
        out: list[str] = []
        for p in parts:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "text":
                out.append(str(p.get("text") or ""))
        joined = "".join(out).strip()
        if joined:
            return joined
    content = msg.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return ""


def extract_user_texts(ui_messages: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    prev: Optional[str] = None
    for m in ui_messages:
        if not isinstance(m, dict):
            continue
        if str(m.get("role") or "") != "user":
            continue
        t = extract_text_from_ui_message(m)
        if not t:
            continue
        if prev == t:
            continue
        out.append(t)
        prev = t
    return out


def last_user_text(ui_messages: list[dict[str, Any]]) -> str:
    for m in reversed(ui_messages):
        if not isinstance(m, dict):
            continue
        if str(m.get("role") or "") != "user":
            continue
        t = extract_text_from_ui_message(m)
        if t:
            return t
    return ""


def user_history_text(ui_messages: list[dict[str, Any]], *, max_turns: int = 10) -> str:
    texts = extract_user_texts(ui_messages)
    if len(texts) <= 1:
        return ""
    hist = texts[-int(max_turns) : -1]
    return "\n".join([t for t in hist if t.strip()]).strip()


def build_history_context(ui_messages: list[dict[str, Any]], *, max_messages: int = 10, max_turns: int = 10) -> str:
    from app.services.rag.memory import EnhancedConversationMemory

    memory = EnhancedConversationMemory(max_messages=max_messages)
    prev_role: Optional[str] = None
    prev_content: Optional[str] = None
    for m in ui_messages:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "")
        if role not in {"user", "assistant"}:
            continue
        content = extract_text_from_ui_message(m)
        if not content:
            continue
        if role == prev_role and content == prev_content:
            continue
        memory.add_message(role=role, content=content)
        prev_role = role
        prev_content = content
    return memory.get_context(max_turns=max_turns)
