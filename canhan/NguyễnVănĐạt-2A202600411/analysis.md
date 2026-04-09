# UX exercise — MoMo Moni AI

## Sản phẩm: MoMo — Moni AI Assistant (phân loại chi tiêu tự động)

---

## 4 paths

### 1. AI đúng
- User đặt Grab 85k → Moni tự động tag "Di chuyển", user mua Baemin 60k → tag "Ăn uống"
- User thấy tag đúng, không cần làm gì thêm
- UI: hiện tag + icon category ngay dưới giao dịch, không hỏi confirm
- Kết quả: báo cáo cuối tháng chính xác → user tự tin ra quyết định tài chính

### 2. AI không chắc
- User chuyển tiền 200k cho bạn → Moni không tag hoặc tag "Khác"
- UI: không hiện gợi ý nào, user phải tự vào Sổ giao dịch → chỉnh thủ công
- Vấn đề: không có cơ chế hỏi lại "Bạn muốn phân loại giao dịch này không?"
- Thực tế xác nhận: giao dịch chuyển tiền và giao dịch ngoài MoMo không tự động phân loại

### 3. AI sai
- User mua sách trên Shopee → Moni tag "Mua sắm" thay vì "Học tập"; Grab bị tag "Giải trí" thay vì "Di chuyển"
- User chỉ phát hiện khi xem báo cáo cuối tháng — không có alert tại thời điểm giao dịch
- Sửa: Lịch sử GD → Mở quản lý chi tiêu → Sổ giao dịch → chọn giao dịch → bấm tag → đổi category (4 bước)
- Vấn đề: không có nút Sửa inline tại giao dịch; không rõ AI có học từ correction này không

### 4. User mất niềm tin
- Sau nhiều lần tag sai, user không tin báo cáo chi tiêu tự động nữa
- Không có option "tắt auto-tag" hoặc "xem lý do AI phân loại vào danh mục này"
- Không có fallback rõ ràng ngoài việc sửa từng giao dịch một cách thủ công
- Kết quả: user bỏ dùng tính năng Quản lý chi tiêu hoàn toàn

---

## Path yếu nhất: Path 3 + 4

- Khi AI sai, recovery flow mất 4 bước — không có lối tắt inline
- Không có feedback loop rõ — user sửa nhưng không biết AI có học không, không có xác nhận
- Không có exit/fallback cho user đã mất niềm tin (không thể tắt auto-tag, không có manual-first mode)
- Hậu quả lớn nhất: báo cáo sai → user ra quyết định tài chính dựa trên data rác

---

## Gap marketing vs thực tế

- **Marketing:** "AI Moni giúp tự động phân loại chi tiêu với độ chính xác cao — quản lý tài chính thông minh, không cần ghi chép"
- **Thực tế:** auto-tag chỉ hoạt động với giao dịch thanh toán qua MoMo; các edge case (chuyển tiền, giao dịch ngoài app, merchant mơ hồ) thường bị tag sai hoặc không tag
- **Gap lớn nhất:** marketing không đề cập kịch bản khi AI sai → user kỳ vọng 100% chính xác → mất tin mạnh hơn khi gặp lỗi đầu tiên
- **Gap thứ hai:** AI có cơ chế học từ correction của user, nhưng hoàn toàn ẩn — user không biết, không có lý do để tiếp tục sửa

---

## Sketch

*(Ảnh đính kèm: sketch giấy)*

- **As-is:** giao dịch → auto-tag thầm lặng → user thấy kết quả trong báo cáo → nếu sai phải vào sửa thủ công 4 bước → không biết AI có học không
- **To-be:** giao dịch → auto-tag → nếu confidence thấp: hiện "Bạn muốn phân loại giao dịch này không?" → user chọn danh mục → AI ghi nhận correction → hiện bubble **"Moni đã ghi nhớ! Lần sau sẽ chính xác hơn"** → sau 3 lần sửa cùng merchant: hỏi **"Tự động phân loại Grab = Di chuyển từ giờ không?"**

---

## Thêm / Bớt / Đổi

**➕ Thêm**
- Nút ✏ Sửa inline kề tag danh mục ngay tại giao dịch
- Prompt phân loại khi AI không chắc (confidence thấp)
- Bubble xác nhận "Moni đã ghi nhớ" sau mỗi lần correction
- Hiển thị lý do AI phân loại ("Xếp vào Di chuyển vì: Grab")

**➖ Bớt**
- Luồng sửa 4 bước ẩn sâu trong Sổ giao dịch
- Báo cáo không có disclaimer về độ chính xác
- Auto-tag hoàn toàn thầm lặng, không giải thích

**↔ Đổi**
- Lỗi im lặng → Learning moment có thông báo
- AI "đóng hộp" → AI minh bạch, giải thích được
- User bị động chờ báo cáo → User chủ động dạy AI từng giao dịch

---

## Insight chính

> *"Vấn đề không phải AI sai — AI nào cũng sai đôi lúc. Vấn đề là khi sai, user không có đường sửa nhanh, và không biết việc sửa có ích gì không. To-be biến mỗi lần lỗi thành learning moment: user sửa → Moni xác nhận học → cả hai cùng tiến bộ. Đây là loop xây trust, không phải loop mất trust."*
