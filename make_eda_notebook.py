"""Sinh notebook tien xu ly + EDA: notebooks/09_eda_preprocess.ipynb

Chay:  python make_eda_notebook.py
"""
from make_notebooks import code, md, notebook, write

CELLS = [
    md("""
# Tiền xử lý và EDA: thực vật Việt Nam, GBIF 2020–2026

**Mục tiêu:** làm sạch dữ liệu đã gộp, rồi khám phá để chốt nội dung dashboard.
Mỗi mục có ô code ngắn và một nhận xét ngay bên dưới.

1. Đọc và xem tổng quan
2. Tiền xử lý
3. Khám phá (EDA): thời gian, nguồn, phân loại, không gian, bảo tồn, chất lượng tọa độ
4. Tổng kết và gợi ý cho dashboard
"""),
    md("""
## Giải thích các feature

**Dữ liệu:** mỗi dòng là một lần ghi nhận một cây thực vật ở Việt Nam (một mẫu thu hoặc một quan sát), lấy từ GBIF API, năm 2020–2026.

### A. Cột lấy trực tiếp từ GBIF

| Nhóm | Cột | Ý nghĩa | Ví dụ / giá trị |
|---|---|---|---|
| Định danh | `gbifID` | Mã duy nhất của bản ghi trên GBIF, dùng để loại trùng | 2557736268 |
| Phân loại | `scientificName` | Tên khoa học đầy đủ, kèm tác giả đặt tên | *Cocos nucifera* L. |
| | `species`, `genus`, `family`, `order`, `class`, `phylum` | Các bậc phân loại: loài, chi, họ, bộ, lớp, ngành (từ nhỏ đến lớn) | *Cocos nucifera*, *Cocos*, Arecaceae (họ cau) |
| | `taxonRank` | Bậc thấp nhất mà bản ghi được định danh đến | SPECIES, GENUS, FAMILY... Nếu là GENUS thì `species` để trống |
| Bảo tồn | `iucnRedListCategory` | Mức đánh giá trong Sách đỏ IUCN. Để trống nếu loài chưa được đánh giá | CR, EN, VU, NT, LC, DD, EX, EW, CD (xem bảng B) |
| Nguồn | `basisOfRecord` | Cách có được bản ghi | HUMAN_OBSERVATION (quan sát, ví dụ ảnh iNaturalist), PRESERVED_SPECIMEN (tiêu bản trong bảo tàng), MATERIAL_SAMPLE, MATERIAL_CITATION, LIVING_SPECIMEN (mẫu sống) |
| | `datasetName` | Bộ dữ liệu cung cấp bản ghi | iNaturalist research-grade observations, Moscow Digital Herbarium, Tropicos |
| | `institutionCode` | Mã tổ chức lưu giữ hoặc đóng góp | iNaturalist, KAG, Moscow State University |
| | `license` | Giấy phép sử dụng dữ liệu, lưu dưới dạng đường dẫn | CC BY-NC 4.0 (khoảng 60%), CC BY 4.0, CC0. Bản CC BY-NC không dùng cho mục đích thương mại |
| Thời gian | `year`, `month`, `day` | Ngày ghi nhận | 2024, 3, 17 |
| Không gian | `decimalLatitude`, `decimalLongitude` | Vĩ độ, kinh độ (độ thập phân) | 10.78, 106.70 |
| | `coordinateUncertaintyInMeters` | Sai số của tọa độ, tính bằng mét. Càng nhỏ càng chính xác; để trống nếu không rõ | 6 (rất chính xác), 3.000.000 (nhiều khả năng sai) |
| | `province_gadm` | Tỉnh chứa điểm đó, suy ra từ tọa độ theo ranh giới GADM (63 tỉnh) | Lâm Đồng |
| | `stateProvince` | Tỉnh do người nhập tự ghi, thiếu và không thống nhất | Hồ Chí Minh city |
| | `elevation` | Độ cao (m) | Thiếu 84% |
| | `recordedBy` | Người thu mẫu | Tên cá nhân |

### B. Mức IUCN

| Mã | Ý nghĩa | Nhóm trong notebook |
|---|---|---|
| CR | Cực kỳ nguy cấp | Nguy cấp |
| EN | Nguy cấp | Nguy cấp |
| VU | Sắp nguy cấp (dễ bị tổn thương) | Nguy cấp |
| NT | Gần bị đe dọa | Ít quan ngại |
| LC | Ít quan ngại | Ít quan ngại |
| DD | Thiếu dữ liệu để đánh giá | Thiếu dữ liệu |
| EX, EW, CD | Tuyệt chủng, tuyệt chủng ngoài tự nhiên, phụ thuộc bảo tồn | Khác |
| (để trống) | Chưa được IUCN đánh giá | Chưa đánh giá |

### C. Cột tự tạo

| Cột | Tạo ở đâu | Cách tính | Dùng để |
|---|---|---|---|
| `is_assessed` | Notebook gộp | `True` nếu có mức IUCN | Tỷ lệ loài đã được đánh giá |
| `is_threatened` | Notebook gộp | `True` nếu IUCN là CR, EN hoặc VU | Đếm bản ghi nguy cấp |
| `source_type` | Notebook gộp | Gộp `basisOfRecord`: "Quan sat" (quan sát), "Tieu ban" (tiêu bản), "Mau song", "Khac" (MATERIAL_SAMPLE, MATERIAL_CITATION) | So sánh tiêu bản với quan sát |
| `year_month` | Notebook gộp | Ngày đầu tháng của (`year`, `month`) | Vẽ theo tháng |
| `province` | Mục 2.2 | Bằng `province_gadm`, nhưng đặt trống nếu điểm bị gán sang tỉnh nước ngoài | Phân tích theo tỉnh (thay `province_gadm`) |
| `species_level` | Mục 2.4 | `True` nếu định danh đến loài (SPECIES, SUBSPECIES, VARIETY, FORM) và có `species` | Đếm số loài |
| `iucn_group` | Mục 2.5 | Gộp mức IUCN thành 5 nhóm theo bảng B | Biểu đồ bảo tồn |
| `coord_imprecise` | Mục 2.5 | `True` nếu sai số tọa độ lớn hơn 5.000 m | Loại điểm kém chính xác khỏi bản đồ |

**Cột bị bỏ ở mục 2.1:** `elevation`, `stateProvince`, `recordedBy`. `province_gadm` được thay bằng `province` ở mục 2.2.
"""),
    code("""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (8, 4)

PATH = next(p for p in [Path("vn_plants_gbif_2020_2026.csv"),
                        Path("../vn_plants_gbif_2020_2026.csv")] if p.exists())
df = pd.read_csv(PATH, low_memory=False)
print(df.shape)
df.head(3)
"""),

    md("## 1. Tổng quan"),
    code("""
# Tỷ lệ thiếu theo cột (chỉ in cột có thiếu)
missing = df.isna().mean().round(2).sort_values(ascending=False)
missing[missing > 0]
"""),
    md("""
**Nhận xét**
- `elevation` thiếu 84%, không dùng được. `stateProvince` thiếu 19% và trùng ý với tỉnh từ GADM.
- `iucnRedListCategory` thiếu 61%: phần lớn loài chưa được IUCN đánh giá, đây là thực tế của dữ liệu chứ không phải lỗi thu thập.
- `province_gadm` chỉ thiếu 7%, đủ để phân tích theo tỉnh.
- `coordinateUncertaintyInMeters` thiếu 34%, cần cẩn thận khi dùng làm tiêu chí lọc.
"""),

    md("## 2. Tiền xử lý"),
    md("### 2.1 Bỏ cột không dùng"),
    code("""
# elevation: thiếu quá nhiều; stateProvince: trùng province_gadm; recordedBy: tên cá nhân, không cần
df = df.drop(columns=["elevation", "stateProvince", "recordedBy"])
df.shape
"""),

    md("### 2.2 Làm sạch tên tỉnh"),
    code("""
# GADM gán một số điểm sát biên giới vào tỉnh của nước láng giềng -> coi như không xác định
FOREIGN = {"Guangxi", "Yunnan", "Kep", "Môndól Kiri", "Phôngsali"}
print("Bản ghi gán sang tỉnh nước ngoài:", df["province_gadm"].isin(FOREIGN).sum())

df["province"] = df["province_gadm"].where(~df["province_gadm"].isin(FOREIGN))
df = df.drop(columns="province_gadm")
print("Số tỉnh còn lại:", df["province"].nunique(), "| thiếu tỉnh:", df["province"].isna().mean().round(3))
"""),
    md("""
**Nhận xét:** chỉ 26 bản ghi bị gán sang Quảng Tây, Vân Nam, Kep, Môndól Kiri, Phôngsali (điểm sát biên giới hoặc ngoài khơi). Sau khi loại, còn 63 tỉnh thành và 8% bản ghi không rõ tỉnh.
"""),

    md("### 2.3 Loại bản ghi trùng"),
    code("""
# Cùng loài, cùng tọa độ, cùng ngày -> coi là một lần ghi nhận
key = ["species", "decimalLatitude", "decimalLongitude", "year", "month", "day"]
before = len(df)
df = df.drop_duplicates(key).reset_index(drop=True)
print(f"Loại {before - len(df)} bản ghi trùng: {before} -> {len(df)}")
"""),
    md("""
**Nhận xét:** khoảng 1.060 bản (6%) trùng. Phần lớn là một người đăng nhiều ảnh cùng một cây trong cùng một lần đi, nên giữ một bản là hợp lý.
"""),

    md("### 2.4 Mức phân loại: chỉ phân tích loài khi bản ghi định danh đến loài"),
    code("""
RANKS_SPECIES = ["SPECIES", "SUBSPECIES", "VARIETY", "FORM"]
df["species_level"] = df["taxonRank"].isin(RANKS_SPECIES) & df["species"].notna()
print("Định danh đến loài:", df["species_level"].mean().round(3))
df.loc[~df["species_level"], "taxonRank"].value_counts()
"""),
    md("""
**Nhận xét:** 97% bản ghi định danh đến loài. Phần còn lại chỉ đến chi hoặc họ nên vẫn dùng được cho thống kê theo họ, nhưng bị loại khi đếm số loài.
"""),

    md("### 2.5 Nhóm IUCN và cờ chất lượng tọa độ"),
    code("""
IUCN_GROUP = {"CR": "Nguy cấp", "EN": "Nguy cấp", "VU": "Nguy cấp",
              "LC": "Ít quan ngại", "NT": "Ít quan ngại",
              "DD": "Thiếu dữ liệu",
              "EX": "Khác", "EW": "Khác", "CD": "Khác"}
df["iucn_group"] = df["iucnRedListCategory"].map(IUCN_GROUP).fillna("Chưa đánh giá")

# Tọa độ lệch trên 5 km: giữ lại nhưng gắn cờ, không dùng để vẽ bản đồ chi tiết
df["coord_imprecise"] = df["coordinateUncertaintyInMeters"] > 5000

print(df["iucn_group"].value_counts().to_string())
print("\\nTọa độ kém chính xác (>5 km):", df["coord_imprecise"].sum())
"""),
    md("""
**Nhận xét:** nhóm "Nguy cấp" (CR, EN, VU) có khoảng 500 bản ghi (3%), đủ cho một trang nhỏ trên dashboard. Nhóm "Khác" chỉ 8 bản (EX, EW, CD), gộp lại để khỏi rối biểu đồ. Khoảng 1.560 bản có tọa độ lệch trên 5 km nên không dùng cho bản đồ chi tiết.
"""),

    md("### 2.6 Lưu dữ liệu sạch"),
    code("""
df.to_csv(PATH.with_name("vn_plants_clean.csv"), index=False, encoding="utf-8-sig")
print("Đã lưu", PATH.with_name("vn_plants_clean.csv").name, df.shape)
"""),

    md("## 3. Khám phá (EDA)"),
    md("### 3.1 Theo thời gian"),
    code("""
fig, ax = plt.subplots(1, 2, figsize=(11, 4))

df["year"].value_counts().sort_index().plot(kind="bar", ax=ax[0], color="seagreen")
ax[0].set(title="Số bản ghi theo năm (2026 chưa hết năm)", xlabel="", ylabel="Số bản ghi")

df["month"].value_counts().sort_index().plot(kind="bar", ax=ax[1], color="steelblue")
ax[1].set(title="Số bản ghi theo tháng (gộp 7 năm)", xlabel="Tháng", ylabel="")
plt.tight_layout()
"""),
    md("""
**Nhận xét**
- Số bản ghi tăng mạnh: 948 (2020) lên khoảng 4.100 (2024–2025), tức gấp hơn 4 lần. Năm 2026 mới có 2.340 bản vì chưa hết năm, không được so trực tiếp với các năm trước.
- Theo tháng, cao nhất ở tháng 3–4 (khoảng 1.800 bản), thấp nhất ở tháng 9 (777 bản). Có thể do mùa khô thuận lợi cho đi thực địa, nhưng đây mới là giả thuyết, chưa kiểm chứng.
"""),

    md("### 3.2 Theo nguồn dữ liệu"),
    code("""
fig, ax = plt.subplots(1, 2, figsize=(12, 4))

(pd.crosstab(df["year"], df["source_type"], normalize="index") * 100).plot(
    kind="bar", stacked=True, ax=ax[0], colormap="viridis")
ax[0].set(title="Cơ cấu loại bản ghi theo năm (%)", xlabel="", ylabel="%")
ax[0].legend(title="", loc="lower left")

top_ds = df["datasetName"].fillna("Không rõ").value_counts().head(5)
top_ds.sort_values().plot(kind="barh", ax=ax[1], color="darkorange")
ax[1].set(title="Top 5 bộ dữ liệu nguồn", xlabel="Số bản ghi", ylabel="")
plt.tight_layout()
"""),
    md("""
**Nhận xét**
- Khoảng 87% là quan sát thực địa và 12% là tiêu bản. Riêng iNaturalist đóng góp khoảng 77% (13.186 bản), nên dữ liệu phản ánh thói quen của người chụp ảnh cộng đồng nhiều hơn là một cuộc khảo sát bài bản.
- Từ 2025, tiêu bản gần như biến mất (dưới 2%). Nhiều khả năng do tiêu bản thường được số hóa và đưa lên GBIF trễ nhiều năm, nên số liệu năm gần đây thiếu tiêu bản.
"""),

    md("### 3.3 Theo phân loại"),
    code("""
sp = df[df["species_level"]]
print("Số loài:", sp["species"].nunique(), "| số họ:", df["family"].nunique())

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
df["family"].value_counts().head(10).sort_values().plot(kind="barh", ax=ax[0], color="seagreen")
ax[0].set(title="Top 10 họ theo số bản ghi", xlabel="Số bản ghi", ylabel="")
sp["species"].value_counts().head(10).sort_values().plot(kind="barh", ax=ax[1], color="olive")
ax[1].set(title="Top 10 loài theo số bản ghi", xlabel="Số bản ghi", ylabel="")
plt.tight_layout()
"""),
    md("""
**Nhận xét**
- Có khoảng 2.770 loài thuộc 327 họ. Họ nhiều nhất là Asteraceae (cúc) và Fabaceae (đậu).
- Top loài gồm lục bình (*Pontederia crassipes*), cúc áo (*Bidens alba*), trinh nữ (*Mimosa pudica*), sen (*Nelumbo nucifera*): toàn cây phổ biến ở ven đường, ao hồ, đô thị. Cây rừng đặc hữu hầu như không lọt top.
- Vì vậy bộ dữ liệu này nói về "thực vật nói chung được người dân ghi nhận", chưa phải "thực vật rừng". Nên nêu rõ điều này khi báo cáo.
"""),

    md("### 3.4 Theo không gian"),
    code("""
fig, ax = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1, 1.2]})

geo = df[~df["coord_imprecise"]]
hb = ax[0].hexbin(geo["decimalLongitude"], geo["decimalLatitude"], gridsize=35, bins="log", cmap="YlGn")
ax[0].set(title="Mật độ bản ghi (thang log)", xlabel="Kinh độ", ylabel="Vĩ độ")
fig.colorbar(hb, ax=ax[0], label="log10(số bản ghi)")

df["province"].value_counts().head(12).sort_values().plot(kind="barh", ax=ax[1], color="teal")
ax[1].set(title="Top 12 tỉnh theo số bản ghi", xlabel="Số bản ghi", ylabel="")
plt.tight_layout()
"""),
    md("""
**Nhận xét**
- Bản ghi dồn vào vài điểm: TP.HCM (khoảng 1.970), Lâm Đồng (1.620), Khánh Hòa (1.040), Đồng Nai (1.000), Hà Nội (770). Các tỉnh miền núi phía Bắc và Tây Nguyên (trừ Lâm Đồng) rất thưa.
- Đây là mật độ **người đi ghi nhận**, không phải mật độ cây: thành phố lớn, điểm du lịch (Đà Lạt, Nha Trang) có nhiều người chụp ảnh hơn.
"""),

    md("### 3.5 Tỉnh theo năm"),
    code("""
top_prov = df["province"].value_counts().head(10).index
heat = pd.crosstab(df["province"], df["year"]).loc[top_prov]

plt.figure(figsize=(8, 5))
sns.heatmap(heat, annot=True, fmt="d", cmap="Blues", cbar_kws={"label": "Số bản ghi"})
plt.title("Số bản ghi: top 10 tỉnh theo năm")
plt.xlabel("")
plt.ylabel("")
"""),
    md("""
**Nhận xét:** nhiều ô biến động mạnh giữa các năm, ví dụ Lâm Đồng 515 bản năm 2022 nhưng chỉ 16 bản năm 2021. Điều này gợi ý mỗi đợt tăng vọt thường do một dự án hoặc một nhóm người ghi nhận tập trung, không phải xu hướng tự nhiên. Khi vẽ xu hướng theo tỉnh cần ghi chú điều này.
"""),

    md("### 3.6 Mức độ bảo tồn (IUCN)"),
    code("""
order = ["Chưa đánh giá", "Ít quan ngại", "Nguy cấp", "Thiếu dữ liệu", "Khác"]
threat = df[df["iucn_group"] == "Nguy cấp"]

fig, ax = plt.subplots(1, 3, figsize=(14, 4))
df["iucn_group"].value_counts().reindex(order).plot(kind="bar", ax=ax[0], color="gray")
ax[0].set(title="Nhóm IUCN", xlabel="", ylabel="Số bản ghi")
ax[0].tick_params(axis="x", rotation=30)

threat["province"].value_counts().head(8).sort_values().plot(kind="barh", ax=ax[1], color="firebrick")
ax[1].set(title="Loài nguy cấp: top tỉnh", xlabel="Số bản ghi", ylabel="")

threat["family"].value_counts().head(8).sort_values().plot(kind="barh", ax=ax[2], color="indianred")
ax[2].set(title="Loài nguy cấp: top họ", xlabel="Số bản ghi", ylabel="")
plt.tight_layout()
print("Số loài nguy cấp:", threat["species"].nunique())
"""),
    md("""
**Nhận xét**
- 59% bản ghi chưa có mức IUCN. Trong số đã đánh giá, đa số là "ít quan ngại". Các bản nguy cấp thuộc 92 loài khác nhau.
- Bản ghi nguy cấp (506 bản, 3%) tập trung ở Lâm Đồng (54), Đắk Nông (36), Nghệ An (32) và TP.HCM (32). Họ nhiều nhất là Lauraceae (long não, 116 bản).
- Họ Cycadaceae (tuế) và Cupressaceae (hoàng đàn) cũng xuất hiện nhiều, và TP.HCM có 32 bản nguy cấp nên một phần có thể là cây trồng ở công viên, vườn. Đây là suy đoán, cần kiểm tra thêm trước khi kết luận.
"""),

    md("### 3.7 Chất lượng tọa độ"),
    code("""
import numpy as np

unc = df["coordinateUncertaintyInMeters"].dropna()
print(unc.describe().round(1).to_string())

plt.figure(figsize=(7, 3.5))
plt.hist(np.log10(unc), bins=30, color="slategray")
plt.axvline(np.log10(5000), color="red", linestyle="--", label="Ngưỡng 5 km")
plt.title("Phân bố độ không chắc chắn của tọa độ (log10, mét)")
plt.xlabel("log10(mét)")
plt.ylabel("Số bản ghi")
plt.legend()
"""),
    md("""
**Nhận xét:** đa số tọa độ rất chính xác (trung vị khoảng 24 m) nhưng có đuôi dài, tối đa hơn 3.000 km (nhiều khả năng là lỗi nhập). Ngưỡng 5 km đủ để chỉ loại phần đuôi này mà vẫn giữ phần lớn dữ liệu.
"""),

    md("""
## 4. Tổng kết

| Phát hiện | Hệ quả cho dashboard |
|---|---|
| Số bản ghi tăng mạnh từ 2020, 2026 chưa hết năm | Biểu đồ theo năm phải chú thích 2026 là năm dở dang |
| 87% là quan sát, 77% từ iNaturalist | Nêu rõ nguồn; số bản ghi phản ánh người ghi nhận, không phải số cây |
| Từ 2025 gần như không còn tiêu bản | Giải thích do số hóa trễ, không so sánh trực tiếp |
| Top loài là cây phổ biến đô thị và ven nước | Không kết luận về "rừng"; gọi là "thực vật được cộng đồng ghi nhận" |
| Bản ghi dồn vào TP.HCM, Lâm Đồng, Khánh Hòa | Trang bản đồ làm nổi bật vùng thưa dữ liệu |
| 3% nguy cấp, tập trung Lâm Đồng, Đắk Nông, Nghệ An | Một trang nhỏ, ghi chú mẫu ít và có thể gồm cây trồng |

**Thông điệp chốt:** dữ liệu thực vật Việt Nam 2020–2026 tăng nhanh nhờ ghi nhận cộng đồng, nhưng lệch về đô thị và điểm du lịch, nên vùng núi và rừng sâu vẫn là khoảng trống.

**Hạn chế:** dữ liệu là mẫu quan sát có thiên lệch, không phải khảo sát có hệ thống; mức IUCN thiếu 59%; tỉnh theo ranh giới GADM cũ (63 tỉnh).
"""),
]

if __name__ == "__main__":
    write("09_eda_preprocess.ipynb", notebook(CELLS))
    print("Da sinh notebooks/09_eda_preprocess.ipynb")
