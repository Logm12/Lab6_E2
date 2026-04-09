# Analysis - MoMo AI Moni

## I. Overview

**Sản phẩm**: MoMo – Trợ thủ AI Moni  
**Chức năng chính**:
- Phân loại chi tiêu tự động
- Chatbot tài chính cá nhân
- Tích hợp trong app MoMo

---

## II. Phân tích 4 Paths

### 1. Path 1: Query → Insight (FAIL ❌)

**User query**: “Tháng này tôi tiêu nhiều nhất vào cái gì?”

**Thực tế**:
- AI không trả lời danh mục chi tiêu nhiều nhất
- Chỉ trả lời tổng chi tiêu và số ngày
- Yêu cầu user vào mục khác để tự tìm

**Vấn đề**:
- Không hiểu đúng intent của user
- Không extract insight từ dữ liệu sẵn có
- Tăng friction (user phải tự thao tác thêm)

**Kết luận**:
> Chatbot chưa thực sự đóng vai trò “trợ lý”, mà chỉ là công cụ điều hướng.

---

### 2. Path 2: Query → Comparison (PASS ⚠️)

**User query**: “So sánh chi tiêu tháng này với tháng trước”

**Thực tế**:
- AI trả lời đầy đủ
- Có breakdown rõ ràng
- Có gợi ý đi kèm

**Điểm tốt**:
- Structured response
- Dễ hiểu

**Hạn chế**:
- Chỉ hoạt động khi user hỏi (reactive)
- Chưa cá nhân hóa sâu

**Kết luận**:
> Đây là flow tốt nhất hiện tại, nhưng vẫn chưa tạo ra trải nghiệm “AI chủ động”.

---

### 3. Path 3: Query → Reasoning (WEAK ⚠️)

**User query**: “Tại sao tôi tiêu nhiều hơn tháng trước?”

**Thực tế**:
- AI đưa ra lý do (ví dụ: mới trải qua 8 ngày)

**Vấn đề**:
- Reasoning còn nông
- Không breakdown theo danh mục
- Không hỗ trợ decision making

**Kết luận**:
> Có reasoning nhưng chưa “useful reasoning”.

---

### 4. Path 4: Query → Advice (FAIL ❌)

**User query**: “Tôi nên tiết kiệm như thế nào?”

**Thực tế**:
- AI đưa ra các tips chung chung:
  - Theo dõi chi tiêu
  - Đặt ngân sách
  - Săn ưu đãi

**Vấn đề**:
- Không dựa trên dữ liệu cá nhân
- Nội dung generic (giống blog/Google)
- Không actionable

**Kết luận**:
> AI không tận dụng được lợi thế dữ liệu người dùng.

---

## III. Gap: Marketing vs Thực tế

### 1. Marketing hứa hẹn

- “Trợ lý tài chính thông minh”
- “Hiểu chi tiêu của bạn”
- “Đưa ra gợi ý cá nhân hóa”

---

### 2. Thực tế trải nghiệm

| Khía cạnh | Marketing | Thực tế |
|----------|----------|--------|
| Hiểu người dùng | AI hiểu chi tiêu cá nhân | Không trả lời đúng intent |
| Phân tích | Insight thông minh | Thiếu insight quan trọng |
| Reasoning | Giải thích rõ ràng | Giải thích hời hợt |
| Cá nhân hóa | Gợi ý riêng cho từng user | Tips chung chung |
| Chủ động | AI như trợ lý | Hoàn toàn bị động |

---

### 3. Gap chính

#### ❌ 1. Intent Understanding Gap
- Marketing: AI hiểu user
- Reality: Không trả lời đúng câu hỏi đơn giản

#### ❌ 2. Data Utilization Gap
- Marketing: dùng dữ liệu để phân tích
- Reality: không khai thác sâu dữ liệu

#### ❌ 3. Personalization Gap
- Marketing: cá nhân hóa
- Reality: nội dung generic

#### ❌ 4. Intelligence Gap
- Marketing: “AI thông minh”
- Reality: giống rule-based chatbot

#### ❌ 5. Proactive Gap
- Marketing: trợ lý
- Reality: chỉ phản hồi khi hỏi

---

## IV. Key Insights

1. Người dùng không cần chatbot → họ cần insight rõ ràng
2. AI hiện tại trả lời câu hỏi, nhưng không giúp ra quyết định
3. Giá trị lớn nhất (data cá nhân) chưa được khai thác
4. Sự khác biệt giữa “AI thật” và “chatbot template” rất rõ

---

## V. Opportunity

- Xây AI agent thay vì chatbot
- Tập trung vào:
  - Insight chính xác
  - Reasoning sâu
  - Gợi ý hành động cụ thể
  - Chủ động (proactive)

---

## VI. Kết luận

> MoMo Moni hiện tại là một chatbot tài chính cơ bản,  
> chưa đạt được kỳ vọng của một “AI assistant” thực thụ.

Cơ hội cạnh tranh nằm ở việc:
- Hiểu đúng intent
- Tận dụng data cá nhân
- Và chuyển từ “trả lời” → “giúp ra quyết định”