from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.models import CarRecommendation
from app.models import UserProfile
from app.utils import debug_print, data_dir, safe_int


@dataclass(frozen=True)
class CarSpec:
    model: str
    body_type: str
    seats: int
    range_km: Optional[int]
    price_min_vnd: Optional[int]
    price_max_vnd: Optional[int]
    highlights: list[str]


def load_catalog(path: Optional[Path] = None) -> list[CarSpec]:
    base = path or (data_dir() / "cars.json")
    if not base.exists():
        return [
            CarSpec(
                model="VinFast VF3",
                body_type="mini-suv",
                seats=4,
                range_km=210,
                price_min_vnd=240_000_000,
                price_max_vnd=350_000_000,
                highlights=["Gọn gàng dễ đỗ", "Chi phí vận hành thấp"],
            ),
            CarSpec(
                model="VinFast VF5",
                body_type="suv",
                seats=5,
                range_km=300,
                price_min_vnd=450_000_000,
                price_max_vnd=600_000_000,
                highlights=["Gầm cao đi phố", "Không gian 5 chỗ thực dụng"],
            ),
            CarSpec(
                model="VinFast VF e34",
                body_type="suv",
                seats=5,
                range_km=285,
                price_min_vnd=650_000_000,
                price_max_vnd=780_000_000,
                highlights=["Nhiều lựa chọn xe lướt", "Không gian gia đình"],
            ),
            CarSpec(
                model="VinFast VF6",
                body_type="suv",
                seats=5,
                range_km=399,
                price_min_vnd=675_000_000,
                price_max_vnd=900_000_000,
                highlights=["Công nghệ hỗ trợ lái", "Đi xa ổn định"],
            ),
            CarSpec(
                model="VinFast VF7",
                body_type="suv",
                seats=5,
                range_km=431,
                price_min_vnd=800_000_000,
                price_max_vnd=1_050_000_000,
                highlights=["Vận hành mạnh", "Không gian rộng rãi"],
            ),
            CarSpec(
                model="VinFast VF8",
                body_type="suv",
                seats=5,
                range_km=457,
                price_min_vnd=1_050_000_000,
                price_max_vnd=1_400_000_000,
                highlights=["SUV cỡ D", "Tiện nghi và an toàn"],
            ),
            CarSpec(
                model="VinFast VF9",
                body_type="suv",
                seats=7,
                range_km=438,
                price_min_vnd=1_450_000_000,
                price_max_vnd=1_900_000_000,
                highlights=["7 chỗ rộng", "Phù hợp gia đình lớn"],
            ),
        ]
    raw = json.loads(base.read_text(encoding="utf-8"))
    out: list[CarSpec] = []
    for item in raw:
        out.append(
            CarSpec(
                model=str(item["model"]),
                body_type=str(item.get("body_type", "")),
                seats=int(item.get("seats", 5)),
                range_km=safe_int(item.get("range_km")),
                price_min_vnd=safe_int(item.get("price_min_vnd")),
                price_max_vnd=safe_int(item.get("price_max_vnd")),
                highlights=list(item.get("highlights", [])),
            )
        )
    return out


def budget_score(budget: Optional[int], car: CarSpec) -> float:
    if budget is None or car.price_min_vnd is None or car.price_max_vnd is None:
        return 0.5
    if car.price_min_vnd <= budget <= car.price_max_vnd:
        return 1.0
    if budget < car.price_min_vnd:
        gap = (car.price_min_vnd - budget) / max(car.price_min_vnd, 1)
        return max(0.0, 1.0 - min(gap, 1.0))
    gap = (budget - car.price_max_vnd) / max(budget, 1)
    return max(0.0, 1.0 - min(gap, 1.0))


def seats_score(seats: Optional[int], car: CarSpec) -> float:
    if seats is None:
        return 0.6
    if car.seats >= seats:
        return 1.0
    diff = seats - car.seats
    return max(0.0, 1.0 - 0.35 * diff)


def evidence_score(model: str, retrieved: dict[str, list[tuple[Any, float]]]) -> float:
    m = model.lower()
    score = 0.0
    for source, items in retrieved.items():
        boost = 0.06 if source in {"youtube", "facebook"} else 0.04
        for doc, sim in items:
            text = str(getattr(doc, "text", "")).lower()
            if m in text:
                score += boost * max(0.0, min(float(sim), 1.0))
                break
    return min(score, 0.15)


def to_recommendation(car: CarSpec, score: float, profile: UserProfile) -> CarRecommendation:
    pros: list[str] = []
    cons: list[str] = []
    if car.range_km is not None:
        pros.append(f"Tầm hoạt động tham khảo ~{car.range_km} km")
    pros.append(f"{car.seats} chỗ, phù hợp nhu cầu cơ bản")
    if car.highlights:
        pros.extend(car.highlights[:2])

    if profile.budget_vnd is not None and car.price_min_vnd is not None and profile.budget_vnd < car.price_min_vnd:
        cons.append("Ngân sách hiện tại có thể chưa chạm cấu hình/phiên bản phù hợp")
    if profile.seats is not None and car.seats < profile.seats:
        cons.append("Số chỗ có thể không đủ nếu đi đủ người")
    if not cons:
        cons.append("Nên lái thử để kiểm tra cảm giác lái và không gian thực tế")

    reason_bits: list[str] = []
    if profile.seats is not None:
        reason_bits.append(f"cần {profile.seats} chỗ")
    if profile.budget_vnd is not None:
        reason_bits.append("bám ngân sách")
    short_reason = "Phù hợp " + ", ".join(reason_bits) if reason_bits else "Phù hợp nhu cầu tổng quát"

    price_mid = None
    if car.price_min_vnd is not None and car.price_max_vnd is not None:
        price_mid = int((car.price_min_vnd + car.price_max_vnd) / 2)
    return CarRecommendation(
        model=car.model,
        match_score=round(float(score), 3),
        short_reason=short_reason,
        pros=pros[:4],
        cons=cons[:3],
        price_vnd=price_mid,
        seats=car.seats,
    )


class RecommenderEngine:
    def __init__(self, catalog: Optional[list[CarSpec]] = None) -> None:
        self.catalog = catalog or load_catalog()
        debug_print("DEBUG_PIPELINE", "engine.catalog", {"size": len(self.catalog)})

    def rank(self, profile: UserProfile, retrieved: dict[str, list[tuple[Any, float]]]) -> list[tuple[CarSpec, float]]:
        out: list[tuple[CarSpec, float]] = []
        for car in self.catalog:
            s_budget = budget_score(profile.budget_vnd, car)
            s_seats = seats_score(profile.seats, car)
            s_evidence = evidence_score(car.model, retrieved)
            score = 0.6 * s_budget + 0.3 * s_seats + s_evidence
            out.append((car, score))
        out.sort(key=lambda x: x[1], reverse=True)
        return out

    def render_recommendations_message(self, recs: list[CarRecommendation]) -> str:
        lines: list[str] = ["Top gợi ý phù hợp nhất:"]
        for i, r in enumerate(recs, start=1):
            lines.append(f"{i}) {r.model} — match {int(r.match_score * 100)}%: {r.short_reason}")
        lines.append("Nếu bạn muốn, mình có thể nối bạn với tư vấn viên để chốt phiên bản/giá lăn bánh.")
        return "\n".join(lines)
