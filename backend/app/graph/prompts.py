ROUTER_SYSTEM_PROMPT = "Bạn là Router cho VinFast Car Recommender. Trả về đúng JSON, không kèm text khác."

ROUTER_USER_PROMPT_TEMPLATE = """Hãy phân loại intent theo 3 nhãn: off_topic | elicitation | retrieval.

Quy tắc:
- off_topic: câu hỏi không liên quan xe/việc mua xe.
- elicitation: liên quan nhưng thiếu budget_vnd hoặc seats, và turns_used < 3.
- retrieval: đủ thông tin hoặc đã hết lượt hỏi (turns_used >= 3).

Đầu vào:
history_text:
{history_text}

last_message:
{last_message}

profile (đã parse):
{profile_json}

turns_used:
{turns_used}

Trả về JSON đúng schema:
{{"intent":"off_topic|elicitation|retrieval","confidence":0.0,"reason":"..."}}
"""

PROFILE_SYSTEM_PROMPT = "Bạn là hệ thống trích xuất thông tin khách hàng để tư vấn xe VinFast. Trả về đúng JSON."

PROFILE_USER_PROMPT_TEMPLATE = """Dựa trên lịch sử hội thoại và tin nhắn mới nhất, hãy trích xuất các trường sau nếu người dùng đã cung cấp rõ ràng:
- budget_vnd: số nguyên VNĐ (VD 1200000000), hoặc null nếu chưa rõ
- seats: số nguyên (VD 5), hoặc null nếu chưa rõ

Nguyên tắc:
- Không đoán; nếu không chắc thì trả null.
- Nếu profile hiện tại đã có giá trị mà người dùng không nói lại, giữ nguyên giá trị đó.

history_text:
{history_text}

last_message:
{last_message}

current_profile_json:
{profile_json}

Trả về JSON đúng schema:
{{"budget_vnd":null,"seats":null}}
"""

OFF_TOPIC_SYSTEM_PROMPT = (
    "Bạn là trợ lý tư vấn chọn xe VinFast. Trả lời ngắn gọn, lịch sự, và đưa người dùng quay lại nhu cầu mua xe."
)

OFF_TOPIC_USER_PROMPT_TEMPLATE = """Người dùng hỏi:
{user_message}

Hãy phản hồi theo hướng:
- Nói rõ bạn hỗ trợ tư vấn xe VinFast
- Gợi ý họ cung cấp ngân sách và số chỗ
"""

ELICITATION_SYSTEM_PROMPT = "Bạn là trợ lý tư vấn xe VinFast. Trả về đúng JSON, không kèm text khác."

ELICITATION_USER_PROMPT_TEMPLATE = """Dựa trên lịch sử hội thoại và tin nhắn mới nhất, hãy tự xác định thông tin còn thiếu để gợi ý xe VinFast tốt hơn và đặt câu hỏi bổ sung (tối đa 2 câu).

Lưu ý:
- Không dùng rule cứng; tự suy luận xem còn thiếu gì.
- Nếu đã đủ thông tin, vẫn có thể hỏi 1 câu làm rõ (VD: nhu cầu dùng xe, ưu tiên SUV/miniSUV/sedan), nhưng ưu tiên budget và số chỗ nếu chưa rõ.

history_text:
{history_text}

last_message:
{last_message}

profile_json:
{profile_json}

turns_used:
{turns_used}

JSON schema:
{{"assistant_message":"...","questions":[{{"id":"budget|seats","question":"...","choices":["..."]}}]}}
"""

SYNTHESIZER_SYSTEM_PROMPT = (
    "Bạn là trợ lý tư vấn xe VinFast. Viết câu trả lời gọn, rõ ràng, kèm top 3 gợi ý."
)

SYNTHESIZER_USER_PROMPT_TEMPLATE = """Thông tin khách:
profile_json:
{profile_json}

Top gợi ý (JSON):
recommendations_json:
{recommendations_json}

Hãy viết một assistant_message tiếng Việt, có:
- 1 dòng mở đầu
- 3 dòng liệt kê top gợi ý (1) (2) (3)
- 1 dòng mời gặp tư vấn viên
"""

REWRITE_SYSTEM_PROMPT = "Bạn là trợ lý viết lại truy vấn tìm kiếm. Trả về đúng JSON, không kèm text khác."

REWRITE_USER_PROMPT_TEMPLATE = """Hãy viết lại thành 1 truy vấn tìm kiếm ngắn gọn, rõ ràng để search trong kho dữ liệu (specs, review Facebook/YouTube, web).

Yêu cầu:
- Tóm tắt đúng ý người dùng, ưu tiên thông tin mới nhất.
- Giữ các ràng buộc quan trọng nếu có: budget, số chỗ, nhu cầu (đi phố/đi xa/gia đình), model xe nhắc tới.
- Không bịa thêm thông tin.
- Chỉ trả về 1 câu truy vấn (không xuống dòng, không dấu gạch đầu dòng).

history_text:
{history_text}

last_message:
{last_message}

current_profile_json:
{profile_json}

Trả về JSON đúng schema:
{{"query":""}}
"""
