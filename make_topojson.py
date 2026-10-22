"""Sinh powerbi/vn_provinces.topojson (dung cho visual Shape map cua Power BI).

Ten tinh (properties.name) trung voi cot `province` trong vn_plants_clean.csv.
Chay:  python make_topojson.py
"""
import json
from pathlib import Path

import pandas as pd

from build_dashboard import GEO_CACHE, norm

ROOT = Path(__file__).parent


MIN_AREA = 2e-5  # bo dao qua nho (nho hon khoang 0,25 km2), giu lai vanh lon nhat cua moi tinh


def area2(ring):
    """Hai lan dien tich co dau: duong khi vanh quay theo chieu kim dong ho."""
    return sum((x2 - x1) * (y2 + y1) for (x1, y1), (x2, y2) in zip(ring, ring[1:]))


def clockwise(ring):
    """TopoJSON quy uoc vanh ngoai quay theo chieu kim dong ho; GeoJSON (GADM) thi nguoc lai."""
    return ring if area2(ring) > 0 else ring[::-1]


def main():
    names = sorted(pd.read_csv(ROOT / "vn_plants_clean.csv", usecols=["province"])["province"].dropna().unique())
    by_norm = {norm(n): n for n in names}
    arcs, geoms, unmatched = [], [], []
    for feat in json.loads(GEO_CACHE.read_text(encoding="utf-8")):
        name = by_norm.get(norm(feat["name"]))
        if name is None:
            unmatched.append(feat["name"])
            continue
        polygons = []
        rings = [r for r in feat["rings"] if abs(area2(r)) >= MIN_AREA]
        rings = rings or [max(feat["rings"], key=lambda r: abs(area2(r)))]
        for ring in rings:
            arcs.append(clockwise(ring))           # mot vanh = mot cung khep, toa do tuyet doi (khong dung transform)
            polygons.append([[len(arcs) - 1]])
        geom = ({"type": "Polygon", "arcs": polygons[0]} if len(polygons) == 1
                else {"type": "MultiPolygon", "arcs": polygons})
        geom["properties"] = {"name": name}
        geoms.append(geom)
    topo = {"type": "Topology", "objects": {"provinces": {"type": "GeometryCollection", "geometries": geoms}}, "arcs": arcs}
    out = ROOT / "powerbi" / "vn_provinces.topojson"
    out.write_text(json.dumps(topo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Da tao {out.name}: {len(geoms)} tinh, {len(arcs)} cung, {out.stat().st_size / 1e3:.0f} KB; khong khop: {unmatched}")


if __name__ == "__main__":
    main()
