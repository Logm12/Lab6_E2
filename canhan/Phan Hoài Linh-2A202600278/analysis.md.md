
# Phân tích sản phẩm MoMo - Trợ thủ AI Moni

**Người thực hiện:** Phan Hoài Linh - 2A202600278

## 1. Khám phá
### * Mô tả sản phẩm:
MoMo là siêu app Ví điện tử, nay là "Trợ thủ tài chính với AI". Moni là trợ lý AI cá nhân (chatbot) giúp quản lý chi tiêu, ghi chép tự động, phân tích, nhắc nhở và tư vấn tài chính. Truy cập bằng cách kéo xuống phần Trợ thủ AI - Moni trên app.

**User flow chính:**
* Mở app $\rightarrow$ kéo xuống thấy card Moni.
* Chat ngay: "Hôm nay tôi chi 200k ăn uống" $\rightarrow$ Moni ghi chép, phân loại, hỏi thêm chi tiết.
* Xem báo cáo: Biểu đồ chi tiêu theo tuần.

### * Marketing khớp thực tế:
Khớp khá tốt: Làm rất tốt phần ghi chép và phân tích cơ bản. Bảo mật AI 5 lớp được nhấn mạnh và cảm giác an toàn.

---

## 2. Phân tích 4 paths

### Path 1: Ghi chép chi tiêu nhanh
* **User:** "Tôi vừa chi 32k mua đồ ăn"
* **Moni:** Ghi chép, phân loại, cập nhật báo cáo.
* **Tốt:** Nhanh, tự nhiên, vui vẻ (có emoji, giọng điệu thân thiện).
* **Xấu:** (Trống)

### Path 2: Xem, thấu hiểu các chi tiêu
* **User:** "Tháng này chi bao nhiêu?"
* **Moni:** Đưa ra phân tích, thống kê.
* **Tốt:** Dễ hiểu, cụ thể, chi tiết.
* **Xấu:** Báo cáo nhiều chỗ chưa sâu, thiếu thông tin.

### Path 3: Tư vấn tài chính
* **User:** "Làm sao tiết kiệm 1M/tháng?"
* **Moni:** Đặt mục tiêu, đưa tips chung.
* **Tốt:** Thân thiện, khuyến khích.
* **Xấu:** Tư vấn còn generic (chung chung), chưa cá nhân hóa mạnh.

### Path 4: Xử lý lỗi, thoát giữa chừng
* **Vấn đề:** Chat không hiểu.
    * Moni đôi khi quên context (ngữ cảnh) trong trò chuyện cũ.
    * Không có nút "Thoát" hoặc "Trò chuyện mới".

---

## 3. Sketch To-be

### Phân tích thay đổi:

| As-is (Hiện tại) | To-be (Cải tiến) |
| :--- | :--- |
| User phải gõ dài hoặc chat nhiều lượt. | **Thêm:** Nút ghi âm. |
| Dễ mất context khi chat dài. | **Auto detect:** Gợi ý giao dịch từ MoMo Pay. |
| | **Bản:** Text dài dòng. |
| | **Đổi giao diện:** Thêm nút sửa, xóa ngay trong chat. |