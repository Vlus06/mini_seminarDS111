"""Thu thap ~3000 ban ghi thuc vat Viet Nam tu GBIF API (khong can API key).

Lay mau ngau nhien (seed co dinh) bang cach lay nhieu trang nho tai offset ngau nhien,
de tranh lech do GBIF sap xep ban ghi theo bo du lieu.
Chay:  python scrape_gbif.py
"""
import random
import time

import pandas as pd
import requests

URL = "https://api.gbif.org/v1/occurrence/search"
BASE = dict(country="VN", kingdomKey=6, hasCoordinate="true", hasGeospatialIssue="false")
TARGET = 3000
PAGE = 20
SEED = 42

FIELDS = [
    "gbifID", "scientificName", "species", "genus", "family", "order", "phylum", "class",
    "taxonRank", "iucnRedListCategory", "basisOfRecord", "datasetName", "institutionCode",
    "year", "month", "day", "decimalLatitude", "decimalLongitude",
    "coordinateUncertaintyInMeters", "elevation", "stateProvince", "recordedBy", "license",
]


def get(params):
    for attempt in range(4):
        try:
            r = requests.get(URL, params={**BASE, **params}, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("GBIF khong phan hoi")


def main():
    total = get({"limit": 0})["count"]
    max_offset = min(total, 100000) - PAGE  # GBIF gioi han offset + limit <= 100000
    random.seed(SEED)
    offsets = random.sample(range(0, max_offset, PAGE), TARGET // PAGE + 10)
    rows, seen = [], set()
    for i, off in enumerate(offsets, 1):
        for rec in get({"limit": PAGE, "offset": off})["results"]:
            if rec["gbifID"] in seen:
                continue
            seen.add(rec["gbifID"])
            row = {k: rec.get(k) for k in FIELDS}
            gadm = rec.get("gadm") or {}
            row["province_gadm"] = (gadm.get("level1") or {}).get("name")
            rows.append(row)
        if i % 20 == 0:
            print(f"{i}/{len(offsets)} trang, {len(rows)} ban ghi")
        time.sleep(0.2)
    df = pd.DataFrame(rows).head(TARGET)
    df.to_csv("vn_plants_gbif.csv", index=False, encoding="utf-8-sig")
    print("Da luu", len(df), "dong -> vn_plants_gbif.csv")


if __name__ == "__main__":
    main()
