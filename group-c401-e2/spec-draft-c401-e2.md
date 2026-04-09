# SPEC draft — c401-e2

## Track: VinFast Car Recommender

## Problem statement

Khách hàng đến showroom hoặc lên web VinFast không biết nên chọn mẫu xe nào.
Hiện tại phải hỏi nhân viên tư vấn hoặc tự lọc thủ công trên trang, mất 10-20
phút, nhân viên phải hỏi lại nhiều lần về ngân sách và nhu cầu. AI có thể hỏi
vài câu cơ bản và gợi ý top 3 mẫu xe phù hợp kèm lý do ngắn gọn.

## Canvas draft

| | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| Trả lời | Khách hàng chưa rõ nhu cầu. Pain: so sánh thủ công mất thời gian, chọn sai phân khúc = mất deal. AI gợi ý top 3 xe từ ngân sách + mục đích sử dụng. | Nếu gợi ý sai xe → khách mất lòng tin, quay lưng với thương hiệu. Phải có option "gặp tư vấn viên" luôn hiện. | API call ~$0.01/lượt, latency <20s. Risk: mô tả nhu cầu mơ hồ, nhiều mẫu overlap phân khúc. |

**Auto hay aug?** Augmentation — AI gợi ý, khách hàng quyết định cuối cùng.

**Learning signal:** khách chọn mẫu xe nào sau gợi ý AI → so sánh với xe thực tế mua → correction signal.

## Hướng đi chính

- Prototype: pipeline 8 node (Router → Elicitation → Profile → Retrieval fan-out → Synthesizer → Response → Feedback) hỏi tối đa 3 lượt → gợi ý top 3 xe + match score + pros/cons
- Dữ liệu: crawl từ vinfast.vn (specs chính thức), Facebook groups (review thực tế), YouTube (video test drive), web search (giá/khuyến mãi realtime)
- Eval: precision trên top-3 suggestions ≥ 70%, router accuracy ≥ 90%
- Main failure mode: mô tả nhu cầu chung chung ("xe gia đình") → gợi ý quá rộng; ngân sách không khớp bất kỳ mẫu nào

## Phân công

- **Đạt**: AI Backend — xây khung LangGraph pipeline (8 node), FastAPI `POST /recommend`, Synthesizer prompt, test tích hợp tổng hợp dữ liệu end-to-end
- **Huấn**: Data crawler YouTube + web search tool — crawl review/transcript ≥ 5 mẫu xe, tích hợp web search (giá/KM/recall realtime), tạo hàm `search_vectordb(query, top_k)`
- **Long**: Data crawler Facebook + Prompt engineer — crawl review/comment từ groups & fanpage VinFast, viết và test prompt Router+Guard node (≥ 90% accuracy trên 10 edge case)
- **Hiếu**: Frontend — UI chat Next.js 15 + Tailwind, result card top 3 (tên, giá, số chỗ, match score, lý do), kết nối API `/recommend`
- **Linh**: Data crawler vinfast.vn + Embedding — crawl specs ≥ 8 mẫu → `cars.json`, tạo embedding toàn bộ corpus (cars + FB + YT) → load ChromaDB/FAISS, viết 10 test case QA + bug list P0/P1
