from __future__ import annotations

from app.pipeline import RecommenderPipeline


CASES = [
    ("Em muốn mua xe gia đình", "ask"),
    ("Ngân sách 700 triệu, đi phố là chính", "ask"),
    ("Ngân sách 1.2 tỷ, gia đình 5 người, hay đi xa", "recommend"),
    ("Cần 7 chỗ, đi du lịch, tầm 1.8 tỷ", "recommend"),
    ("Chạy dịch vụ, 5 chỗ, khoảng 600 triệu", "recommend"),
    ("Đi làm nội thành, xe nhỏ gọn", "ask"),
    ("Khoảng 450 triệu, cần 5 chỗ, đi phố", "recommend"),
    ("Tầm 2 tỷ, muốn xe sang chở đối tác, 5 chỗ", "recommend"),
    ("Mình phân vân giữa VF 6 và VF 7, nhà 5 người", "ask"),
    ("Ngân sách 300 triệu, đi làm trong phố, 4 chỗ", "recommend"),
]


def main() -> None:
    pipeline = RecommenderPipeline()
    correct = 0
    for text, expected in CASES:
        res = pipeline.run(messages=[text], state={}, top_k=3)
        got = res.next_step.value
        if got == expected:
            correct += 1
    acc = correct / len(CASES)
    print(f"router_accuracy={acc:.3f} ({correct}/{len(CASES)})")


if __name__ == "__main__":
    main()
