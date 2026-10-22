"""Sinh dashboard.html (mot file HTML doc lap) tu vn_plants_clean.csv.

Chay:  python build_dashboard.py
Can co: vn_plants_clean.csv (notebook 09) va dashboard_template.html.
Ranh gioi tinh: GADM 4.1 (tai ve lan dau, luu don gian hoa trong assets/vn_provinces.json).
"""
import io
import json
import math
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).parent
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_VNM_1.json.zip"
GEO_CACHE = ROOT / "assets" / "vn_provinces.json"
TOLERANCE = 0.008  # do, khoang 900 m
SCALE = 48         # pixel tren mot do vi do


def norm(name):
    """Bo dau cach, dau gach, chuan hoa unicode de khop ten GADM voi ten trong du lieu."""
    s = unicodedata.normalize("NFC", str(name)).lower()
    return "".join(ch for ch in s if ch.isalnum())


def simplify(points, tol):
    """Douglas-Peucker (khong de quy sau) cho mot duong gom cac diem (lon, lat)."""
    if len(points) < 4:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = points[a], points[b]
        dx, dy = x2 - x1, y2 - y1
        norm_len = math.hypot(dx, dy) or 1e-12
        far, far_i = 0.0, None
        for i in range(a + 1, b):
            x, y = points[i]
            d = abs(dy * (x - x1) - dx * (y - y1)) / norm_len
            if d > far:
                far, far_i = d, i
        if far_i is not None and far > tol:
            keep[far_i] = True
            stack += [(a, far_i), (far_i, b)]
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, tol):
    """Vanh khep co diem dau trung diem cuoi: tach doi tai diem xa nhat roi don gian hoa tung nua."""
    far = max(range(len(ring)), key=lambda i: math.hypot(ring[i][0] - ring[0][0], ring[i][1] - ring[0][1]))
    return simplify(ring[:far + 1], tol)[:-1] + simplify(ring[far:], tol)


def load_provinces():
    if GEO_CACHE.exists():
        return json.loads(GEO_CACHE.read_text(encoding="utf-8"))
    raw = requests.get(GADM_URL, timeout=120)
    raw.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(raw.content))
    gj = json.loads(z.read(z.namelist()[0]))
    out = []
    for feat in gj["features"]:
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        rings = []
        for poly in polys:
            for ring in poly[:1]:  # chi lay vanh ngoai
                s = simplify_ring([tuple(p) for p in ring], TOLERANCE)
                if len(s) >= 4:
                    rings.append([[round(x, 3), round(y, 3)] for x, y in s])
        out.append({"name": feat["properties"]["NAME_1"], "rings": rings})
    GEO_CACHE.parent.mkdir(exist_ok=True)
    GEO_CACHE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def build_geo(provinces, prov_names):
    index = {norm(n): i for i, n in enumerate(prov_names)}
    lons = [x for p in provinces for r in p["rings"] for x, _ in r]
    lats = [y for p in provinces for r in p["rings"] for _, y in r]
    lon0, lat1 = min(lons) - 0.1, max(lats) + 0.1
    cos = math.cos(math.radians((min(lats) + max(lats)) / 2))
    geo = {"lon0": lon0, "lat1": lat1, "k": SCALE, "cos": cos,
           "w": round((max(lons) + 0.1 - lon0) * SCALE * cos, 1),
           "h": round((lat1 - min(lats) + 0.1) * SCALE, 1), "f": []}
    unmatched = []
    for p in provinces:
        idx = index.get(norm(p["name"]), -1)
        if idx < 0:
            unmatched.append(p["name"])
        d = ""
        for ring in p["rings"]:
            pts = [f"{(x - lon0) * SCALE * cos:.1f},{(lat1 - y) * SCALE:.1f}" for x, y in ring]
            d += "M" + "L".join(pts) + "Z"
        geo["f"].append({"p": idx, "d": d})
    return geo, unmatched


def main():
    df = pd.read_csv(ROOT / "vn_plants_clean.csv", low_memory=False)

    def codes(series, order=None):
        cats = order or sorted(series.dropna().unique())
        lut = {c: i for i, c in enumerate(cats)}
        return cats, series.map(lut).fillna(-1).astype(int).tolist()

    prov, p = codes(df["province"])
    fam_counts = df["family"].value_counts()
    fam, f = codes(df["family"], list(fam_counts.index))  # da sap theo so ban ghi giam dan
    sp_df = df["species"].where(df["species_level"])
    sp, s = codes(sp_df)
    iucn_order = ["Chưa đánh giá", "Ít quan ngại", "Nguy cấp", "Thiếu dữ liệu", "Khác"]
    _, iu = codes(df["iucn_group"], iucn_order)
    src = df["source_type"].map({"Quan sat": 0, "Tieu ban": 1}).fillna(2).astype(int).tolist()
    ds_series = df["datasetName"].fillna("Không rõ nguồn").str.replace(
        "iNaturalist research-grade observations", "iNaturalist (research grade)")
    ds, dsi = codes(ds_series)

    data = {
        "n": len(df),
        "dict": {"years": list(range(2020, 2027)), "prov": prov, "fam": fam,
                 "famOrder": list(range(len(fam))), "sp": sp, "iucn": iucn_order, "ds": ds},
        "r": {
            "y": df["year"].astype(int).tolist(),
            "m": df["month"].fillna(0).astype(int).tolist(),
            "p": p, "f": f, "s": s, "src": src, "iu": iu,
            "th": df["is_threatened"].astype(int).tolist(),
            "lat": df["decimalLatitude"].round(3).tolist(),
            "lon": df["decimalLongitude"].round(3).tolist(),
            "imp": df["coord_imprecise"].astype(int).tolist(),
            "ds": dsi,
        },
    }
    geo, unmatched = build_geo(load_provinces(), prov)
    if unmatched:
        print("Canh bao: tinh GADM khong khop ten trong du lieu:", unmatched)

    html = (ROOT / "dashboard_template.html").read_text(encoding="utf-8")
    html = html.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*GEO*/null", json.dumps(geo, ensure_ascii=False, separators=(",", ":")))
    out = ROOT / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"Da tao {out.name}: {out.stat().st_size / 1e6:.2f} MB, {len(df)} ban ghi, "
          f"{sum(1 for x in geo['f'] if x['p'] >= 0)}/{len(geo['f'])} tinh khop")


if __name__ == "__main__":
    main()
