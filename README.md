# Thực vật Việt Nam qua ống kính cộng đồng (GBIF, 2020–2026)

Mini seminar môn DS111: phân tích dữ liệu thực vật Việt Nam từ GBIF và thiết kế dashboard.

**Thông điệp chính:** dữ liệu thực vật Việt Nam tăng nhanh nhờ cộng đồng ghi nhận, nhưng lệch về đô thị và điểm du lịch. Rừng và vùng núi vẫn là khoảng trống dữ liệu.

> Lưu ý: đây là thực vật nói chung được cộng đồng ghi nhận, **chưa phải "thực vật rừng"**. Top loài là lục bình, cúc áo, trinh nữ, sen.

## Dữ liệu

| Mục | Nội dung |
|---|---|
| Nguồn | [GBIF](https://www.gbif.org) (Global Biodiversity Information Facility), API `https://api.gbif.org/v1/occurrence/search` |
| Phạm vi | Thực vật (Plantae) ở Việt Nam, có tọa độ, không lỗi vị trí, năm 2020–2026 |
| Quy mô | 18.180 bản ghi thu được, còn 17.120 sau khi loại trùng; 2.770 loài, 327 họ, 63 tỉnh |
| Ngày thu thập | 22/10/2026 (năm 2026 chưa hết năm) |

Mỗi dòng là một lần ghi nhận một cây: hoặc quan sát cộng đồng (chủ yếu iNaturalist, 87%), hoặc tiêu bản bảo tàng (12%). GBIF chỉ gom dữ liệu từ các nơi cung cấp, không tự thu mẫu. Giải thích chi tiết từng cột nằm ở đầu notebook `09_eda_preprocess.ipynb`.

**Giấy phép:** dữ liệu giữ giấy phép của từng nơi cung cấp, ghi trong cột `license` (khoảng 60% là CC BY-NC 4.0, không dùng cho mục đích thương mại; phần còn lại CC BY 4.0 và CC0). Khi dùng lại cần ghi nguồn GBIF và các bộ dữ liệu gốc (cột `datasetName`).

## Cấu trúc thư mục

```
.
├── notebooks/
│   ├── 01_scrape_2020.ipynb ... 07_scrape_2026.ipynb   # mỗi năm một notebook, thu dữ liệu từ GBIF
│   ├── 08_merge_clean.ipynb                            # gộp 7 năm, tạo cột phụ
│   └── 09_eda_preprocess.ipynb                         # tiền xử lý và EDA
├── data/                                # file CSV theo năm (kết quả của notebook 01–07)
├── vn_plants_gbif_2020_2026.csv         # dữ liệu gộp (kết quả của notebook 08)
├── vn_plants_clean.csv                  # dữ liệu sạch dùng cho dashboard (kết quả của notebook 09)
├── dashboard.html                       # dashboard 3 trang, một file độc lập (dữ liệu nhúng sẵn)
├── dashboard_template.html              # mẫu giao diện dashboard
├── build_dashboard.py                   # sinh dashboard.html từ vn_plants_clean.csv
├── assets/vn_provinces.json             # ranh giới 63 tỉnh (GADM 4.1, đã đơn giản hóa) cho bản đồ
├── make_notebooks.py                    # sinh notebook 01–08
├── make_eda_notebook.py                 # sinh notebook 09
└── THIET_KE_MINISEMINAR.md              # thiết kế mini seminar: nguyên lý, kỹ thuật, dashboard, dàn ý
```

## Cách chạy lại

Yêu cầu: Python 3.10 trở lên.

```bash
pip install requests pandas matplotlib seaborn jupyter
```

1. Chạy `notebooks/01_scrape_2020.ipynb` đến `07_scrape_2026.ipynb` (mỗi notebook vài giây đến vài chục giây). File CSV lưu vào `data/`. Trên Kaggle, bật Internet trong Settings, file lưu ở `/kaggle/working`.
2. Chạy `08_merge_clean.ipynb` để gộp thành `vn_plants_gbif_2020_2026.csv`.
3. Chạy `09_eda_preprocess.ipynb` để tiền xử lý, EDA và tạo `vn_plants_clean.csv`.

Số liệu GBIF thay đổi theo thời gian, nên chạy lại có thể cho số bản ghi khác một chút.

Muốn đổi khoảng năm hoặc cột thu thập: sửa `make_notebooks.py` rồi chạy `python make_notebooks.py`.

Sinh lại dashboard sau khi có `vn_plants_clean.csv`: `python build_dashboard.py` (cần `pandas`, `requests`; lần đầu tải ranh giới tỉnh từ GADM). Mở `dashboard.html` bằng trình duyệt để xem.

## Quy trình xử lý

- **Thu thập:** gọi API theo từng năm, mỗi trang 300 bản, thử lại khi lỗi; so số bản thu được với số GBIF báo (cả 7 năm khớp 100%).
- **Làm sạch:** bỏ 3 cột (`elevation` thiếu 84%, `stateProvince`, `recordedBy`); đặt tỉnh nước ngoài (26 bản) thành không xác định; loại 1.060 bản trùng (cùng loài, tọa độ, ngày); gắn cờ tọa độ sai số trên 5 km (không xóa).
- **Cột tạo thêm:** `species_level`, `iucn_group`, `coord_imprecise`, `is_assessed`, `is_threatened`, `source_type`, `year_month`, `province`.

## Phát hiện chính

- Số bản ghi tăng từ 948 (2020) lên khoảng 4.100 (2024–2025), gấp hơn 4 lần. Năm 2026 chưa hết năm.
- 87% là quan sát thực địa, iNaturalist chiếm 77%. Từ 2025 tiêu bản gần như biến mất (dưới 2%), nhiều khả năng do số hóa trễ (chưa kiểm chứng).
- Bản ghi dồn vào TP.HCM (1.972), Lâm Đồng (1.618), Khánh Hòa (1.042). Đây là mật độ người ghi nhận, không phải mật độ cây.
- Loài nguy cấp (CR, EN, VU) chỉ 506 bản (3%), thuộc 92 loài; 59% bản ghi chưa có mức IUCN.
- Tọa độ loài nguy cấp có sai số lớn hơn hẳn (28,5% trên 5 km so với 8,5% ở các bản còn lại), có thể do nơi cung cấp cố ý làm mờ vị trí.

## Hạn chế

- Dữ liệu là quan sát cộng đồng, thiên lệch về nơi có người đi ghi nhận; không phải khảo sát có hệ thống.
- Tỉnh theo ranh giới GADM cũ (63 tỉnh).
- Một số nhận xét trong notebook là giả thuyết, đã ghi rõ trong từng chỗ.

## Trạng thái

- [x] Thu thập và gộp dữ liệu
- [x] Tiền xử lý và EDA
- [x] Thiết kế mini seminar (xem `THIET_KE_MINISEMINAR.md`)
- [x] Dashboard HTML 3 trang (`dashboard.html`, mở trực tiếp bằng trình duyệt, không cần cài gì)
