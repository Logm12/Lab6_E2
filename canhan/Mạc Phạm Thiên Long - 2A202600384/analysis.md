**Họ và tên:** Mạc Phạm Thiên Long

**Mã học viên:** 2A202600384

**Nhóm:** *C401-E2*

# BÀI TẬP: PHÂN TÍCH SẢN PHẨM AI - CHATBOT NEO (VIETNAM AIRLINES)

## 1. Khám phá: Gap Marketing vs. Thực tế

**Thông điệp Marketing:**
Vietnam Airlines định vị Chatbot NEO là một Trợ lý ảo thông minh, người bạn đồng hành có khả năng hỗ trợ khách hàng mọi lúc mọi nơi. Hình ảnh truyền thông hướng tới một AI có khả năng giao tiếp tự nhiên, thấu hiểu khách hàng và giúp việc tìm chuyến bay, đặt vé hay giải đáp thắc mắc thuận lợi và hiệu quả hơn.

**Thực tế trải nghiệm:**
* **Rule-based vs. NLP:** NEO hoạt động chủ yếu dựa trên rule-based và bắt từ khóa  thay vì thực sự thấu hiểu ngữ cảnh giao tiếp tự nhiên (NLP). 
* **Thiếu linh hoạt trong intent switching:** Khoảng cách lớn nhất lộ ra khi người dùng đi chệch khỏi luồng tuyến tính. Nếu người dùng dùng ngôn ngữ đời thường hoặc hỏi gộp nhiều ý, bot dễ dàng gán sai intent và ép người dùng vào một quy trình cứng nhắc. 
* **Kết luận:** Marketing hứa hẹn một trợ lý thấu hiểu người dùng, nhưng thực tế người dùng đang tương tác với một hệ thống menu tự động dưới hình thức chat.

---

## 2. Phân tích 4 paths và ghi chú UX

### Path 1: Luồng đúng (Happy path):
* **Tình huống:** Người dùng đưa ra câu lệnh đầy đủ dữ kiện: "Tìm chuyến bay Hà Nội đi TP.HCM sáng mai".
* **Trải nghiệm lý tưởng:** Bot xử lý mượt mà, trích xuất chính xác Điểm đi (HAN), Điểm đến (SGN), và Thời gian (Sáng mai). Trả về dạng thẻ lướt ngang (Carousel) chứa 3 chuyến bay phù hợp, kèm giá và nút "Đặt vé ngay".
* **Ghi chú phân tích UX:** * Luồng không ma sát (Frictionless). Việc sử dụng UI Carousel thay vì Text thuần giúp tối ưu hóa không gian hiển thị và tăng tốc độ đọc lướt (scannability).
    * Cấu trúc thông tin đưa người dùng từ giai đoạn tìm kiếm (Search) sang hành động (Action) chỉ trong 1-2 lượt tương tác, đảm bảo tỷ lệ chuyển đổi cao.

### Path 2: Luồng không Chắc (Ambiguous path):
* **Tình huống:** Người dùng gõ "Chuyến bay đi Đà Nẵng ngày 15/10". Bot nhận diện được chuyến bay nhưng thiếu động từ để xác định rõ bối cảnh là "Đặt vé mới" hay "Tra cứu vé cũ".
* **Trải nghiệm xử lý:** Bot dừng lại để làm rõ  thay vì tự động đoán: "Chào bạn, bạn muốn NEO hỗ trợ gì cho chuyến bay ngày 15/10". Kèm theo 2 nút Quick Reply tương ứng.
* **Ghi chú phân tích UX:** * Nguyên tắc "Đừng bắt người dùng phải nghĩ" được áp dụng. 
    * Sử dụng nút bấm thay vì yêu cầu người dùng gõ lại giúp giảm tải nhận thức. Bot chủ động dẫn dắt luồng hội thoại, hạn chế tối đa nguy cơ chuyển sang luồng lỗi.

### Path 3: Luồng sai (Error path):
* **Tình huống:** Người dùng muốn tìm vé mới và gõ "Tìm cho tôi chuyến bay từ HN đi TPHCM ngày mai". Hệ thống bắt từ khóa "chuyến bay" và lập tức kích hoạt luồng tra cứu.
* **Trải nghiệm thực tế:** Bot phản hồi "Vui lòng nhập mã số chuyến bay hoặc mã đặt chỗ (PNR)". Người dùng bị chững lại vì chưa hề mua vé.
* **Ghi chú phân tích UX:** 
    * Điểm mù chí mạng của giao diện này là không có cơ chế sửa sai. Việc không cung cấp lối thoát như nút "Tôi chưa có vé" hay "Quay lại" khiến người dùng bị kẹt cứng trong một luồng do chính hệ thống tạo ra.

### Path 4: Luồng Mất tin (Fail path):
* **Tình huống:** Kế tiếp path 3, do không có nút bấm, người dùng đành gõ text giải thích: "Tôi không có mã, tôi muốn tìm vẽ!". Bot quét dữ liệu, không thấy mã PNR định dạng 6 ký tự.
* **Trải nghiệm thực tế:** Bot báo "Mã không hợp lệ, vui lòng nhập lại". Người dùng rơi vào vòng lặp lỗi và thoát ứng dụng.
* **Ghi chú phân tích UX:** * Hệ thống xử lý thất bại  ở khâu dự phòng (Human fallback). Bot thiếu logic đếm số lần lỗi (Fallback count) và thiếu bộ lọc cảm xúc (Sentiment analysis).