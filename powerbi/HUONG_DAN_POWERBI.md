# Dựng dashboard Power BI (giống dashboard.html)

> **Có sẵn dự án `ThucVat_VN.pbip` (trang 2 đã dựng xong).** Chạy `python make_pbip.py` để sinh lại, rồi mở `powerbi/ThucVat_VN.pbip` bằng Power BI Desktop và bấm **Home > Refresh** để nạp dữ liệu. Dự án gồm bảng `ban_ghi`, 15 measure và trang "2. Thời gian và nguồn" (11 visual). Các bước thủ công bên dưới dùng cho trang 1 và 3 hoặc khi cần dựng lại.

Thời gian dự kiến: 45–60 phút. Các file trong thư mục này:

| File | Dùng để |
|---|---|
| `load_data.m` | Nạp `vn_plants_clean.csv` bằng Power Query (ngôn ngữ M), thêm các cột nhãn tiếng Việt |
| `measures.dax` | Toàn bộ measure (số bản ghi, số loài, tỷ lệ, các dòng tiêu đề thông điệp) |
| `theme_thucvat.json` | Bảng màu giống dashboard.html |
| `vn_provinces.topojson` | Ranh giới 63 tỉnh cho visual Shape map (`name` trùng cột `province`) |

> Chưa kiểm chứng: tôi chưa mở các file này trong Power BI Desktop. Nếu một bước báo lỗi, xem mục "Nếu gặp lỗi" ở cuối.

## 1. Nạp dữ liệu
1. Mở Power BI Desktop, chọn **Get data > Blank query**, rồi **Advanced Editor**.
2. Dán toàn bộ `load_data.m`. Sửa `DuongDan` cho đúng vị trí file `vn_plants_clean.csv` trên máy bạn.
3. Đổi tên truy vấn thành `ban_ghi`, bấm **Close & Apply**.
4. Kiểm tra: bảng có 17.120 dòng; cột `province` có chỗ trống (đúng, 8% bản ghi không rõ tỉnh).

## 2. Thiết lập mô hình
Chọn cột trong khung Data, vào thẻ **Column tools**:
- `loai_ban_ghi`: **Sort by column** chọn `loai_ban_ghi_thu_tu`.
- `iucn_group`: **Sort by column** chọn `iucn_thu_tu`.
- `thang_nhan`: **Sort by column** chọn `month`.
- `year`, `month`, `day`: **Summarization** chọn **Don't summarize**.
- `decimalLatitude`: **Data category** chọn **Latitude**; `decimalLongitude`: **Longitude**.
- `province`: **Data category** chọn **State or Province**.

## 3. Measure và theme
1. Mở **DAX query view** (biểu tượng DAX thanh trái), dán `measures.dax`, bấm **Update model: Add all measures** (xuất hiện phía trên mỗi khối). Nếu không thấy nút, tạo từng measure bằng chuột phải bảng `ban_ghi` > **New measure**.
2. **View > Themes > Browse for themes**, chọn `theme_thucvat.json`.
3. Đặt màu cố định theo ý nghĩa (giống dashboard.html): Quan sát màu xanh, Tiêu bản màu cam, Khác màu xám, Nguy cấp màu đỏ.

## 4. Bố cục chung cho cả 3 trang
- Thêm 3 trang, đặt tên: `1. Tổng quan`, `2. Thời gian và nguồn`, `3. Bảo tồn`.
- Hàng trên cùng mỗi trang là **slicer** (bộ lọc):
  - **Năm**: Slicer, field `nam_nhan`, kiểu Tile (Format > Slicer settings > Style = Tile), chọn nhiều (Multi-select).
  - **Loại bản ghi**: field `loai_ban_ghi`, kiểu Tile.
  - **Mức IUCN**: field `iucn_group`, kiểu Tile.
  - **Họ**: field `family`, kiểu Dropdown.
- **View > Sync slicers**: bật đồng bộ cả 4 slicer trên cả 3 trang.
- Dòng tiêu đề thông điệp: visual **Card**, field là measure `Tieu_de_trang1` (trang 1), `Tieu_de_trang2` (trang 2), `Tieu_de_trang3` (trang 3). Phóng cỡ chữ 16–18, tắt tên field (Category label = Off).
- Cuối mỗi trang: ô văn bản (Text box) ghi nguồn: "Nguồn: GBIF, thực vật Việt Nam, thu ngày 22/10/2026. Mỗi dòng là một lần ghi nhận, không phải một cây. 2026* chưa hết năm."

## 5. Trang 1: Tổng quan
| Visual | Cách dựng |
|---|---|
| 5 thẻ KPI | 5 visual **Card**: `So_ban_ghi`, `So_loai`, `So_ho`, `So_tinh`, `Ty_le_IUCN` (đổi tên hiển thị: Bản ghi, Loài, Họ, Tỉnh có dữ liệu, Có mức IUCN) |
| Bản đồ theo tỉnh | **Shape map**: Location = `province`, Color saturation = `So_ban_ghi`. Format > Map settings > **Add map** > chọn `vn_provinces.topojson`. Format > Colors: min `#cde2fb`, max `#0d366b`. Nếu thiếu visual, bật Shape map trong File > Options > Preview features rồi khởi động lại. |
| Top 10 họ | **Clustered bar chart**: Y = `family`, X = `So_ban_ghi`. Filter pane > visual-level > `family` > **Top N** = 10 theo `So_ban_ghi`. Sắp xếp giảm dần. |
| Top 10 loài | **Clustered bar chart**: Y = `species`, X = `So_ban_ghi`. Filter: `species_level` là True, `species` Top N = 10. |
| Top 12 tỉnh | **Clustered bar chart**: Y = `province`, X = `So_ban_ghi`. Filter: `province` Top N = 12. |

Bấm một tỉnh trên bản đồ hoặc một thanh sẽ lọc các visual còn lại (cross-filter mặc định của Power BI).

## 6. Trang 2: Thời gian và nguồn
| Visual | Cách dựng |
|---|---|
| Bản ghi theo năm | **Clustered column chart**: X = `nam_nhan`, Y = `So_ban_ghi`, bật Data labels. |
| Bản ghi theo tháng | **Clustered column chart**: X = `thang_nhan`, Y = `So_ban_ghi`, bật Data labels. |
| Cơ cấu loại bản ghi theo năm | **100% stacked column chart**: X = `nam_nhan`, Y = `So_ban_ghi`, Legend = `loai_ban_ghi`. |
| Top 5 bộ dữ liệu nguồn | **Clustered bar chart**: Y = `datasetName`, X = `So_ban_ghi`, filter Top N = 5 (có chỗ trống ứng với "không rõ nguồn"). |
| Heatmap tỉnh × năm | **Matrix**: Rows = `province`, Columns = `nam_nhan`, Values = `So_ban_ghi`. Filter `province` Top N = 10. Format > Cell elements > Background color > **Gradient**, thấp `#cde2fb`, cao `#0d366b`. |

## 7. Trang 3: Bảo tồn
| Visual | Cách dựng |
|---|---|
| Nhóm IUCN | **Clustered bar chart**: Y = `iucn_group`, X = `So_ban_ghi`. Đặt màu từng thanh: Nguy cấp đỏ (`#d03b3b`), còn lại xám. |
| Top tỉnh nguy cấp | **Clustered bar chart**: Y = `province`, X = `So_nguy_cap`, filter Top N = 8, màu đỏ. |
| Top họ nguy cấp | **Clustered bar chart**: Y = `family`, X = `So_nguy_cap`, filter Top N = 8, màu đỏ. |
| Vị trí bản ghi nguy cấp | **Map** (bong bóng): Latitude = `decimalLatitude`, Longitude = `decimalLongitude`, Legend = `coord_imprecise`. Filter visual-level: `is_threatened` là True. Power BI không vẽ được chấm rỗng, nên dùng hai màu: `coord_imprecise` False (đỏ đậm), True (đỏ nhạt). Ghi chú: sai số trên 5 km thường do làm mờ vị trí loài nguy cấp. |

## 8. Hoàn thiện
- **Edit interactions** (Format > Edit interactions): để các biểu đồ lọc lẫn nhau, riêng biểu đồ "theo năm" nên để slicer lọc dạng Highlight nếu bạn muốn thấy cả các năm không được chọn.
- Căn lưới, đồng bộ cỡ chữ, bật tiêu đề cho từng visual theo thông điệp.
- Lưu `.pbix`. Trình chiếu: View > **Full screen**, hoặc File > Export > PDF.

## Nếu gặp lỗi
- **Lỗi kiểu dữ liệu ở bước nạp (cột month/day):** bước `TransformColumnTypes` có thể kêu lỗi vì giá trị dạng `1.0`. Thay `Int64.Type` bằng `type number` cho `month` và `day`, rồi thêm một bước đổi sang Whole number trong giao diện.
- **Shape map trống hoặc chỉ hiện nền:** TopoJSON có thể chưa tương thích. Dùng thay thế: **Filled map** (Bing), Location = `province`, bật Data category = State or Province; hoặc dùng visual **Map** với `decimalLatitude`/`decimalLongitude` tô theo `So_ban_ghi`. Hai cách này cần có mạng.
- **Measure `Tieu_de_trang2` báo lỗi hoặc ra chuỗi lạ:** thay bằng ô văn bản tĩnh (Text box) với dòng "Ghi nhận tăng gấp 4,4 lần (2020 đến 2024), nhưng tiêu bản chỉ còn 1% năm 2025". Đây là số chạy trên toàn bộ dữ liệu.
- **Số liệu kiểm tra:** khi không lọc gì, 5 thẻ KPI phải là 17.120 bản ghi, 2.770 loài, 327 họ, 63 tỉnh, 41% có IUCN. Nếu khác, kiểm tra lại bước nạp dữ liệu.
