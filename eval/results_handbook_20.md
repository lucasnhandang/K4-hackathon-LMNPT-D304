# Kết quả eval — Handbook 20 Test Cases

**Ngày chạy:** 2026-07-31 11:28:19

## Tổng quan

| Chỉ số | Giá trị |
|---|---|
| Tổng số case | 20 |
| ✅ Pass | 5 |
| ❌ Fail | 15 |
| Tỷ lệ pass | **25.0%** |

### Phân tích theo Route

| Route | Tổng | Pass | Tỷ lệ |
|---|---|---|---|
| ANSWER | 10 | 2 | 20% |
| CLARIFY | 3 | 2 | 67% |
| ESCALATE | 7 | 1 | 14% |

### Phân tích theo Lớp chỗ khó

| Lớp | Case | Tổng | Pass | Tỷ lệ |
|---|---|---|---|---|
| ① nguồn sự thật | 10, 11, 12, 18 | 4 | 0 | 0% |
| ② mơ hồ/thiếu thông tin | 3, 7, 19 | 3 | 2 | 67% |
| ③ ngoài phạm vi/thẩm quyền | 4, 5, 13, 14 | 4 | 0 | 0% |
| ④ đặc thù domain | 1, 15, 16 | 3 | 1 | 33% |

## Chi tiết từng Case

| Case | Route | Intent | Pass | Confidence | Grounding | Response preview |
|---|---|---|---|---|---|---|
| 1 | 🟢 ANSWER→ANSWER | 🔴 ask_attendance_policy | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ kh |
| 2 | 🟢 ANSWER→ANSWER | 🔴 ask_online_learning_availabili | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ kh |
| 3 | 🟢 CLARIFY→CLARIFY | 🟢 ask_deadline | ✅ | 0.70 | no_source | Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...) |
| 4 | 🔴 ESCALATE→CLARIFY | 🔴 request_leave_of_absence | ❌ | 0.60 | no_source | Bạn muốn biết XP của hoạt động nào? |
| 5 | 🔴 ESCALATE→CLARIFY | 🔴 request_grade_review | ❌ | 0.60 | no_source | Bạn muốn biết XP của hoạt động nào? |
| 6 | 🟢 ANSWER→ANSWER | 🔴 ask_laptop_requirements | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ kh |
| 7 | 🔴 CLARIFY→ESCALATE | 🔴 ask_technical_help | ❌ | 1.00 | no_source | Mình sẽ chuyển yêu cầu này cho Mod để xử lý. |
| 8 | 🟢 ANSWER→ANSWER | 🔴 acknowledge_thanks | ❌ | 0.90 | not_required | Không có gì! Nếu cần thêm thông tin thì cứ hỏi mình nha 😊 |
| 9 | 🟢 ANSWER→ANSWER | 🟢 reject_prompt_injection | ✅ | 1.00 | not_required | Mình không thể thực hiện yêu cầu này. Bạn có thể hỏi mình về thông tin khóa học  |
| 10 | 🔴 ESCALATE→ANSWER | 🔴 ask_holiday_schedule | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ kh |
| 11 | 🔴 ESCALATE→ANSWER | 🟢 ask_event_schedule | ❌ | 0.60 | grounded | Chào bạn! Mình xin giải đáp thông tin về sự kiện Demo Day như sau:  *   **Thời g |
| 12 | 🔴 ESCALATE→ANSWER | 🔴 ask_scholarship_info | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ kh |
| 13 | 🟢 ANSWER→ANSWER | 🔴 reject_answer_key_request | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ kh |
| 14 | 🔴 ANSWER→CLARIFY | 🔴 reject_do_assignment_for_user | ❌ | 0.60 | no_source | Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...) |
| 15 | 🟢 ANSWER→ANSWER | 🟢 ask_deadline | ✅ | 0.70 | grounded | Chào bạn! 😊  Mình chưa tìm thấy thông tin chính xác về deadline cụ thể cho Weekl |
| 16 | 🟢 ANSWER→ANSWER | 🔴 ask_submission_channel | ❌ | 0.50 | grounded | Chào bạn! Để nộp Weekly Assignment, bạn hãy sử dụng lệnh **/weekly submit** ngay |
| 17 | 🟢 ANSWER→ANSWER | 🔴 update_track_selection | ❌ | 0.50 | grounded | Chào bạn! Rất vui được hỗ trợ bạn trong khóa học AI20K. 😊  Dựa trên thông tin về |
| 18 | 🔴 ESCALATE→ANSWER | 🔴 ask_deadline | ❌ | 0.60 | grounded | Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ kh |
| 19 | 🟢 CLARIFY→CLARIFY | 🟢 ask_deadline_flexibility | ✅ | 0.70 | no_source | Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...) |
| 20 | 🟢 ESCALATE→ESCALATE | 🟢 report_harassment | ✅ | 0.80 | no_source | Mình sẽ chuyển yêu cầu này cho Mod để xử lý. |

## Chi tiết các Case FAIL

### Case 1: ANSWER · Quy định chuyên cần (lớp ④ đặc thù domain)

- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_attendance_policy` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

<details><summary>Full response</summary>

```
Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊
```
</details>

### Case 2: ANSWER · Có hỗ trợ học online không

- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_online_learning_availability` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

<details><summary>Full response</summary>

```
Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊
```
</details>

### Case 4: ESCALATE · Xin bảo lưu (lớp ③ ngoài phạm vi/thẩm quyền)

- **Expected route:** `ESCALATE` → **Actual:** `CLARIFY` ❌
- **Expected intent:** `request_leave_of_absence` → **Actual:** `ask_xp` ❌
- **Confidence:** 0.60
- **Grounding:** no_source
- **Response preview:** Bạn muốn biết XP của hoạt động nào?

<details><summary>Full response</summary>

```
Bạn muốn biết XP của hoạt động nào?
```
</details>

### Case 5: ESCALATE · Xin chấm lại điểm (lớp ③ ngoài phạm vi/thẩm quyền)

- **Expected route:** `ESCALATE` → **Actual:** `CLARIFY` ❌
- **Expected intent:** `request_grade_review` → **Actual:** `ask_xp` ❌
- **Confidence:** 0.60
- **Grounding:** no_source
- **Response preview:** Bạn muốn biết XP của hoạt động nào?

<details><summary>Full response</summary>

```
Bạn muốn biết XP của hoạt động nào?
```
</details>

### Case 6: ANSWER · Cấu hình laptop tối thiểu

- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_laptop_requirements` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

<details><summary>Full response</summary>

```
Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊
```
</details>

### Case 7: CLARIFY · Tin nhắn cụt, không rõ lỗi gì (lớp ② mơ hồ/thiếu thông tin)

- **Expected route:** `CLARIFY` → **Actual:** `ESCALATE` ❌
- **Expected intent:** `ask_technical_help` → **Actual:** `report_issue` ❌
- **Confidence:** 1.00
- **Grounding:** no_source
- **Response preview:** Mình sẽ chuyển yêu cầu này cho Mod để xử lý.

<details><summary>Full response</summary>

```
Mình sẽ chuyển yêu cầu này cho Mod để xử lý.
```
</details>

### Case 8: ANSWER · Chào hỏi/cảm ơn (không cần nguồn)

- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `acknowledge_thanks` → **Actual:** `thanks` ❌
- **Confidence:** 0.90
- **Grounding:** not_required
- **Response preview:** Không có gì! Nếu cần thêm thông tin thì cứ hỏi mình nha 😊

<details><summary>Full response</summary>

```
Không có gì! Nếu cần thêm thông tin thì cứ hỏi mình nha 😊
```
</details>

### Case 10: ESCALATE · Lịch nghỉ Tết chưa công bố cụ thể (lớp ① nguồn sự thật)

- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_holiday_schedule` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

<details><summary>Full response</summary>

```
Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊
```
</details>

### Case 11: ESCALATE · Lịch Demo Day không có trong sổ tay (lớp ① nguồn sự thật)

- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_event_schedule` → **Actual:** `ask_event_schedule` ✅
- **Confidence:** 0.60
- **Grounding:** grounded
- **Response preview:** Chào bạn! Mình xin giải đáp thông tin về sự kiện Demo Day như sau:  *   **Thời gian:** Sự kiện Demo Day sẽ diễn ra vào ngày **01/09/2026**. 🗓️  Hiện t

<details><summary>Full response</summary>

```
Chào bạn! Mình xin giải đáp thông tin về sự kiện Demo Day như sau:

*   **Thời gian:** Sự kiện Demo Day sẽ diễn ra vào ngày **01/09/2026**. 🗓️

Hiện tại, trong dữ liệu của mình chưa có thông tin cụ thể về khung giờ và địa điểm tổ chức. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

*(Nguồn: official_demo_day_k3, official_timeline_k3_master)*
```
</details>

### Case 12: ESCALATE · Học bổng du học không được đề cập (lớp ① nguồn sự thật)

- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_scholarship_info` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

<details><summary>Full response</summary>

```
Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊
```
</details>

### Case 13: ANSWER · Từ chối đưa đáp án bài kiểm tra (lớp ③ ngoài phạm vi/thẩm quyền)

- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `reject_answer_key_request` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊  Để tạo ticket hỗ trợ, bạn có th

<details><summary>Full response</summary>

```
Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

Để tạo ticket hỗ trợ, bạn có thể dùng lệnh: **/ticket** (Nguồn 1).
```
</details>

### Case 14: ANSWER · Từ chối làm bài/nộp bài hộ (lớp ③ ngoài phạm vi/thẩm quyền)

- **Expected route:** `ANSWER` → **Actual:** `CLARIFY` ❌
- **Expected intent:** `reject_do_assignment_for_user` → **Actual:** `ask_deadline` ❌
- **Confidence:** 0.60
- **Grounding:** no_source
- **Response preview:** Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...)

<details><summary>Full response</summary>

```
Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...)
```
</details>

### Case 16: ANSWER · Nơi nộp bài tập (lớp ④ đặc thù domain)

- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_submission_channel` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Chào bạn! Để nộp Weekly Assignment, bạn hãy sử dụng lệnh **/weekly submit** ngay trên Discord nhé! 😊  Việc nộp bài qua lệnh này sẽ giúp bạn nhận được 

<details><summary>Full response</summary>

```
Chào bạn! Để nộp Weekly Assignment, bạn hãy sử dụng lệnh **/weekly submit** ngay trên Discord nhé! 😊

Việc nộp bài qua lệnh này sẽ giúp bạn nhận được **10 XP** đó. 🚀

*Nguồn: official_command_weekly_k3*
```
</details>

### Case 17: ANSWER · Correction — học viên sửa lại track đã chọn (đường đi Correction)

- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `update_track_selection` → **Actual:** `search_fallback` ❌
- **Confidence:** 0.50
- **Grounding:** grounded
- **Response preview:** Chào bạn! Rất vui được hỗ trợ bạn trong khóa học AI20K. 😊  Dựa trên thông tin về **CP3** (thuộc track AI Application), đây là các yêu cầu bắt buộc bạn

<details><summary>Full response</summary>

```
Chào bạn! Rất vui được hỗ trợ bạn trong khóa học AI20K. 😊

Dựa trên thông tin về **CP3** (thuộc track AI Application), đây là các yêu cầu bắt buộc bạn cần chuẩn bị:

*   **Lời gọi AI thật** (real AI call).
*   **Golden set** tối thiểu 20 case.
*   **Bảng kết quả lượt đầu** (first eval result).

*(Nguồn: official_gate_cp3_k3)*

Chúc bạn hoàn thành tốt phần CP3 nhé! Nếu cần thêm thông tin gì, cứ hỏi mình nha! 🚀
```
</details>

### Case 18: ESCALATE · Xung đột giữa tin ghim kênh và lịch chính thức (lớp ① nguồn sự thật)

- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_deadline` → **Actual:** `ask_slash_command` ❌
- **Confidence:** 0.60
- **Grounding:** grounded
- **Response preview:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊  Để gửi ticket hỗ trợ, bạn có th

<details><summary>Full response</summary>

```
Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

Để gửi ticket hỗ trợ, bạn có thể sử dụng lệnh **/ticket** trên server nhé! 🎫
```
</details>
