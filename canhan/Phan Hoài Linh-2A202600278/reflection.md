# Individual reflection — Phan Hoài Linh (2A202600278)
---
# Case Study: AI Tư vấn xe VinFast **
## 1. Vai trò (Role)

Product Designer AI/Data Engineer & QA.

## 2. Đóng góp cốt lõi
* **Xây dựng Data Pipeline (Crawler):** Tự phát triển script cào dữ liệu trực tiếp từ `vinfast.vn`. Trích xuất, làm sạch thông số kỹ thuật (specs) của hơn 8 mẫu xe và chuẩn hóa đầu ra lưu trữ vào file `vinfast.csv`.
* **Thiết kế RAG & Vector DB:** Chịu trách nhiệm tạo embedding cho toàn bộ dữ liệu đa nguồn. Tích hợp và nạp toàn bộ vector vào hệ thống cơ sở dữ liệu **ChromaDB/FAISS** để phục vụ tìm kiếm thông tin theo thời gian thực.
* **Đảm bảo chất lượng (QA & Testing):** Trực tiếp thiết kế bộ 10 QA Test Cases bao phủ từ luồng chuẩn đến các ca khó (Edge cases). Đồng thời, rà soát và lập danh sách lỗi ưu tiên để chặn đứng các rủi ro  trước khi deploy.

## 3. Đánh giá & Khắc phục (Troubleshooting)
* **Điểm mạnh:** Quản lý tốt kho dữ liệu. Việc đưa cả Review FB/YT vào Corpus giúp AI tư vấn  hơn, không chỉ đọc specs khô khan mà còn biết tư vấn dựa trên cảm nhận thực tế của cộng đồng.
* **Điểm tối ưu:** Khi load toàn bộ Corpus vào chung một ChromaDB/FAISS, cần thiết lập metadata (tags) chặt chẽ  để lúc Retrieval không bị mâu thuẫn thông tin.

## 4. Bài học 
* **Garbage in, Garbage out:** Chất lượng của hệ thống RAG phụ thuộc 90% vào file `vinfast.csv` và cách làm sạch text từ Facebook/YouTube trước khi embedding. 
* **Test Case không chỉ để tìm lỗi code:** Bộ 10 test case QA và bug list P0/P1 giúp tôi nhận ra các số liệu nhạy cảm (như Giá tiền, Chính sách bảo hành) bắt buộc phải dùng logic truy xuất chính xác tuyệt đối, thà trả lời "không biết" chứ tuyệt đối không để LLM tự "hallucinate".
* Metric là quyết định Sản phẩm: Khi làm AI bán hàng giá trị cao, thà để bot nói "Tôi xin phép kiểm tra lại" còn hơn là "Hallucinate" sai giá xe.
* Xử lý mâu thuẫn dữ liệu: Khi kết hợp Specs từ hãng (chuẩn xác, khô khan) và Review từ FB/YT (thực tế, cảm tính), đôi khi có sự mâu thuẫn. Hệ thống RAG phải được thiết kế để phân định rõ ràng: "Theo công bố của hãng là X, nhưng cộng đồng người dùng đánh giá là Y", thay vì gộp chung làm khách hàng bối rối.

## 5. AI giúp gì / sai gì

Giúp: Sử dụng LLMs hiệu quả để brainstorm các "Failure Modes" và "Edge Cases" bổ sung cho bộ test.

Sai: AI gợi ý mở rộng tính năng vượt quá giới hạn (VD: thêm luồng đặt cọc/thanh toán trực tiếp). Cần kỹ năng kiểm soát để tránh scope creep.
---