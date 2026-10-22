"""Sinh cac notebook cao GBIF (moi nam mot notebook) va notebook gop du lieu.

Chay:  python make_notebooks.py
Ket qua: thu muc notebooks/
"""
import json
import os

YEARS = range(2020, 2027)
OUT_DIR = "notebooks"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {
        "cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
        "source": text.strip("\n").splitlines(True),
    }


def notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


SCRAPE_CODE = '''
import time
import pandas as pd
import requests

URL = "https://api.gbif.org/v1/occurrence/search"
BASE = dict(country="VN", kingdomKey=6, hasCoordinate="true", hasGeospatialIssue="false", year=YEAR)

FIELDS = [
    "gbifID", "scientificName", "species", "genus", "family", "order", "class", "phylum",
    "taxonRank", "iucnRedListCategory", "basisOfRecord", "datasetName", "institutionCode",
    "year", "month", "day", "decimalLatitude", "decimalLongitude",
    "coordinateUncertaintyInMeters", "elevation", "stateProvince", "recordedBy", "license",
]


def get(params):
    for attempt in range(5):
        try:
            r = requests.get(URL, params={**BASE, **params}, timeout=60)
            if r.status_code == 429:  # bi gioi han toc do
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"GBIF khong phan hoi (offset={params.get('offset')})")


expected = get({"limit": 0})["count"]
print(f"Nam {YEAR}: GBIF bao co {expected} ban ghi")

rows = []
for offset in range(0, expected, PAGE):
    for rec in get({"limit": PAGE, "offset": offset})["results"]:
        row = {k: rec.get(k) for k in FIELDS}
        gadm = rec.get("gadm") or {}
        row["province_gadm"] = (gadm.get("level1") or {}).get("name")
        rows.append(row)
    time.sleep(0.3)
    print(f"  offset {offset}: tong {len(rows)}")

df = pd.DataFrame(rows).drop_duplicates("gbifID")
print(f"Thu duoc {len(df)} / {expected} ban ghi")
'''

SAVE_CODE = '''
import os
os.makedirs(OUT_DIR, exist_ok=True)
path = os.path.join(OUT_DIR, f"gbif_vn_plants_{YEAR}.csv")
df.to_csv(path, index=False, encoding="utf-8-sig")
print("Da luu", path)
'''

CHECK_CODE = '''
print("So dong:", len(df), "| so cot:", df.shape[1])
print("Khop voi GBIF:", len(df) == expected, f"({len(df)} / {expected})")
print()
print("Ty le thieu theo cot:")
print(df.isna().mean().round(2).sort_values(ascending=False).head(10).to_string())
df.head()
'''


def scrape_notebook(year):
    return notebook([
        md(f"# Cào dữ liệu thực vật Việt Nam từ GBIF: năm {year}\n\n"
           "Mỗi notebook cào một năm. Chạy hết các ô theo thứ tự rồi tải file CSV ở `OUT_DIR`.\n"
           "Trên Kaggle: bật Internet trong Settings, kết quả nằm ở `/kaggle/working`."),
        code(f'YEAR = {year}\nPAGE = 300  # GBIF cho toi da 300 ban ghi moi trang\n'
             'import os\nOUT_DIR = "/kaggle/working" if "KAGGLE_KERNEL_RUN_TYPE" in os.environ else "data"'),
        code(SCRAPE_CODE),
        code(SAVE_CODE),
        md("## Kiểm tra nhanh"),
        code(CHECK_CODE),
    ])


MERGE_CODE = '''
import glob
import pandas as pd

files = sorted(glob.glob(f"{DATA_DIR}/gbif_vn_plants_*.csv"))
print(len(files), "file:", [f.split("_")[-1][:4] for f in files])
df = pd.concat([pd.read_csv(f, low_memory=False) for f in files], ignore_index=True)
print("Truoc khi loai trung:", len(df))
df = df.drop_duplicates("gbifID")
print("Sau khi loai trung:", len(df))
'''

CLEAN_CODE = '''
THREATENED = {"CR", "EN", "VU"}

df["is_assessed"] = df["iucnRedListCategory"].notna()
df["is_threatened"] = df["iucnRedListCategory"].isin(THREATENED)
df["source_type"] = df["basisOfRecord"].map({
    "PRESERVED_SPECIMEN": "Tieu ban",
    "HUMAN_OBSERVATION": "Quan sat",
    "OCCURRENCE": "Quan sat",
    "MACHINE_OBSERVATION": "Quan sat",
    "LIVING_SPECIMEN": "Mau song",
}).fillna("Khac")
df["year_month"] = pd.to_datetime(
    dict(year=df["year"], month=df["month"].fillna(1).astype(int), day=1), errors="coerce"
)

print(df[["is_assessed", "is_threatened"]].mean().round(3).to_string())
print()
print(df["source_type"].value_counts().to_string())
print()
print("Ty le thieu theo cot:")
print(df.isna().mean().round(2).sort_values(ascending=False).to_string())
'''

SAVE_MERGE_CODE = '''
df.to_csv("vn_plants_gbif_2020_2026.csv", index=False, encoding="utf-8-sig")
print("Da luu vn_plants_gbif_2020_2026.csv:", df.shape)
'''


def merge_notebook():
    return notebook([
        md("# Gộp và làm sạch dữ liệu GBIF 2020–2026\n\n"
           "Đặt 7 file `gbif_vn_plants_<năm>.csv` (tải từ các notebook cào) vào thư mục `DATA_DIR`."),
        code('DATA_DIR = "data"'),
        code(MERGE_CODE),
        md("## Tạo cột phụ"),
        code(CLEAN_CODE),
        md("## Lưu file dùng cho dashboard"),
        code(SAVE_MERGE_CODE),
    ])


def write(name, nb):
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, y in enumerate(YEARS, 1):
        write(f"{i:02d}_scrape_{y}.ipynb", scrape_notebook(y))
    write("08_merge_clean.ipynb", merge_notebook())
    print("Da sinh", len(list(YEARS)) + 1, "notebook trong", OUT_DIR)


if __name__ == "__main__":
    main()
