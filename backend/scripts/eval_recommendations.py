from __future__ import annotations

from app.pipeline import RecommenderPipeline


CASES = [
    ("Ngân sách 500 triệu, đi phố, 5 chỗ", {"VF 5"}),
    ("Nhà 7 chỗ, hay đi du lịch, khoảng 1.7 tỷ", {"VF 9"}),
    ("Tầm 900 triệu, gia đình 5 người, đi xa", {"VF 7", "VF 8"}),
    ("Khoảng 300 triệu, đi làm nội thành, 4 chỗ", {"VF 3"}),
    ("700-800 triệu, gia đình 5 người", {"VF 6", "VF e34"}),
    ("1.3 tỷ, đi xa nhiều, 5 chỗ", {"VF 8"}),
    ("600 triệu, chạy dịch vụ, 5 chỗ", {"VF 5", "VF e34"}),
    ("1 tỷ, lịch sự chở đối tác, 5 chỗ", {"VF Lux A2.0 (tham khảo)", "VF 7"}),
    ("800 triệu, đi phố 80%, cuối tuần về quê, 5 chỗ", {"VF 6", "VF e34"}),
    ("2 tỷ, gia đình đông người, cần rộng", {"VF 9"}),
]


def main() -> None:
    pipeline = RecommenderPipeline()
    hit = 0
    for text, expected in CASES:
        res = pipeline.run(messages=[text], state={"turns_used": 3}, top_k=3)
        got = {r.model for r in res.recommendations}
        if got.intersection(expected):
            hit += 1
    precision = hit / len(CASES)
    print(f"top3_precision={precision:.3f} ({hit}/{len(CASES)})")


if __name__ == "__main__":
    main()
