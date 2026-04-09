from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CarRow:
    model: str
    body_type: str
    seats: int
    range_km: Optional[int]
    price_min_vnd: Optional[int]
    price_max_vnd: Optional[int]
    highlights: list[str]


def _fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _extract_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return "VinFast"
    return re.sub(r"\s+", " ", m.group(1)).strip()


def crawl_stub() -> list[dict[str, object]]:
    return json.loads((Path(__file__).resolve().parents[1] / "data" / "cars.json").read_text(encoding="utf-8"))


def main() -> None:
    out_path = Path(__file__).resolve().parents[1] / "data" / "cars.json"
    urls = sys.argv[1:]
    if not urls:
        cars = crawl_stub()
        out_path.write_text(json.dumps(cars, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(out_path))
        return

    fetched = []
    for url in urls:
        html = _fetch(url)
        fetched.append({"url": url, "title": _extract_title(html)})

    out = {"note": "stub crawler: chưa parse specs tự động", "fetched": fetched}
    (out_path.parent / "crawl_debug.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path.parent / "crawl_debug.json"))


if __name__ == "__main__":
    main()
