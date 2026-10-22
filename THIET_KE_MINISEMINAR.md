# Mini seminar: Thực vật Việt Nam qua ống kính cộng đồng (GBIF, 2020–2026)

**Thông điệp chính:** dữ liệu thực vật Việt Nam bùng nổ nhờ cộng đồng ghi nhận, nhưng lệch về đô thị và điểm du lịch. Rừng và vùng núi vẫn là khoảng trống dữ liệu.

Thời lượng đề xuất: 10–12 phút trình bày + 3 phút demo dashboard. Bám đúng 3 mục đề bài: (1) nguyên lý/triết lý xây dựng, (2) kỹ thuật/phương pháp, (3) dashboard.

Mọi con số dưới đây lấy từ notebook EDA ([notebooks/09_eda_preprocess.ipynb](notebooks/09_eda_preprocess.ipynb)), tính trên 17.120 bản ghi sau làm sạch.

---

## 0. Dữ liệu

| Mục | Nội dung |
|---|---|
| Nguồn | GBIF API (`api.gbif.org/v1/occurrence/search`), công khai, không cần key |
| Phạm vi | Thực vật (Plantae) ở Việt Nam, có tọa độ, năm 2020–2026 |
| Thu thập | 7 notebook (mỗi năm một notebook), 18.180 bản, khớp 100% số GBIF báo |
| Sau làm sạch | 17.120 bản ghi (loại 1.060 bản trùng), 2.770 loài, 327 họ, 63 tỉnh |
| File | `vn_plants_clean.csv` (dùng cho dashboard) |
| Giải thích cột | Đầu notebook 09, mục "Giải thích các feature" |

**Giới hạn cần nói thẳng** (nên có 1 slide):
- Đây là thực vật nói chung được cộng đồng ghi nhận, **chưa phải "thực vật rừng"**: top loài là lục bình, cúc áo, trinh nữ, sen.
- Số bản ghi phản ánh nơi có người đi ghi nhận, không phải nơi có nhiều cây.
- 2026 chưa hết năm; tỉnh theo ranh giới GADM cũ (63 tỉnh); 59% bản ghi chưa có mức IUCN.
- Giấy phép: khoảng 60% bản ghi là CC BY-NC (không dùng thương mại), cần ghi nguồn khi công bố lại.

---

## 1. Phần 1: Nguyên lý và triết lý xây dựng

Khung chính là **GQM (Goal–Question–Metric)**: đi từ mục tiêu xuống câu hỏi rồi mới tới chỉ số, nên mỗi biểu đồ truy ngược được về một câu hỏi. Mục tiêu viết theo **SMART**.

### Mục tiêu (SMART)
> Tới ngày 23/10/2026, dùng 17.120 bản ghi thực vật Việt Nam từ GBIF giai đoạn 2020–2026, chỉ ra thực vật được ghi nhận nhiều ở đâu, bởi nguồn nào, thay đổi thế nào theo thời gian, và vùng nào còn thiếu dữ liệu.

(Specific: thực vật Việt Nam, 3 chiều không gian/nguồn/thời gian. Measurable: số bản ghi, tỷ lệ. Achievable: dữ liệu đã thu đủ. Relevant: định hướng khảo sát bảo tồn. Time-bound: 2020–2026, hạn 23/10/2026.)

### Cây GQM

| Goal | Question | Metric (trên dashboard) |
|---|---|---|
| G1 Biết dữ liệu nằm ở đâu, gồm gì | Q1 Thực vật được ghi nhận ở đâu và là loài nào? | Số bản ghi theo tỉnh; top 10 họ và loài; số loài, số họ |
| G2 Hiểu dữ liệu thay đổi ra sao | Q2 Số ghi nhận thay đổi thế nào theo năm, tháng, và từ nguồn nào? | Số bản ghi theo năm, tháng; % quan sát so với tiêu bản; top bộ dữ liệu |
| G3 Đánh giá mức độ bảo tồn | Q3 Loài nguy cấp ở đâu, và bao nhiêu chưa được đánh giá? | % có mức IUCN; số bản ghi CR/EN/VU theo tỉnh và họ |

### Nguyên tắc thiết kế dashboard (một slide)
1. **Overview first, zoom and filter, details on demand** (Shneiderman): trang đầu là tổng quan, lọc bằng slicer, bấm tỉnh để xem chi tiết.
2. **Một biểu đồ, một câu hỏi:** tiêu đề biểu đồ là thông điệp, không phải tên cột.
3. **Data-ink ratio** (Tufte): bỏ lưới, viền, hiệu ứng 3D thừa.
4. **Quy tắc 5 giây:** nhìn vào là thấy ý chính nhờ hàng thẻ KPI.
5. **Màu có nghĩa và nhất quán:** quan sát một màu, tiêu bản một màu, nhóm nguy cấp luôn là đỏ.
6. **Trung thực dữ liệu:** ghi nguồn, khoảng thời gian, và chú thích 2026 là năm dở dang ngay trên dashboard.

---

## 2. Phần 2: Kỹ thuật và phương pháp

### Quy trình ETL (Extract–Transform–Load)

| Bước | Việc làm | Công cụ |
|---|---|---|
| Extract | Gọi GBIF API, chia theo năm, mỗi trang 300 bản, thử lại khi lỗi, đối chiếu số bản với GBIF | Python `requests`, 7 notebook (`01`–`07`) |
| Transform | Gộp và loại trùng `gbifID`; bỏ 3 cột (`elevation` thiếu 84%, `stateProvince`, `recordedBy`); gán tỉnh nước ngoài (26 bản) thành không xác định; loại 1.060 bản trùng; tạo cột `species_level`, `iucn_group`, `coord_imprecise` | pandas, notebook `08`, `09` |
| Load | Lưu `vn_plants_clean.csv`, nạp vào dashboard | CSV, Power BI hoặc Streamlit |

### Quy tắc tiền xử lý đã chọn

| Quy tắc | Lý do |
|---|---|
| Trùng = cùng loài, cùng tọa độ, cùng ngày | Phần lớn là một người đăng nhiều ảnh một cây trong một lần đi |
| Đếm loài chỉ với bản ghi định danh đến loài (97%) | Bản ghi chỉ đến chi hoặc họ vẫn dùng cho thống kê theo họ |
| Gắn cờ tọa độ sai số trên 5 km (1.558 bản), không xóa | Giữ dữ liệu nhưng không dùng cho bản đồ chi tiết |
| Nhóm IUCN: Nguy cấp (CR, EN, VU), Ít quan ngại (LC, NT), Thiếu dữ liệu (DD), Khác (EX, EW, CD), Chưa đánh giá | Gọn biểu đồ; nhóm "Khác" chỉ 8 bản |

### Biểu đồ dùng (đúng loại trong bài giảng)

| Câu hỏi | Biểu đồ |
|---|---|
| Phân bố không gian | Hexbin hoặc bản đồ điểm (thang log) |
| So sánh tỉnh, họ, loài, nguồn | Bar ngang |
| Theo năm, tháng | Bar/line |
| Cơ cấu nguồn theo năm | Stacked bar 100% |
| Tỉnh × năm | Heatmap ma trận |
| Chất lượng tọa độ | Histogram (log) |
| Nhóm IUCN | Bar |

Không dùng ML hay kiểm định phức tạp: đây là bài trực quan hóa và kể chuyện bằng dữ liệu, nên giữ gọn.

---

## 3. Phần 3: Thiết kế dashboard

Công cụ: **Power BI Desktop** (khớp bài giảng, có Python visual, dùng DAX) hoặc **Streamlit + Plotly** (dựng nhanh bằng code). Bố cục dưới đây áp dụng cho cả hai.

### Trang 1. Tổng quan (trả lời Q1, G1)

```
+---------------------------------------------------------------------------+
| Thực vật Việt Nam qua ống kính cộng đồng | GBIF 2020–2026 | [Năm] [Họ]    |
+-----------+-----------+-----------+------------+--------------------------+
| Bản ghi   | Số loài   | Số họ     | Số tỉnh    | % có mức IUCN            |
| 17.120    | 2.770     | 327       | 63         | 41%                      |
+-----------+-----------+-----------+------------+--------------------------+
| BẢN ĐỒ hexbin mật độ bản ghi             | Top 10 họ (bar ngang)          |
| (bấm tỉnh => lọc cả trang)               +--------------------------------+
|                                          | Top 10 loài (bar ngang)        |
+------------------------------------------+--------------------------------+
| Top 12 tỉnh theo số bản ghi (bar ngang)                                   |
+---------------------------------------------------------------------------+
```
Thông điệp tiêu đề gợi ý: "Năm tỉnh thành đầu bảng chiếm khoảng 37% bản ghi" (1.972 + 1.618 + 1.042 + 999 + 772 trên 17.120).

### Trang 2. Thời gian và nguồn (trả lời Q2, G2)

```
+--------------------------------+---------------------------------+
| Bar: số bản ghi theo năm       | Bar: số bản ghi theo tháng      |
| (2026: chú thích năm dở dang)  | (gộp 7 năm)                     |
+--------------------------------+---------------------------------+
| Stacked bar 100%: loại bản ghi | Bar ngang: top 5 bộ dữ liệu     |
| theo năm (quan sát/tiêu bản)   | nguồn                           |
+--------------------------------+---------------------------------+
| Heatmap: top 10 tỉnh x năm (màu = số bản ghi)                    |
+------------------------------------------------------------------+
| Ghi chú: các đợt tăng vọt thường do một dự án ghi nhận tập trung |
+------------------------------------------------------------------+
```
Thông điệp: "Ghi nhận tăng hơn 4 lần, nhưng tiêu bản gần như biến mất từ 2025".

### Trang 3. Bảo tồn (trả lời Q3, G3)

```
+--------------------------------+---------------------------------+
| Bar: cơ cấu nhóm IUCN          | Bar ngang: top tỉnh nguy cấp    |
+--------------------------------+---------------------------------+
| Bản đồ điểm: chỉ bản ghi       | Bar ngang: top họ nguy cấp      |
| nguy cấp (đỏ)                  | (Lauraceae đứng đầu)            |
+--------------------------------+---------------------------------+
| Ghi chú: khoảng 500 bản, 92 loài; một phần có thể là cây trồng    |
+------------------------------------------------------------------+
```
Thông điệp: "Chỉ 3% bản ghi là loài nguy cấp, và hơn một nửa chưa được đánh giá".

### Tương tác (mục 7 của slide)
- Slicer: năm, loại bản ghi (`source_type`), nhóm IUCN, họ.
- Lọc chéo: bấm một tỉnh thì mọi biểu đồ lọc theo.
- Drill-down: họ, chi, rồi loài.
- Tooltip: tên loài, năm, nguồn, tỉnh.

### Mô hình dữ liệu và measure (nếu dùng Power BI)
Một bảng sự kiện `ban_ghi` (từ `vn_plants_clean.csv`); có thể thêm bảng chiều `nam` và `tinh` nếu cần star schema. Measure DAX gợi ý:
```
So_ban_ghi   = COUNTROWS(ban_ghi)
So_loai      = CALCULATE(DISTINCTCOUNT(ban_ghi[species]), ban_ghi[species_level] = TRUE())
Ty_le_IUCN   = DIVIDE(CALCULATE([So_ban_ghi], ban_ghi[is_assessed] = TRUE()), [So_ban_ghi])
So_nguy_cap  = CALCULATE([So_ban_ghi], ban_ghi[iucn_group] = "Nguy cấp")
```

### Cập nhật dữ liệu tự động (mục 6 của slide)
Không làm real-time trong bài này. Trình bày như hướng mở rộng: chạy lại 7 notebook (hoặc chỉ năm hiện tại) theo lịch, đối chiếu số bản với GBIF, ghi log, rồi Refresh dashboard.

### Chọn nền tảng (mục 4 của slide)
Một câu trên slide: Power BI có giao diện gần Excel, mạnh về mô hình hóa và DAX, tích hợp Python; Grafana, Kibana thiên về giám sát thời gian thực và log nên không hợp với dữ liệu tĩnh theo năm này.

---

## 4. Dàn ý thuyết trình (11 slide)

| # | Slide | Nội dung chính |
|---|---|---|
| 1 | Tiêu đề | Câu hỏi: dữ liệu thực vật Việt Nam đang kể điều gì, và bỏ sót điều gì? |
| 2 | Dữ liệu | GBIF, 2020–2026, 17.120 bản, 2.770 loài; giới hạn "chưa phải thực vật rừng" |
| 3 | Mục tiêu SMART | Câu mục tiêu và 5 yếu tố |
| 4 | Cây GQM | Bảng Goal, Question, Metric |
| 5 | Nguyên tắc thiết kế | Sáu nguyên tắc |
| 6 | Quy trình ETL | Thu thập, làm sạch, lưu; các quy tắc tiền xử lý |
| 7 | Dashboard trang 1 (demo) | Tổng quan, phân bố lệch về đô thị |
| 8 | Dashboard trang 2 (demo) | Tăng 4 lần, tiêu bản biến mất |
| 9 | Dashboard trang 3 (demo) | 3% nguy cấp, 59% chưa đánh giá |
| 10 | Kết luận và hạn chế | Số bản ghi phản ánh người ghi nhận; khoảng trống ở rừng |
| 11 | Hướng mở rộng, Hỏi–Đáp | Chuỗi cập nhật tự động; thêm dữ liệu rừng (loài thân gỗ); phân tích theo vùng |

---

## 5. Insight nên nhấn mạnh

| Insight | Số liệu | Lưu ý khi nói |
|---|---|---|
| Ghi nhận bùng nổ | 948 (2020) lên khoảng 4.100 (2024–2025) | 2026 chưa hết năm, không so trực tiếp |
| Cộng đồng chi phối | 87% quan sát, iNaturalist 77% | Dữ liệu phản ánh thói quen người chụp ảnh |
| Tiêu bản gần biến mất từ 2025 | dưới 2% | Nhiều khả năng do số hóa trễ (suy luận) |
| Lệch về đô thị, điểm du lịch | TP.HCM 1.972, Lâm Đồng 1.618, Khánh Hòa 1.042 | Là mật độ người ghi nhận, không phải mật độ cây |
| Top loài là cây ven đường | lục bình, cúc áo, trinh nữ, sen | Không kết luận về rừng |
| Tăng vọt do dự án | Lâm Đồng 16 bản (2021), 515 bản (2022) | Không đọc xu hướng tỉnh quá chặt |
| Ghi nhận theo mùa | Tháng 3–4 cao nhất (khoảng 1.800), tháng 9 thấp nhất (777) | Giả thuyết mùa khô, chưa kiểm chứng |
| Loài nguy cấp ít, thiếu đánh giá | 506 bản (3%), 92 loài; 59% chưa có IUCN | Một phần ở TP.HCM có thể là cây trồng (suy đoán) |

---

## 6. Việc còn lại

1. Chọn công cụ (Power BI hoặc Streamlit) và dựng 3 trang theo wireframe, đọc từ `vn_plants_clean.csv`.
2. Mở notebook 09 bằng Jupyter để xem hình, kiểm tra lại các nhận xét bằng mắt.
3. Soạn slide theo dàn ý mục 4.
4. Chuẩn bị câu trả lời cho các câu hỏi dễ gặp: "vì sao không phải rừng?", "vì sao chỉ 2020–2026?", "số bản ghi nhiều có nghĩa là nhiều cây không?".
