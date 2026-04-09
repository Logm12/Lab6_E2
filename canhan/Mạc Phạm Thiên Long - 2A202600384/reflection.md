# Individual reflection — Mạc Phạm Thiên Long (Nhóm VinFast-C401-E2)

## 1. Role
Data crawler (Facebook) và Prompt Engineer. Phụ trách xây dựng hệ thống nhận dạng ngữ nghĩa, kỹ thuật phân luồng cho Guard và Router.

## 2. Đóng góp cụ thể
- Xây dựng luồng thu thập dữ liệu tự động từ các hội nhóm và bài đăng phổ biến trên Facebook qua thư viện Apify, kết hợp kịch bản lọc bình luận giá trị bằng mô hình ngôn ngữ lớn (file `filter_posts.py` và nằm trong folder facebook_crawler).
- Thiết lập system prompt độc lập cho các Router để phân loại ba mức ý định của người dùng: câu hỏi ngoài luồng, truy vấn thiếu bối cảnh cần làm rõ, truy vấn đủ điều kiện tra cứu database.
- Thiết kế toàn bộ tập lệnh kiểm thử định tuyến (`eval_router.py`) chứa mười tình huống ngoại lệ đánh đố, đảm bảo ngưỡng đáp ứng chính xác vượt 90%.

## 3. SPEC mạnh/yếu
- **Điểm mạnh**: Cấu trúc technical thể hiện rõ tính thực tiễn ở các Failure modes. Việc triển khai luồng chốt chặn ngay từ nút Router ban đầu đã khắc phục điểm yếu của các hệ thống chatbot là sa đà vào những câu giao tiếp không liên quan tới nhiệm vụ nó cần làm.
- **Điểm yếu**: Mô hình giả định phân tích ROI khá lạc quan khi dựa dẫm hoàn toàn vào lượng kết nối lưu lượng . Chi phí hạ tầng vận hành chuỗi LangGraph đan chéo cho hàng nghìn lượt truy vấn kéo dài có thể phát sinh phí duy trì lớn.

## 4. Đóng góp khác
- Trực tiếp chuẩn hóa các tập dữ liệu CSV đã xử lý nhiễu về chung một định dạng chuẩn trước khi cung cấp cho nhóm phụ trách bước mã hóa không gian lưu trữ (Embedding vector).
- Chủ động đóng góp rà soát các biên bản kịch bản giao tiếp tương tác giữa các đầu việc của Backend Engineer và End-user.

## 5. Điều học được
- Quyết định đánh giá hiệu suất không định tính qua thông số kỹ thuật khô khan mà bắt buộc xuất phát từ bản chất bài toán. Lựa chọn hy sinh Recall để đánh đổi sự gắt gao trong độ chính xác tuyệt đối (Precision) là quy luật thiết yếu trong ngành xe phân khúc cao cấp, hạn chế rủi ro đưa ra các mẫu xe lệch nhu cầu vốn tạo ra tâm lý e ngại cho người dùng.
- Quá trình phát triển dự án tạo ra cơ sở cho bản thân em được giao lưu, học hỏi các phương pháp phân tích hệ thống từ những dự án của các nhóm khác, đồng thời nâng cao kinh nghiệm phản biện qua quá trình tham gia tranh luận chuyên sâu về AI product và các kiến trúc kỹ thuật.
- Cấu trúc kết xuất tham chiếu đầu ra cần được định dạng dưới khuôn khổ tham số tĩnh (kiểu JSON) thay cho kiểu phản hồi ngôn ngữ mở, để giúp mã nền nhận định và điều hướng luồng xử lý chặt chẽ.

## 6. Nếu làm lại
- Sẽ phân bổ ứng dụng thêm hệ thống kỹ năng điều hướng dựa trên dẫn xuất trước (few-shot prompting) với số lượng ngữ cảnh giả lập dày đặc hơn, phục vụ riêng cho khai báo chỉ thị hệ thống thay vì lệ thuộc vào lời giải thích ban đầu; từ đó tạo nên luồng dự phóng phân tích nhạy bén hơn.

## 7. AI giúp gì / AI sai gì
- **AI giúp gì**: Giải quyết dứt điểm rào cản công sức trong việc phân loại và lược bỏ hàng nghìn bình luận rác vô giá trị từ cộng đồng trực tuyến. Dễ dàng tự động hóa chu trình tạo thân đoạn mã phân rã nhanh cấu trúc chức năng giữa các tệp.
- **AI sai gì**: Các mô hình chưa được trained có khuynh hướng luôn trả lời lan man để xoa dịu tâm lý khách hàng kể cả khi thiếu tham số lọc giá, từ đó sản sinh ra dữ liệu ảo hallucination. Quá trình này đòi hỏi bắt buộc phải kết hợp code function thay vì để mô hình tự quyết định.