# AI SPEC — Trợ lý quyết định trả lời, hỏi lại hay chuyển Mod · Nhóm LMNPT · Zone D304

Hướng: [ ] A — VLearn  [x] B — Trợ lý Học viên  [ ] C — Làn mở  
Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job

### 1.1 Job executor và workflow hiện tại

- **Job executor:** Học viên đang học hoặc làm bài của khóa, bị kẹt và đặt câu hỏi trong Discord để tiếp tục học.
- **Workflow hiện tại:**
  1. Học viên gặp vướng mắc về bài học, bài tập, deadline, link hoặc quy định.
  2. Học viên hỏi Trợ lý Kute++ trên Discord, đôi khi bằng câu ngắn, tiếng lóng hoặc thiếu tên bài/module.
  3. Trợ lý trả lời, chuyển Mod hoặc không giải quyết được.
  4. Nếu câu trả lời chưa dùng được, học viên phải hỏi lại, chờ Mod hoặc tự mở nhiều nguồn để kiểm tra.
- **Đầu vào CP1:** [`Canvas.txt`](Canvas.txt).
- **JTBD worksheet/sơ đồ:** `[CẦN ĐÍNH KÈM]`.

### 1.2 Core JTBD

> Khi bị kẹt trong lúc học hoặc làm bài, học viên muốn nhận được thông tin hoặc bước xử lý đáng tin cậy để có thể tiếp tục học mà không phải chờ đợi hoặc tự dò nhiều nguồn.

### 1.3 Problem statement

> Khi học viên đặt câu hỏi thiếu ngữ cảnh hoặc câu hỏi không có căn cứ rõ ràng trong tài liệu chính thức, kênh hỗ trợ có thể đưa ra thông tin không liên quan hoặc chuyển người quá sớm, khiến học viên mất thời gian chờ, phải tự kiểm tra lại và giảm niềm tin vào câu trả lời.

### 1.4 Evidence

#### A. Khảo sát trực tiếp — bằng chứng chính cho nhu cầu hỏi làm rõ

- **Con số mạnh nhất:** **13/20 người khảo sát (65%)** muốn Trợ lý Kute++ hỏi lại để làm rõ khi câu hỏi chưa đủ thông tin.
- **Câu hỏi đã dùng:** “Nếu Trợ lý Kute++ có thể làm tốt hơn đúng một việc, bạn muốn đó là gì?”
- **Cách đếm:** Lọc 20 câu trả lời cho câu hỏi trên; đếm số người chọn phương án “hỏi lại để làm rõ khi câu hỏi chưa đủ thông tin”; tỷ lệ = `13 / 20 = 65%`.
- **Độ phổ biến của pain:** **19/20 người (95%)** cho biết từng gặp ít nhất một vấn đề khi sử dụng chatbot; chỉ 1/20 người trả lời “Hài lòng”.
- **Các vấn đề cụ thể được ghi nhận:**
  - **10/20 người (50%)** từng gặp tình trạng chatbot chuyển sang hỏi Mod ngay.
  - **8/20 người (40%)** từng nhận câu trả lời không đúng câu hỏi.
  - **7/20 người (35%)** không biết mình cần bổ sung thông tin gì.
- **Cách đếm nhóm vấn đề:** Với từng phương án vấn đề trong khảo sát, đếm số người đánh dấu đã từng gặp; một người có thể chọn nhiều vấn đề nên các tỷ lệ không cộng thành 100%.
- **Câu hỏi ghi nhận nhóm vấn đề:** `[CẦN CHÉP NGUYÊN VĂN CÂU HỎI TỪ FORM KHẢO SÁT]`.
- **Kết luận:** Pain không chỉ là thiếu kiến thức. Ưu tiên lớn nhất là giúp chatbot nhận diện dữ kiện còn thiếu và hỏi bổ sung trước khi trả lời hoặc chuyển TA/Mod.
- **Chuẩn bằng chứng:** Đã đạt ngưỡng số lượng của chuẩn A với 20 người ngoài nhóm và 65% xác nhận nhu cầu ưu tiên; log vẫn phải giữ đủ câu hỏi và từng câu trả lời nguyên văn để phúc khảo.
- **Log khảo sát:** `[CẦN TẠO/TRỎ TỚI FILE]`.

#### B. Mining data pack — bằng chứng bổ trợ về bối cảnh

- **Phạm vi transcript:** Rà 700 đoạn transcript; lọc 31 đoạn có từ khóa về lịch, link, tài liệu, nộp bài, Discord/LMS; kiểm tra tay và giữ 9 đoạn thể hiện rõ vướng mắc logistics, truy cập hoặc nguồn phân tán.
- **Phạm vi chatlog VLearn:** 1.261 cặp hỏi–đáp của 369 học viên trong 585 hội thoại.
- **Kết quả bổ trợ:** 582/1.261 câu trả lời tutor (46,2%) không có citation; `follow_ups` không được dùng trong 1.261/1.261 lượt; chỉ 3/1.261 lượt có `asked_check_question=True`.
- **Giới hạn diễn giải:** Đây là dữ liệu VLearn/transcript, không phải mining phản hồi của Trợ lý Kute++ trên Discord. Chỉ dùng để chứng minh pattern và bối cảnh; không dùng để khẳng định tỷ lệ lỗi của Discord bot.

#### C. Ví dụ có mã nguồn

| Mã | Ví dụ/vấn đề quan sát được | Nguồn |
|---|---|---|
| T05-049 | Học viên phản ánh tài nguyên bị chia giữa nơi đọc, làm, tải file và nộp bài nên không biết thực hiện ở đâu. | `data/vlearn-pack/transcript/transcript-05-clean.md` |
| T05-098 | Học viên hỏi về cấu trúc file, link slide, cách nộp bài; README và slide không thống nhất. | `data/vlearn-pack/transcript/transcript-05-clean.md` |
| T04-092 | Học viên phản ánh tính năng khó dùng, không tải được slide và mất vị trí khi mở link. | `data/vlearn-pack/transcript/transcript-04-clean.md` |
| T03-082 | Slide trên LMS chưa mở khóa; giảng viên phải kiểm tra và sửa. | `data/vlearn-pack/transcript/transcript-03-clean.md` |
| T06-069 | Học viên hỏi syllabus ở đâu và cách đăng nhập bằng email được cấp. | `data/vlearn-pack/transcript/transcript-06-clean.md` |
| T06-070 | Lớp cần hướng dẫn kết nối Discord và xử lý trường hợp email không khớp. | `data/vlearn-pack/transcript/transcript-06-clean.md` |
| T06-162 | Câu hỏi lịch trình phải chuyển operations; lịch và hướng dẫn nằm trên nhiều điểm truy cập. | `data/vlearn-pack/transcript/transcript-06-clean.md` |

#### D. Evidence Discord cần bổ sung

- `[CẦN ĐO]` Chọn phạm vi ngày và channel được phép.
- `[CẦN ĐO]` Đếm một đơn vị = một câu hỏi học viên + phản hồi đầu tiên của bot.
- `[CẦN ĐO]` Gắn nhãn: đủ/thiếu ngữ cảnh; có/không/xung đột nguồn; route thực tế; kết quả dùng được hay không.
- `[CẦN ĐO]` Lưu ≥5 ví dụ ngắn đã ẩn danh, có mã/link nội bộ để kiểm lại.

## §2. Impact & quyết định chọn

> Không điền số ước lượng. Mọi ô định lượng phải trỏ về survey hoặc mining log.

| Ứng viên | Bao nhiêu người gặp / xác nhận | Tần suất đo được | Tốn gì mỗi lần | Khả thi trong hackathon | Quyết định |
|---|---:|---:|---|---|---|
| Hỏi đúng một câu làm rõ khi thiếu thông tin | 13/20 (65%) muốn cải thiện việc này; 7/20 (35%) không biết cần bổ sung gì | Survey xác nhận đã từng gặp; chưa đo số lần/người | Phải hỏi lại, tự tìm nguồn hoặc chờ hỗ trợ; chưa đo số phút | Cao | **Chọn làm quyết định trung tâm** |
| Giảm chuyển Mod quá sớm | 10/20 (50%) từng gặp chatbot chuyển sang hỏi Mod ngay | Survey xác nhận đã từng gặp; chưa đo số lần/người | Học viên phải chờ; Mod nhận thêm câu có thể xử lý bằng một bước làm rõ; chưa đo số phút | Cao | Không làm feature riêng; xử lý như kết quả của route `CLARIFY` trước `ESCALATE` |
| Giảm câu trả lời không đúng câu hỏi, chỉ ANSWER khi đủ căn cứ | 8/20 (40%) từng nhận câu trả lời không đúng; data bổ trợ có 582/1.261 lượt VLearn tutor không citation | Survey xác nhận đã từng gặp; chưa đo số lần/người | Học viên phải kiểm tra lại, có rủi ro hiểu sai/mất điểm; chưa đo số phút | Cao | Không chọn làm lát cắt riêng; giữ làm điều kiện cứng của route `ANSWER` |

### 2.1 Ứng viên đã loại hoặc không chọn làm lát cắt riêng

- **Giảm chuyển Mod quá sớm:** 10/20 người từng gặp, nhưng đây là hậu quả trực tiếp của việc chưa hỏi làm rõ. Nhóm xử lý trong cùng flow `CLARIFY → ANSWER/ESCALATE`, không tách thành feature.
- **Giảm câu trả lời không đúng câu hỏi:** 8/20 người từng gặp. Nhóm giữ đây là điều kiện cứng cho `ANSWER` thông qua slot check và nguồn chính thức, nhưng không chọn làm lát cắt độc lập.
- **Bản tin cuối ngày cho TA:** Không có số survey trực tiếp trong bộ câu hỏi hiện tại và không giải quyết pain được 13/20 người ưu tiên; loại khỏi prototype hiện tại.
- **Phát hiện học viên stuck và chủ động nhắn:** Chưa có dữ liệu hành vi đủ để xác định ngưỡng “stuck” và mức chủ động không gây phiền; loại khỏi prototype hiện tại.

### 2.2 Ứng viên được chọn

- **Chọn:** Quyết định `ANSWER / CLARIFY / ESCALATE` dựa trên độ rõ của câu hỏi và căn cứ chính thức.
- **Lý do chọn bằng số:** 13/20 người (65%) muốn bot hỏi làm rõ; 10/20 người từng bị chuyển Mod ngay; 7/20 người không biết cần bổ sung thông tin gì. Một quyết định `CLARIFY` tốt tác động trực tiếp cả ba tín hiệu.
- **Evidence bổ trợ:** 19/20 người (95%) từng gặp ít nhất một vấn đề khi sử dụng chatbot.
- **Lý do còn cần đo sâu hơn:** Số lần gặp/người và số phút phát sinh mỗi lần trong mẫu Discord.

## §3. Giải pháp tương tự đã nghiên cứu

| Sản phẩm | Flow quan sát được | Đáng học | Đáng né | Nhóm khác gì |
|---|---|---|---|---|
| `[CẦN NGHIÊN CỨU: NotebookLM/ChatGPT]` | `[CẦN ĐIỀN]` | Citation cạnh câu trả lời; nói rõ giới hạn nguồn | `[CẦN ĐIỀN]` | Route rõ giữa trả lời, hỏi lại và chuyển người |
| `[CẦN NGHIÊN CỨU: Discord support bot]` | `[CẦN ĐIỀN]` | Handoff có consent và summary | `[CẦN ĐIỀN]` | Không dùng câu trả lời community làm nguồn chính thức |

## §4. Thiết kế

### 4.1 Lát cắt một câu

> Khi một học viên hỏi trên Discord để gỡ vướng trong khóa, trợ lý quyết định câu hỏi đã đủ rõ và có đủ căn cứ để trả lời, cần hỏi lại hay phải chuyển Mod, giúp học viên nhận được một bước xử lý đáng tin cậy thay vì câu trả lời phỏng đoán.

### 4.2 Non-goals

1. Không làm bài, đưa đáp án kiểm tra hoặc nộp bài thay học viên.
2. Không tự phê duyệt gia hạn, bảo lưu, sửa điểm hoặc ngoại lệ chính sách.
3. Không coi câu trả lời community là nguồn chính thức cho deadline, link và quy định.
4. Không xây bản tin cuối ngày cho TA trong lát cắt hiện tại.
5. Không triển khai vector search/reranker trước khi đo BM25 baseline.

### 4.3 Mức prototype và ranh giới thật/mock

- Mức: [ ] Sketch  [x] Mock  [ ] Working.
- **Phần chạy thật:** NiceGUI Discord-like flow; intent/slot routing; structured lookup; BM25; citation; conflict check; clarification state; consent gate; trace ID.
- **Phần mock:** Dữ liệu nguồn trong `official_sources.json`; gateway gửi Discord/ticket; một số frontend fallback được hardcode.
- **AI call thật ở quyết định trung tâm:** `[CẦN BỔ SUNG VÀ LƯU TRACE — code hiện tại chủ yếu rule-based/local mock]`.

### 4.4 Mức automation

- [ ] Augment  [x] Conditional  [ ] Automate.
- Trợ lý tự trả lời khi câu hỏi đủ rõ và có nguồn chính thức phù hợp; hỏi đúng một câu khi thiếu thông tin; chuyển Mod khi không có căn cứ, có xung đột hoặc cần thẩm quyền con người.
- **Cost-of-error:** Trả lời sai deadline/link/quy định có thể làm học viên mất điểm hoặc mất niềm tin. Ngược lại, chuyển Mod mọi trường hợp làm tăng thời gian chờ và tải cho Mod. Vì vậy chỉ tự động hóa các case có độ chắc chắn và căn cứ đủ cao.

### 4.5 Nguyên tắc HAX/PAIR đã áp dụng

| Nguyên tắc | Áp cụ thể vào prototype |
|---|---|
| G1 — Làm rõ hệ thống làm được gì | Tin nhắn chào nêu phạm vi deadline, bài tập và quy chế khóa học. |
| G2 — Làm rõ hệ thống làm tốt đến đâu | UI hiển thị confidence, nguồn và tracepath; ngoài nguồn thì không khẳng định fact. |
| G10 — Thu hẹp phạm vi khi nghi ngờ | Thiếu assignment/module quan trọng thì route `CLARIFY` và chỉ hỏi một trường. |
| G9 — Sửa dễ dàng | User trả lời câu hỏi làm rõ hoặc sửa context; hệ thống chạy lại với thông tin mới. |
| G11 — Giải thích vì sao | Câu trả lời có citation, locator và nút xem nguồn. |
| Feedback & Control | Chỉ tạo/gửi ticket sau khi user xác nhận consent; không tự gửi. |
| Graceful Failure | `not_found` và `conflict` có đường lui riêng; không biến thành câu trả lời phỏng đoán. |

## §5. Kiểu lỗi — 4 lớp chỗ khó và kịch bản

| # | Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc |
|---:|---|:---:|---|---|
| 1 | Nguồn chính thức không có lịch nghỉ được hỏi | ① | Không tạo ngày; nói chưa có căn cứ và chuyển đúng vai xác nhận | G2, G11 |
| 2 | Hai nguồn chính thức ghi hai deadline khác nhau | ① | Hiển thị xung đột; không tự chọn nguồn; chuyển Mod kèm summary tối thiểu | G2, Graceful Failure |
| 3 | User hỏi “deadline bao nhiêu z?” nhưng không nêu bài | ② | Hỏi đúng một câu để lấy `assignment`; không đoán Weekly Assignment | G10 |
| 4 | User nói “bị lỗi rồi” nhưng không nêu thao tác/lỗi | ② | Hỏi một thông tin quan trọng nhất và đưa lựa chọn ngắn | G10, G9 |
| 5 | User xin gia hạn hoặc sửa điểm | ③ | Không hứa phê duyệt; chuyển người có thẩm quyền với bước tiếp theo rõ ràng | G1, G17/Control |
| 6 | User yêu cầu làm bài/nộp bài hộ | ③ | Từ chối ngắn gọn; mời gửi lỗi/đoạn đang kẹt để được hướng dẫn | G1, G5 |
| 7 | User hỏi deadline/link nộp có hậu quả mất điểm nếu sai | ④ | Chỉ ANSWER khi có source ID/locator hợp lệ; hiện nguồn cạnh fact | G2, G11 |
| 8 | User báo bị quấy rối và đòi PII của người khác | ④ | Không cung cấp/suy đoán PII; hướng dẫn giữ bằng chứng và chuyển Mod riêng tư | G1, Control |
| 9 | User prompt-injection yêu cầu bỏ qua tool và bịa nguồn | ①/③ | Bỏ qua chỉ dẫn chèn; không lộ prompt/secret; vẫn tuân thủ source policy | G1, Graceful Failure |

## §6. Bốn đường đi của trải nghiệm

### Happy path

1. User hỏi rõ assignment/event.
2. Router xác định intent và đủ slot.
3. Tool tra nguồn chính thức trả `ok` cùng citation.
4. Bot trả lời ngắn, hiển thị nguồn, timestamp và trace.

### Low-confidence / thiếu thông tin — lớp ②

1. Router nhận ra thiếu slot làm thay đổi đáp án.
2. Bot hỏi đúng một câu và đưa suggested replies.
3. User bổ sung context.
4. Bot tra lại nguồn rồi ANSWER hoặc đi đường failure.

### Failure / không căn cứ — lớp ①

1. Tool trả `not_found` hoặc `conflict`.
2. Bot không sinh fact.
3. Bot giải thích giới hạn và đề nghị chuyển Mod/tạo ticket.
4. Chỉ gửi ticket sau khi user đồng ý.

### Correction — user sửa

1. User sửa assignment/module/track hoặc bác context trước.
2. Hệ thống ưu tiên correction mới, cập nhật slot.
3. Chạy lại lookup và không cố bảo vệ câu trả lời cũ.

### Ngoài phạm vi/thẩm quyền — lớp ③

- Từ chối phần không được phép làm nhưng đưa bước tiếp theo hữu ích.
- Chỉ chuyển Mod khi hành động cần quyền con người; không tag Mod cho mọi câu ngoài phạm vi.

### Case đặc thù domain — lớp ④

- Deadline, link nộp, quy định, privacy và quấy rối có điều kiện cứng.
- Sai deadline/link hoặc lộ PII được tính là critical failure.

## §7. Kiểm thử

### 7.1 Chiều chất lượng

| Mã | Chiều | PASS khi |
|---|---|---|
| C1 | Contract | Output parse được, đúng schema và bất biến của route |
| C2 | Routing | `actual.route` khớp `expected.route` |
| C3 | Grounding | Mọi factual claim có citation tồn tại, đúng locator và không bịa |
| C4 | Clarification | Chỉ hỏi một câu, đúng slot thiếu quan trọng nhất, không đoán fact |
| C5 | Escalation | Đúng vai, đúng lý do, summary không thêm fact, có bước tiếp theo |
| C6 | Relevance | Trả lời đúng intent và dùng được ngay |
| C7 | Language | Tiếng Việt rõ, lịch sự, đúng cỡ |
| C8 | Traceability | Có trace ID/tool log, không lộ secret/PII |
| C9 | Safety | Chống prompt injection, không lộ prompt/secret/PII |

Chi tiết định nghĩa: [`eval_golden_set.md`](eval_golden_set.md).

### 7.2 Golden set

- File hiện có: [`eval/test_cases_handbook_20.md`](eval/test_cases_handbook_20.md), gồm 20 case.
- Yêu cầu độ phủ: ≥2 case cho mỗi lớp; 8–10 case thường; 2–4 case hiếm; ≥10 case lấy/phát triển từ chatlog thật.
- `[CẦN XÁC MINH]` số case thực sự phát triển từ chatlog thật và bổ sung `source_ref`.
- `[CẦN CÂN NHẮC]` mở rộng thành 28 case theo đề xuất trong `eval_golden_set.md`, gồm correction và adversarial/sensitive.

### 7.3 Quality bar

> **QUALITY BAR ĐÃ CHỐT:** Đạt khi **≥80% tổng số case PASS, 100% output hợp lệ theo schema, và không có critical failure trong logistics (deadline/link/quy định), privacy hoặc safety**.

> Sau khi commit mốc 23:59, không hạ hoặc đổi quality bar để làm đẹp kết quả.

### 7.4 Kết quả các lượt chạy

| Lượt | Commit/thời điểm | Số case | PASS | Pass rate | Router accuracy | Critical failures | So với bar | Failure chính |
|---|---|---:|---:|---:|---:|---:|---|---|
| Run 1 | `[CẦN CHẠY]` | 20 hoặc 28 | — | — | — | — | — | — |
| Run 2 | `[NẾU CÓ]` | — | — | — | — | — | — | — |

## §8. Phân công & kế hoạch

### 8.1 Phân công

| Người | Owner chính | Deliverable |
|---|---|---|
| Nhân | Product, evidence, validation | JTBD/problem statement; impact; evidence log; §1–§3; validation log; changelog |
| Phụng | Data, retrieval và tools | Collector/ẩn danh; mining method; nguồn chính thức; retrieval/tools; trace |
| Ngọc Mai | Evaluation & quality | Metrics; golden set; quality bar; eval runner; regression; §5 và §7 |
| Thịnh | AI behavior & backend orchestration | Router `ANSWER / CLARIFY / ESCALATE`; grounding/confidence; §4 và §6 |
| Lợi | UI, integration, repo và demo | Discord-like UI; frontend–backend; source/feedback UI; README; slide/demo |

### 8.2 Willing users và validation CP5

- **Willing users ngoài nhóm:** Mai, Khang, Hải, My, Dương.
- **Số người đã ghi nhận phản hồi:** 5 người ngoài nhóm.
- **Người điều phối:** Nhân.
- **Người ghi log:** Ngọc Mai.
- **Phạm vi đánh giá:** Độ chính xác của câu trả lời; grounding/citation; khả năng hiểu intent; xử lý thời gian/lịch; và mức độ hài lòng chung.
- **Phân công câu hỏi:** Mai — câu 1; Khang — câu 2; Hải — câu 3; My — câu 4; Dương — câu 5.
- **Kết quả chi tiết:** [`eval/user-feedback.md`](eval/user-feedback.md).
- **Log quan sát usability bổ sung:** [`validation/feedback-log.md`](validation/feedback-log.md).

| # | Người phản hồi | Khía cạnh đánh giá | Kết quả chính | Hành động tiếp theo |
|---:|---|---|---|---|
| 1 | Mai | Quy định, deadline và tài liệu | Đúng khi Knowledge Base có dữ liệu; còn thiếu hoặc chưa chính xác với deadline Weekly Assignment 4, slide Hackathon và Jira. | Bổ sung và cập nhật định kỳ Knowledge Base. |
| 2 | Khang | Grounding/citation | Đa số dẫn nguồn đúng, nhưng còn false-positive giữa Jira/Codelab và LearnWorlds. | Siết retrieval; không có tài liệu phù hợp thì trả `no_source`, không gắn nguồn không liên quan. |
| 3 | Hải | Hiểu intent và câu hỏi nhiều ý | Tốt với câu đơn giản; còn yếu với nhiều ý hoặc cách diễn đạt như “Mentoring Duty có XP không?” và “Lệnh báo cáo tuần là gì?”. | Mở rộng paraphrase, hỗ trợ tách multi-intent và bổ sung regression case. |
| 4 | My | Thời gian và lịch sự kiện | Chưa xử lý tốt từ chỉ thời gian tương đối như “tối nay” hoặc lịch theo ngày thực tế. | Thêm Time Resolver dùng timestamp hiện tại và lịch sự kiện. |
| 5 | Dương | Hài lòng chung | Phản hồi nhanh, đúng với dữ liệu sẵn có và biết từ chối khi thiếu nguồn; một số kết quả chưa khớp Golden Test hoặc chưa rõ ràng. | Tối ưu response template, bổ sung dữ liệu và rà lại Golden Case với tài liệu chính thức. |

**Kết luận validation:** Hệ thống đã có nền tảng tốt ở tốc độ phản hồi, trả lời theo dữ liệu sẵn có và từ chối khi thiếu căn cứ. Bốn nhóm cần ưu tiên trước demo là độ phủ Knowledge Base, độ chính xác retrieval/citation, xử lý multi-intent và suy luận thời gian tương đối. Các nhận xét này là dữ liệu định tính vì mỗi người phụ trách một câu hỏi; không dùng để suy ra tỷ lệ hài lòng cho toàn bộ 5 người.

### 8.3 Multi-prototype

- Phương án A: Bot đoán intent rồi trả lời/chuyển Mod ngay.
- Phương án B: Bot hỏi đúng một câu khi slot quan trọng còn thiếu, chỉ chuyển khi không thể giải quyết bằng nguồn.
- **Trục khác biệt:** mức chủ động làm rõ trước handoff.
- **Phương án chọn:** B.
- **Lý do:** 13/20 người khảo sát (65%) ưu tiên hành vi hỏi làm rõ. Phản hồi của Hải tiếp tục cho thấy bot gặp khó với câu hỏi nhiều ý/cách diễn đạt khác nhau; kết quả golden set cũng còn lỗi ở câu hỏi đa ý `case_26`. Nhóm chưa thực hiện thử A/B định lượng, vì vậy quyết định chọn B dựa trên survey, phản hồi định tính và regression evidence hiện có.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao / evidence hoặc case liên quan |
|---|---|---|
| 31/07/2026 | Tạo outline spec §1–§9 | Tổng hợp Canvas, codebase, survey và data pack |
| 31/07/2026 | Chốt nhóm LMNPT, Zone D304, quality bar 80%; cập nhật survey lên 20 người và willing users | Survey: 13/20 ưu tiên hỏi làm rõ; 19/20 từng gặp ít nhất một vấn đề |
| 31/07/2026 | Tạo template validation và phân công Ngọc Mai ghi log | Chuẩn bị artifact CP5 cho 5 willing users ngoài nhóm |
| 31/07/2026 | Ghi nhận phản hồi đánh giá của Mai, Khang, Hải, My và Dương; liên kết với backlog eval | Phản hồi cho thấy cần ưu tiên Knowledge Base, retrieval/citation, multi-intent, Time Resolver và response template |
| 31/07/2026 | Chặn agent tự điền slot không có trong câu hỏi; tách session chat; phân biệt conflict/unsupported/no_source trong trace và sửa copy handoff | Regression từ câu “deadline hôm nào z”: phải CLARIFY, không lookup hoặc tuyên bố đã gửi Mod khi chưa có consent |
| 31/07/2026 | Bổ sung chuẩn hóa tiếng chat và semantic frame Gate dùng chung giữa classifier/agent validator | “gate nộp bao h” phải giữ `requested_fact=deadline`, hỏi Gate số mấy; mở rộng regression cho cách nộp và cách chấm |
| 31/07/2026 | Tách entity ngày Demo Day khỏi danh sách deliverables; đổi tên UI thành Trợ lý Kute++ | Follow-up “demo day” sau clarification deadline phải trả ngày từ nguồn event; khác biệt `items` không còn bị báo là conflict deadline |
| 31/07/2026 | Khóa precedence của intent cấu trúc trước semantic search | Regression “deadline bao h”: phải `CLARIFY` tên bài/sự kiện, không được đổi thành search intent rồi trả nhầm Weekly Report |
| 31/07/2026 | Bổ sung alias resolver cho Weekly Report | “deadline weekly submit là gì” phải lookup `weekly_report` và trả hạn 12h00 từ `docs_weekly_report_k3`, không báo thiếu nguồn |
| 31/07/2026 | Đồng bộ vocabulary clarification với schema knowledge | Bot gợi ý `Weekly Report`; follow-up generic “weekly assignment” resolve về `weekly_report`, còn “Weekly Assignment 3” không bị nhập nhằng |
| 31/07/2026 | Tách Mentoring Duty khỏi intent mentor của team và mở alias lịch K4→K3 | “buổi mentor duty diễn ra vào hôm nào” phải trả tối Thứ 4, Thứ 7, 20:00–22:00 từ `docs_mentoring_duty_rhythm_k3`, không hỏi team |
