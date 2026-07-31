th# 20 Test Case cho Trợ lý Kute

> Bộ test rút gọn, ưu tiên các lỗi nghiêm trọng và các chức năng người dùng thường hỏi.

## Hướng dẫn chấm

Mỗi tiêu chí được chấm từ **0 đến 2 điểm**:

| Tiêu chí | 0 điểm | 1 điểm | 2 điểm |
|---|---|---|---|
| Đúng intent | Trả nhầm chủ đề | Đúng một phần | Trả lời đúng nhu cầu chính |
| Đủ ý | Bỏ phần lớn câu hỏi | Thiếu một phần | Trả lời đầy đủ các ý |
| Chính xác/hiện hành | Sai hoặc bịa | Chưa đủ căn cứ | Đúng và có căn cứ hiện hành |
| Hữu ích/hành động | Không có hướng dẫn | Hướng dẫn chung | Có bước thực hiện rõ ràng |

**PASS:** Tổng điểm từ **7/8** và không tiêu chí nào dưới **1 điểm**.

---

## Test 01 — KUTE-REG-007

- **Ưu tiên:** P2
- **Loại test:** Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** Weekly Report
- **Lỗi cần kiểm tra:** Mẫu trả lời lặp

### Input

```text
<@1480861618358452417>  lệnh báo cáo tuần
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan. Phải trả lời đúng khía cạnh được hỏi: lệnh nộp, nội dung, người nộp, lịch nộp hoặc XP; không đánh tráo giữa các khía cạnh.
- **Không được:** Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
weekly report chỉ cần một bạn đại diện nộp báo cáo cho cả team nhé
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531598622901145620
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1531598634070577223

---

## Test 02 — KUTE-REG-096

- **Ưu tiên:** P2
- **Loại test:** Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** Weekly Report
- **Lỗi cần kiểm tra:** Mẫu trả lời lặp

### Input

```text
<@1480861618358452417> hướng dẫn nộp báo cáo tuần
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan. Phải trả lời đúng khía cạnh được hỏi: lệnh nộp, nội dung, người nộp, lịch nộp hoặc XP; không đánh tráo giữa các khía cạnh.
- **Không được:** Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
weekly report chỉ cần một bạn đại diện nộp báo cáo cho cả team nhé
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531844754772463828
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1531844766856249515

---

## Test 03 — KUTE-REG-180

- **Ưu tiên:** P2
- **Loại test:** Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** XP / rank / điểm; Mentor Duty / coaching
- **Lỗi cần kiểm tra:** Mẫu trả lời lặp

### Input

```text
<@1480861618358452417> mentor duty có xp k
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan. Phải phân biệt XP cá nhân, XP thành viên và tổng XP của team. Phải phân biệt Mentor Duty với Workshop, Office Hours và Weekly Report.
- **Không được:** Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Bạn gõ /weekly submit sẽ hiển thị gợi ý những thông tin cần nộp nhé
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532029217867563069
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532029228508385510

---

## Test 04 — KUTE-REG-201

- **Ưu tiên:** P2
- **Loại test:** Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** Daily Stand-up
- **Lỗi cần kiểm tra:** Mẫu trả lời lặp

### Input

```text
<@1480861618358452417> daily có tác dụng và vai trò gì
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan.
- **Không được:** Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Khung giờ nộp daily hàng ngày là từ 0h-10h sáng nhé. Nộp muộn vẫn được ghi nhận nhưng không +XP
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532219864704352437
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532219875957805226

---

## Test 05 — KUTE-REG-158

- **Ưu tiên:** P2
- **Loại test:** Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** Team / group; XP / rank / điểm
- **Lỗi cần kiểm tra:** Mẫu trả lời lặp

### Input

```text
<@1480861618358452417> Làm sao để xem tổng điểm kinh nghiệm hiện có của nhóm
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan. Phải phân biệt team dự án, group Mentor và quyền/thủ tục thay đổi nhóm. Phải phân biệt XP cá nhân, XP thành viên và tổng XP của team.
- **Không được:** Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Các bạn có thể theo dõi hoặc tìm kiếm điểm XP của mình bằng Discord ID tại kênh https://discord.com/channels/1526532830627102781/1527920226862239897, hoặc xem lịch sử XP của bản thân bằng `/rank`
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531963882065760266
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1531963893029671065

---

## Test 06 — KUTE-REG-109

- **Ưu tiên:** P0
- **Loại test:** Multi-intent + Độ mới của thông tin + Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** Weekly Report; Lịch / deadline; Gate / deliverable
- **Lỗi cần kiểm tra:** Câu hỏi nhiều ý; Phụ thuộc thời gian; Mẫu trả lời lặp

### Input

```text
<@1480861618358452417> gate khi nào? và nộp weekly submit khi nào? 2 sự kiện này khác gì nhau
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot nhận diện và trả lời đầy đủ từng ý trong một câu hỏi. Kiểm tra lịch, deadline và sự kiện được trả lời theo dữ liệu hiện hành. Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Tách câu hỏi thành các ý và trả lời từng ý; phần chưa có dữ liệu phải được nêu rõ. Nêu ngày/giờ cụ thể; ưu tiên nguồn/thông báo mới nhất; nếu chưa xác minh được phải nói rõ mức độ chắc chắn. Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan. Phải trả lời đúng khía cạnh được hỏi: lệnh nộp, nội dung, người nộp, lịch nộp hoặc XP; không đánh tráo giữa các khía cạnh. Phải dùng mốc ngày/giờ cụ thể và phân biệt lịch cố định với lịch đã được thông báo cho ngày đang hỏi. Phải phân biệt Gate với Weekly Report và trả đúng deadline/deliverable/lệnh theo câu hỏi.
- **Không được:** Không chỉ trả lời một ý rồi bỏ qua các ý còn lại. Không dùng lịch cũ, từ 'thường', hoặc suy đoán để khẳng định sự kiện đang diễn ra. Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
/gate submit là lệnh dùng để nộp gate cho team của mình đó. 
Bạn có thể kiểm tra các gate đang cần nộp bằng /gate list, xem chi tiết một gate bằng /gate view

Nếu bạn đang thực hiện các thử thách hoặc nhiệm vụ (gate), hãy sử dụng lệnh này để gửi kết quả cho team kiểm tra nhé! 
Link trong gate là link tổng hợp các deliverables, có thể là link github, google drive, docs, ...
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531854130157588511
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1531854140836282548

---

## Test 07 — KUTE-REG-002

- **Ưu tiên:** P1
- **Loại test:** Multi-intent + Escalation đúng lúc + Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** Team / group; Đề tài / exam
- **Lỗi cần kiểm tra:** Câu hỏi nhiều ý; Đề xuất/nhắc tới ticket; Mẫu trả lời lặp

### Input

```text
<@1480861618358452417>  nhóm mình có 4 người nhưng có 2 bạn nghỉ học, giờ còn 2 người thì có join vào nhóm khác hoặc đổi đề tài khác được không
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot nhận diện và trả lời đầy đủ từng ý trong một câu hỏi. Kiểm tra bot chỉ chuyển ticket khi thật sự cần thao tác của Mod/BTC. Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Tách câu hỏi thành các ý và trả lời từng ý; phần chưa có dữ liệu phải được nêu rõ. Trả lời phần thông tin có thể xác nhận trước; nếu cần ticket, nêu rõ lý do, lệnh/cách tạo và thông tin cần cung cấp. Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan. Phải phân biệt team dự án, group Mentor và quyền/thủ tục thay đổi nhóm. Phải phân biệt chọn đề tài, kiểm tra đề tài còn trống và đổi đề tài.
- **Không được:** Không chỉ trả lời một ý rồi bỏ qua các ý còn lại. Không dùng ticket để né trả lời toàn bộ câu hỏi. Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Trong trường hợp có conflict các bạn có thể tạo ticket yêu cầu đổi đề tài trước thời hạn nhé.
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531553767378653215
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1531553779273437195

---

## Test 08 — KUTE-REG-189

- **Ưu tiên:** P0
- **Loại test:** Độ mới của thông tin
- **Chủ đề:** Lịch / deadline
- **Lỗi cần kiểm tra:** Phụ thuộc thời gian

### Input

```text
<@1480861618358452417> tối nay
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra lịch, deadline và sự kiện được trả lời theo dữ liệu hiện hành.
- **Bắt buộc:** Nêu ngày/giờ cụ thể; ưu tiên nguồn/thông báo mới nhất; nếu chưa xác minh được phải nói rõ mức độ chắc chắn. Phải dùng mốc ngày/giờ cụ thể và phân biệt lịch cố định với lịch đã được thông báo cho ngày đang hỏi.
- **Không được:** Không dùng lịch cũ, từ 'thường', hoặc suy đoán để khẳng định sự kiện đang diễn ra.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Tối nay là **Thứ 5 (30/07)**, chúng mình có lịch hoạt động khá sôi nổi nè:

*   **Workshop:** Tối nay có buổi Workshop định kỳ của chương trình đó. Bạn nhớ check thông báo ở các channel để vào đúng giờ nha! ✨
*   **Mentor Duty:** 
    *   **Thời gian:** 20:00 – 22:00
    *   **Nội dung:** Giải đáp thắc mắc, gỡ khó và hỗ trợ tiến độ cho các team.
    *   **Link Zoom cố định:** [Tham gia tại đây](https://zoom.us/j/92862242782?pwd=9TkBzI58DeQCuzGbBJifDPYCY8VYMf.1)

Bạn sắp xếp thời gian tham gia để "nạp" thêm kiến thức và đẩy nhanh tiến độ project nhé! 🚀
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532087421842227471
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532087464427126925

---

## Test 09 — KUTE-REG-198

- **Ưu tiên:** P0
- **Loại test:** Độ mới của thông tin
- **Chủ đề:** Lịch / deadline
- **Lỗi cần kiểm tra:** Phụ thuộc thời gian

### Input

```text
<@1480861618358452417> tối nay có sự kiện gì ?
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra lịch, deadline và sự kiện được trả lời theo dữ liệu hiện hành.
- **Bắt buộc:** Nêu ngày/giờ cụ thể; ưu tiên nguồn/thông báo mới nhất; nếu chưa xác minh được phải nói rõ mức độ chắc chắn. Phải dùng mốc ngày/giờ cụ thể và phân biệt lịch cố định với lịch đã được thông báo cho ngày đang hỏi.
- **Không được:** Không dùng lịch cũ, từ 'thường', hoặc suy đoán để khẳng định sự kiện đang diễn ra.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Tối nay (Thứ Năm) thường sẽ có các hoạt động định kỳ cực "xịn" của cộng đồng mình nè:

*   **Mentor Duty (20:00 – 22:00):** Nơi bạn có thể gặp các Mentor để giải đáp thắc mắc.
    *   Link Zoom: [Tham gia tại đây](https://zoom.us/j/92862242782?pwd=9TkBzI58DeQCuzGbBJifDPYCY8VYMf.1)
*   **Office Hours (thường từ 20:00 – 21:00):** Các buổi chia sẻ chuyên sâu hoặc giải đáp thắc mắc tại kênh Stage.
*   **Workshop:** Các buổi học thuật cũng thường diễn ra vào các buổi tối trong tuần.

Để chắc chắn nhất về nội dung chi tiết và link tham gia của tối nay, bạn hãy ghé qua kênh **`#📣-thông-báo`** để xem lịch cụ thể vừa được cập nhật nhé! ✨
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532207986015993968
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532208027862827019

---

## Test 10 — KUTE-REG-216

- **Ưu tiên:** P0
- **Loại test:** Độ mới của thông tin
- **Chủ đề:** Lịch / deadline
- **Lỗi cần kiểm tra:** Phụ thuộc thời gian

### Input

```text
<@1480861618358452417> tối nay có gì không nhỉ
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra lịch, deadline và sự kiện được trả lời theo dữ liệu hiện hành.
- **Bắt buộc:** Nêu ngày/giờ cụ thể; ưu tiên nguồn/thông báo mới nhất; nếu chưa xác minh được phải nói rõ mức độ chắc chắn. Phải dùng mốc ngày/giờ cụ thể và phân biệt lịch cố định với lịch đã được thông báo cho ngày đang hỏi.
- **Không được:** Không dùng lịch cũ, từ 'thường', hoặc suy đoán để khẳng định sự kiện đang diễn ra.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Tối nay **Thứ 5 (30/07)** là một buổi tối khá "năng suất" của cộng đồng AI20K đó nha! 🔥

Theo lịch trình định kỳ, tối nay bạn cần chú ý hai hoạt động chính sau:

1.  **Workshop định kỳ (Thường bắt đầu lúc 20:00):**
    *   Tối Thứ 5 và Chủ Nhật hàng tuần thường là lịch của các buổi Workshop quan trọng. Đây là nơi bạn cập nhật kiến thức mới và các kỹ thuật "xịn sò" để áp dụng vào dự án của team.
    *   **Lưu ý:** Bạn hãy check ngay kênh **`#📣-thông-báo`** để xem chủ đề cụ thể của tối nay và lấy link tham gia nhé!

2.  **Mentor Duty (20:00 – 22:00):**
    *   Nếu team bạn đang gặp "ca khó", bug fix mãi không xong hoặc cần tư vấn về logic đề tài, hãy ghé ngay buổi Mentor Duty.
    *   **Link Zoom cố định:** [https://zoom.us/j/92862242782?pwd=9TkBzI58DeQCuzGbBJifDPYCY8VYMf.1](https://zoom.us/j/92862242782?pwd=9TkBzI58DeQCuzGbBJifDPYCY8VYMf.1)
    *   Đây là cơ hội vàng để được các Mentor "cầm tay chỉ việc" trực tiếp đó.

**Lời khuyên cho bạn:** Tối nay hãy rủ các thành viên khác trong **Team 219** cùng tham gia Workshop để nắm bắt thông tin đồng bộ, sau đó nếu có gì chưa rõ thì "tạt" qua Mentor Duty hỏi luôn cho nóng nhé! 😉

Chúc team bạn có một buổi tối "build" thật cháy! 🚀
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532225536615649461
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532225593050005696

---

## Test 11 — KUTE-REG-193

- **Ưu tiên:** P0
- **Loại test:** Multi-intent + Độ mới của thông tin
- **Chủ đề:** Lịch / deadline; Mentor Duty / coaching; Workshop / Office Hours / Lab
- **Lỗi cần kiểm tra:** Câu hỏi nhiều ý; Phụ thuộc thời gian

### Input

```text
<@1480861618358452417> tối thứ 5 là workshop hay là mentor duty vậy ? Hay từ tuần này 2 cái là 1 ?
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot nhận diện và trả lời đầy đủ từng ý trong một câu hỏi. Kiểm tra lịch, deadline và sự kiện được trả lời theo dữ liệu hiện hành.
- **Bắt buộc:** Tách câu hỏi thành các ý và trả lời từng ý; phần chưa có dữ liệu phải được nêu rõ. Nêu ngày/giờ cụ thể; ưu tiên nguồn/thông báo mới nhất; nếu chưa xác minh được phải nói rõ mức độ chắc chắn. Phải dùng mốc ngày/giờ cụ thể và phân biệt lịch cố định với lịch đã được thông báo cho ngày đang hỏi. Phải phân biệt Mentor Duty với Workshop, Office Hours và Weekly Report.
- **Không được:** Không chỉ trả lời một ý rồi bỏ qua các ý còn lại. Không dùng lịch cũ, từ 'thường', hoặc suy đoán để khẳng định sự kiện đang diễn ra.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Chào bạn nha! Để mình check lại lịch cho bạn chính xác nè:

Tối **Thứ 5** hàng tuần là buổi **Workshop** bạn nhé! Hai hoạt động này có mục đích khác nhau nên vẫn diễn ra riêng biệt, không gộp chung đâu nè. 

Cụ thể lịch cố định của chúng mình như sau:

*   **Workshop:** Tối **Thứ 5** & **Chủ Nhật** (Nơi chia sẻ kiến thức, kỹ năng mới).
*   **Mentoring Duty:** Tối **Thứ 4** & **Thứ 7** (Nơi các team gặp gỡ Mentor/Lab Coach để giải đáp thắc mắc và review tiến độ).

Bạn nhớ note lại lịch để không bỏ lỡ các buổi Workshop quan trọng tối nay nhé! Chúc bạn có một buổi học thật nhiều kiến thức bổ ích. 🚀✨
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532198979708915864
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532199021081268340

---

## Test 12 — KUTE-REG-226

- **Ưu tiên:** P0
- **Loại test:** Truy xuất / tóm tắt + Độ mới của thông tin
- **Chủ đề:** Lịch / deadline
- **Lỗi cần kiểm tra:** Nhu cầu tìm kiếm/tóm tắt; Phụ thuộc thời gian

### Input

```text
<@1480861618358452417> cho tôi link slide buổi hackathon hôm nay
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả kết quả tìm kiếm hoặc bản tóm tắt trực tiếp. Kiểm tra lịch, deadline và sự kiện được trả lời theo dữ liệu hiện hành.
- **Bắt buộc:** Trả về nội dung tìm được, link liên quan và tóm tắt ngắn; nói rõ phạm vi dữ liệu đã tìm. Nêu ngày/giờ cụ thể; ưu tiên nguồn/thông báo mới nhất; nếu chưa xác minh được phải nói rõ mức độ chắc chắn. Phải dùng mốc ngày/giờ cụ thể và phân biệt lịch cố định với lịch đã được thông báo cho ngày đang hỏi.
- **Không được:** Không chỉ hướng người dùng sang một kênh để tự tìm lại. Không dùng lịch cũ, từ 'thường', hoặc suy đoán để khẳng định sự kiện đang diễn ra.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Link nộp bài: [Nộp dự án demo day tại đây](https://phoenix.note.transformerlabs.ai/demo-day)

1. Giai đoạn 1: Nộp hồ sơ sơ bộ
**Deadline: 23:59:00 28/06/2026**
Yêu cầu bắt buộc: MVP, Video Demo, Slides

2. Giai đoạn 2: Hoàn thiện sản phẩm
**Deadline: 23:00:00 08/07/2026** (updated ~~23:59 05/07/2026~~)
Cập nhật bản chuẩn cuối sản phẩm hoàn thiện.

Lưu ý: tất cả các thành viên trong team phải có AI Logs thì mới đủ điều kiện nộp
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532234191163490344
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532234201724751982

---

## Test 13 — KUTE-REG-215

- **Ưu tiên:** P0
- **Loại test:** Nhận diện intent + Truy xuất / tóm tắt + Cá nhân hóa / chống trả lời mẫu
- **Chủ đề:** Tìm kiếm / tóm tắt; Workshop / Office Hours / Lab
- **Lỗi cần kiểm tra:** Có dấu hiệu trả nhầm intent; Nhu cầu tìm kiếm/tóm tắt; Mẫu trả lời lặp

### Input

```text
<@1480861618358452417> Tìm cho tôi tài liệu workshop 2
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot hiểu đúng mục đích chính của người dùng. Kiểm tra bot trả kết quả tìm kiếm hoặc bản tóm tắt trực tiếp. Kiểm tra bot trả lời đúng chi tiết câu hỏi thay vì áp một mẫu chung.
- **Bắt buộc:** Trả lời trực tiếp intent chính ngay đầu; thông tin bổ sung chỉ được đưa sau khi đã giải quyết câu hỏi. Trả về nội dung tìm được, link liên quan và tóm tắt ngắn; nói rõ phạm vi dữ liệu đã tìm. Câu trả lời phải bám sát từ khóa và nhu cầu cụ thể trong câu hỏi; chỉ đưa thông tin liên quan. Phải đưa kết quả trực tiếp kèm link hoặc nêu rõ không tìm thấy trong phạm vi nào.
- **Không được:** Không chuyển sang chủ đề, lệnh hoặc quy trình khác. Không chỉ hướng người dùng sang một kênh để tự tìm lại. Không lặp mẫu chung hoặc trả lời một câu quen thuộc nhưng không giải quyết đúng yêu cầu.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
các thông tin về các buổi WS (workshop), OH (office hours), mentor duty sẽ được cập nhật ở channel Thông báo nhé https://discord.com/channels/1526532830627102781/1527920171963125953
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532224926944202833
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532224937052340285

---

## Test 14 — KUTE-REG-174

- **Ưu tiên:** P1
- **Loại test:** Truy xuất / tóm tắt + Escalation có ích
- **Chủ đề:** Team / group; Tìm kiếm / tóm tắt
- **Lỗi cần kiểm tra:** Nhu cầu tìm kiếm/tóm tắt; Chuyển trực tiếp cho Mod

### Input

```text
<@1480861618358452417> tổng hợp tin nhắn thông tin trong nhóm từ 18h đến 20h25 phút
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả kết quả tìm kiếm hoặc bản tóm tắt trực tiếp. Kiểm tra bot vẫn cung cấp hỗ trợ ban đầu trước khi chuyển Mod.
- **Bắt buộc:** Trả về nội dung tìm được, link liên quan và tóm tắt ngắn; nói rõ phạm vi dữ liệu đã tìm. Cung cấp câu trả lời một phần, bước tự kiểm tra hoặc câu hỏi làm rõ; chỉ chuyển Mod cho phần cần quyền xác nhận. Phải phân biệt team dự án, group Mentor và quyền/thủ tục thay đổi nhóm. Phải đưa kết quả trực tiếp kèm link hoặc nêu rõ không tìm thấy trong phạm vi nào.
- **Không được:** Không chỉ hướng người dùng sang một kênh để tự tìm lại. Không chỉ tag Mod hoặc nói 'chưa nắm đủ' mà không giúp người dùng bước nào.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
<@&1527919786850390116>

Thông tin câu này mình chưa nắm đủ, nên mình sẽ nhờ đội ngũ Mod trả lời giúp bạn cho chính xác nha!
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532016239411724378
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532016333489705040

---

## Test 15 — KUTE-REG-176

- **Ưu tiên:** P0
- **Loại test:** Truy xuất / tóm tắt + Escalation có ích + Escalation đúng lúc + Độ chính xác lệnh
- **Chủ đề:** Team / group; Tìm kiếm / tóm tắt; Tài khoản / tên / điểm danh
- **Lỗi cần kiểm tra:** Nhu cầu tìm kiếm/tóm tắt; Chuyển trực tiếp cho Mod; Đề xuất/nhắc tới ticket; Lệnh có dấu hiệu suy đoán

### Input

```text
<@1480861618358452417> nhóm mọi người đặt tên ở đâu nhỉ 😬, t thấy mọi người có mấy cái tên vui vui mà nhón t được ghép tự động nên chưa tìm ra chỗ đổi
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot trả kết quả tìm kiếm hoặc bản tóm tắt trực tiếp. Kiểm tra bot vẫn cung cấp hỗ trợ ban đầu trước khi chuyển Mod. Kiểm tra bot chỉ chuyển ticket khi thật sự cần thao tác của Mod/BTC. Kiểm tra bot không tự bịa hoặc suy đoán lệnh Discord.
- **Bắt buộc:** Trả về nội dung tìm được, link liên quan và tóm tắt ngắn; nói rõ phạm vi dữ liệu đã tìm. Cung cấp câu trả lời một phần, bước tự kiểm tra hoặc câu hỏi làm rõ; chỉ chuyển Mod cho phần cần quyền xác nhận. Trả lời phần thông tin có thể xác nhận trước; nếu cần ticket, nêu rõ lý do, lệnh/cách tạo và thông tin cần cung cấp. Chỉ đưa lệnh đã được xác nhận trong nguồn dữ liệu; nếu chưa chắc, nói rõ và chỉ cách kiểm tra chính thức. Phải phân biệt team dự án, group Mentor và quyền/thủ tục thay đổi nhóm. Phải đưa kết quả trực tiếp kèm link hoặc nêu rõ không tìm thấy trong phạm vi nào.
- **Không được:** Không chỉ hướng người dùng sang một kênh để tự tìm lại. Không chỉ tag Mod hoặc nói 'chưa nắm đủ' mà không giúp người dùng bước nào. Không dùng ticket để né trả lời toàn bộ câu hỏi. Không tạo tên lệnh, tham số hoặc chức năng chưa được xác minh.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Ahihi, đúng rồi nè! Nhìn các team khác có tên "kêu" như *AI Avengers* hay *Code Chiến Thần* thấy cũng ham đúng không nè? 🏆

Thường thì khi mới được ghép tự động, team sẽ được đặt tên theo mã số (ví dụ: `t-042`). Để đổi sang một cái tên "cool ngầu" và mang bản sắc riêng, bạn có thể thử 2 cách sau nhé:

1.  **Kiểm tra lệnh Bot:** Bạn thử gõ `/myteam` vào khung chat xem có hiện ra gợi ý lệnh nào như `/myteam rename` hoặc `/myteam setname` không nhé. 
    *   *Lưu ý:* Thông thường quyền đổi tên này sẽ dành cho **Team Leader** (Trưởng nhóm) thực hiện đó nha.

2.  **Nhờ Mod hỗ trợ:** Nếu bạn không tìm thấy lệnh tự đổi, đừng ngần ngại dùng lệnh **`/ticket create`** để mở một ticket hỗ trợ. Bạn chỉ cần nhắn: *"Nhờ Mod đổi tên hiển thị của team t-XXX thành [Tên mới] giúp tụi mình với!"*. Các anh chị Mod sẽ cập nhật trên hệ thống và bảng xếp hạng cho team bạn ngay.

**Một vài lưu ý nhỏ cho team mình:**
*   **Mã số team là bất biến:** Dù bạn có đặt tên "vui vẻ" thế nào thì mã số gốc (ví dụ: `t-042`) vẫn cực kỳ quan trọng để BTC quản lý, chấm điểm và phân quyền kênh chat. Đừng quên nó khi làm báo cáo hay nộp Gate nhé!
*   **Tên team:** Hãy chọn một cái tên thật năng lượng, tích cực và không vi phạm quy định chung của cộng đồng nha.

Team bạn định đặt tên là gì thế? Bật mí cho mình biết với, biết đâu mình lại có gợi ý gì hay ho cho bạn thì sao! 😉✨
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532020834288537700
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1532020903788150814

---

## Test 16 — KUTE-NR-001

- **Ưu tiên:** P1
- **Loại test:** Coverage / không bỏ sót
- **Chủ đề:** Chưa xác định
- **Lỗi cần kiểm tra:** Chưa trả lời

### Input

```text
<@1480861618358452417> cách kiểm tra 1 đề tài đã có nhóm nào chọn chưa
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot luôn phản hồi câu hỏi hợp lệ và không bỏ sót mention.
- **Bắt buộc:** Phải có phản hồi trực tiếp. Trả lời nếu có dữ liệu; nếu thiếu dữ liệu, nêu rõ giới hạn và đưa bước tiếp theo hoặc một câu hỏi làm rõ cụ thể.
- **Không được:** Không im lặng, bỏ qua mention hoặc chỉ chuyển người dùng đi nơi khác mà không có hướng dẫn.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
[Không có câu trả lời trực tiếp trong dữ liệu]
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531657262249021530

---

## Test 17 — KUTE-NR-003

- **Ưu tiên:** P1
- **Loại test:** Coverage / không bỏ sót
- **Chủ đề:** Chưa xác định
- **Lỗi cần kiểm tra:** Chưa trả lời

### Input

```text
Gate 1 nộp những gì và thời gian nộp là bao giờ <@1480861618358452417>
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot luôn phản hồi câu hỏi hợp lệ và không bỏ sót mention.
- **Bắt buộc:** Phải có phản hồi trực tiếp. Trả lời nếu có dữ liệu; nếu thiếu dữ liệu, nêu rõ giới hạn và đưa bước tiếp theo hoặc một câu hỏi làm rõ cụ thể.
- **Không được:** Không im lặng, bỏ qua mention hoặc chỉ chuyển người dùng đi nơi khác mà không có hướng dẫn.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
[Không có câu trả lời trực tiếp trong dữ liệu]
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531843072349048832

---

## Test 18 — KUTE-NR-004

- **Ưu tiên:** P1
- **Loại test:** Coverage / không bỏ sót
- **Chủ đề:** Chưa xác định
- **Lỗi cần kiểm tra:** Chưa trả lời

### Input

```text
<@1480861618358452417> Hi. về các bài codelabs trên lớp tôi làm một bài với nhóm nhưng tôi submit bài cá nhân được ko
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot luôn phản hồi câu hỏi hợp lệ và không bỏ sót mention.
- **Bắt buộc:** Phải có phản hồi trực tiếp. Trả lời nếu có dữ liệu; nếu thiếu dữ liệu, nêu rõ giới hạn và đưa bước tiếp theo hoặc một câu hỏi làm rõ cụ thể.
- **Không được:** Không im lặng, bỏ qua mention hoặc chỉ chuyển người dùng đi nơi khác mà không có hướng dẫn.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
[Không có câu trả lời trực tiếp trong dữ liệu]
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532011236663754914

---

## Test 19 — KUTE-NR-005

- **Ưu tiên:** P1
- **Loại test:** Coverage / không bỏ sót
- **Chủ đề:** Chưa xác định
- **Lỗi cần kiểm tra:** Chưa trả lời

### Input

```text
<@1480861618358452417>  tìm cho mình bài setup jira, mình bị trôi mất tin nhắn đó rồi.
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot luôn phản hồi câu hỏi hợp lệ và không bỏ sót mention.
- **Bắt buộc:** Phải có phản hồi trực tiếp. Trả lời nếu có dữ liệu; nếu thiếu dữ liệu, nêu rõ giới hạn và đưa bước tiếp theo hoặc một câu hỏi làm rõ cụ thể.
- **Không được:** Không im lặng, bỏ qua mention hoặc chỉ chuyển người dùng đi nơi khác mà không có hướng dẫn.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
[Không có câu trả lời trực tiếp trong dữ liệu]
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1532243397740466246

---

## Test 20 — KUTE-REG-031

- **Ưu tiên:** P0
- **Loại test:** Nhận diện intent
- **Chủ đề:** Mentor Duty / coaching
- **Lỗi cần kiểm tra:** Có dấu hiệu trả nhầm intent

### Input

```text
<@1480861618358452417> nộp báo cáo buổi mentor duty ở đâu
```

### Kỳ vọng

- **Mục tiêu:** Kiểm tra bot hiểu đúng mục đích chính của người dùng.
- **Bắt buộc:** Trả lời trực tiếp intent chính ngay đầu; thông tin bổ sung chỉ được đưa sau khi đã giải quyết câu hỏi. Phải phân biệt Mentor Duty với Workshop, Office Hours và Weekly Report.
- **Không được:** Không chuyển sang chủ đề, lệnh hoặc quy trình khác.

<details>
<summary><strong>Câu trả lời sai trước đây</strong></summary>

```text
Bạn nộp daily standup trong thread `Thảo luận` trong channel riêng của team mình nhé (t-xxx)
Cách thức nộp: gõ /daily
```

</details>

### Kết quả chạy test

| Câu trả lời mới | Đúng intent | Đủ ý | Chính xác/hiện hành | Hữu ích/hành động | Tổng | PASS/FAIL |
|---|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |

### Dẫn chứng

- Câu hỏi gốc: https://discord.com/channels/1526532830627102781/1527920243350179960/1531670074627195023
- Câu trả lời cũ: https://discord.com/channels/1526532830627102781/1527920243350179960/1531670086031638739

---
