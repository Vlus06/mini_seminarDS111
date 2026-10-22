"""Sinh du an Power BI (.pbip) cho dashboard thuc vat Viet Nam (3 trang).

Chay:  python make_pbip.py
Ket qua: powerbi/ThucVat_VN.pbip (mo bang Power BI Desktop, Home > Refresh de nap du lieu)
  - ThucVat_VN.SemanticModel/model.bim : bang ban_ghi, cot, measure, truy van M
  - ThucVat_VN.Report/definition/...   : bao cao dang PBIR, 3 trang: Tong quan, Thoi gian va nguon, Bao ton
Nguon: vn_plants_clean.csv, powerbi/load_data.m, powerbi/measures.dax, powerbi/theme_thucvat.json
"""
import csv
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
PB = ROOT / "powerbi"
NAME = "ThucVat_VN"
MODEL_DIR = PB / f"{NAME}.SemanticModel"
REPORT_DIR = PB / f"{NAME}.Report"
ENT = "ban_ghi"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
V_REPORT, V_PAGE, V_VISUAL, V_PAGES = "3.0.0", "2.0.0", "2.3.0", "1.0.0"
RED, RED_LIGHT, GRAY, ORANGE = "#d03b3b", "#f2a0a0", "#b8b7b0", "#eb6834"


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- mo hinh du lieu
INT_COLS = {"gbifID", "year", "month", "day", "loai_ban_ghi_thu_tu", "iucn_thu_tu"}
DOUBLE_COLS = {"decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters"}
BOOL_COLS = {"is_assessed", "is_threatened", "species_level", "coord_imprecise"}
EXTRA_COLS = ["nam_nhan", "thang_nhan", "loai_ban_ghi", "loai_ban_ghi_thu_tu", "iucn_thu_tu", "dia_diem"]
SORT_BY = {"loai_ban_ghi": "loai_ban_ghi_thu_tu", "iucn_group": "iucn_thu_tu", "thang_nhan": "month"}
CATEGORY = {"decimalLatitude": "latitude", "decimalLongitude": "longitude", "province": "stateOrProvince",
            "dia_diem": "place"}
FORMAT = {"Ty_le_IUCN": "0%", "Ty_le_chua_danh_gia": "0%", "Ty_le_nguy_cap": "0%", "Ty_le_tieu_ban": "0%",
          "Top5_tinh_ty_le": "0%", "So_ban_ghi": "#,0", "So_ban_ghi_co_tinh": "#,0", "So_ban_ghi_co_loai": "#,0",
          "So_loai": "#,0", "So_ho": "#,0", "So_tinh": "#,0", "So_nguy_cap": "#,0", "So_nguy_cap_co_tinh": "#,0"}


def lines(text):
    return text.strip("\n").split("\n")


def parse_measures():
    raw = (PB / "measures.dax").read_text(encoding="utf-8")
    raw = raw[raw.index("DEFINE") + 6: raw.rindex("EVALUATE")]
    body = "\n".join(l for l in raw.split("\n") if not l.strip().startswith("//"))
    out = []
    for part in re.split(r"(?m)^\s*MEASURE\s+ban_ghi\[", body):
        if not part.strip():
            continue
        name, rest = part.split("]", 1)
        m = {"name": name, "expression": lines(rest.strip().lstrip("=").strip())}
        if name in FORMAT:
            m["formatString"] = FORMAT[name]
        out.append(m)
    return out


def build_model():
    with open(ROOT / "vn_plants_clean.csv", encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f))
    columns = []
    for c in header + EXTRA_COLS:
        col = {"name": c, "dataType": "string", "sourceColumn": c}
        if c in INT_COLS:
            col.update(dataType="int64", formatString="0", summarizeBy="none")
        elif c in DOUBLE_COLS:
            col.update(dataType="double", summarizeBy="none")
        elif c in BOOL_COLS:
            col.update(dataType="boolean", formatString='"TRUE";"TRUE";"FALSE"')
        if c in SORT_BY:
            col["sortByColumn"] = SORT_BY[c]
        if c in CATEGORY:
            col["dataCategory"] = CATEGORY[c]
        columns.append(col)
    m_code = (PB / "load_data.m").read_text(encoding="utf-8")
    m_code = "\n".join(l for l in m_code.split("\n") if not l.startswith("//")).strip()
    table = {
        "name": ENT, "columns": columns,
        "partitions": [{"name": ENT, "mode": "import", "source": {"type": "m", "expression": lines(m_code)}}],
        "measures": parse_measures(),
    }
    return {"compatibilityLevel": 1567,
            "model": {"culture": "en-US", "defaultPowerBIDataSourceVersion": "powerBI_V3",
                      "sourceQueryCulture": "en-US", "tables": [table],
                      "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps([ENT])}]}}


# ---------------------------------------------------------------- thanh phan bao cao (PBIR)
def lit(value):
    """Literal cua Power BI: chuoi nam trong dau nhay don, so co hau to D, bool la true/false."""
    if isinstance(value, bool):
        return {"expr": {"Literal": {"Value": "true" if value else "false"}}}
    if isinstance(value, (int, float)):
        return {"expr": {"Literal": {"Value": f"{value}D"}}}
    return {"expr": {"Literal": {"Value": "'" + str(value).replace("'", "''") + "'"}}}


def field(kind, prop):
    return {kind: {"Expression": {"SourceRef": {"Entity": ENT}}, "Property": prop}}


def proj(kind, prop, active=None, name=None):
    p = {"field": field(kind, prop), "queryRef": f"{ENT}.{prop}", "nativeQueryRef": prop}
    if active is not None:
        p["active"] = active
    if name:
        p["displayName"] = name
    return p


def src_ref(kind, prop):
    return {kind: {"Expression": {"SourceRef": {"Source": "b"}}, "Property": prop}}


def top_n(col, by_measure, n, name):
    """Bo loc Top N theo mot measure (cung dang file PBIR ma Power BI Desktop ghi ra)."""
    sub = {"Version": 2, "From": [{"Name": "b", "Entity": ENT, "Type": 0}],
           "Select": [{**src_ref("Column", col), "Name": "field"}],
           "OrderBy": [{"Direction": 2, "Expression": src_ref("Measure", by_measure)}], "Top": n}
    return {"name": name.ljust(20, "0"), "field": field("Column", col), "type": "TopN",
            "filter": {"Version": 2,
                       "From": [{"Name": "subquery", "Expression": {"Subquery": {"Query": sub}}, "Type": 2},
                                {"Name": "b", "Entity": ENT, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [src_ref("Column", col)],
                                                       "Table": {"SourceRef": {"Source": "subquery"}}}}}]}}


def is_true(col, name):
    """Bo loc: cot logic bang True."""
    return {"name": name.ljust(20, "0"), "field": field("Column", col), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "b", "Entity": ENT, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [src_ref("Column", col)],
                                                       "Values": [[{"Literal": {"Value": "true"}}]]}}}]}}


def not_blank(col, name):
    """Bo loc: bo gia tri trong (Blank) khoi mot cot."""
    return {"name": name.ljust(20, "0"), "field": field("Column", col), "type": "Advanced",
            "filter": {"Version": 2, "From": [{"Name": "b", "Entity": ENT, "Type": 0}],
                       "Where": [{"Condition": {"Not": {"Expression": {"Comparison": {
                           "ComparisonKind": 0, "Left": src_ref("Column", col),
                           "Right": {"Literal": {"Value": "null"}}}}}}}]}}


def sort_by(kind, prop, direction):
    return {"sort": [{"field": field(kind, prop), "direction": direction}], "isDefaultSort": False}


def solid(color):
    return {"solid": {"color": lit(color)}}


def point_color(col, value, color):
    """Mau rieng cho mot gia tri cua cot (vi du: Nguy cap mau do)."""
    return {"properties": {"fill": solid(color)},
            "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": field("Column", col),
                                                              "Right": {"Literal": {"Value": lit(value)["expr"]["Literal"]["Value"]}}}}}]}}


# Ma Python cho visual ban do. Doc duong vien 63 tinh tu assets/vn_provinces.json (GADM, da don gian hoa).
PY_HEAD = '''import json
import unicodedata

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

def norm(s):
    s = unicodedata.normalize("NFC", str(s)).lower()
    return "".join(ch for ch in s if ch.isalnum())

provinces = json.load(open(r"OUTLINE_PATH", encoding="utf-8"))
fig, ax = plt.subplots()
fig.patch.set_alpha(0)

def draw_outline(fill=None):
    for f in provinces:
        face = fill(f["name"]) if fill else "#efeeea"
        for ring in f["rings"]:
            ax.add_patch(Polygon(ring, closed=True, facecolor=face, edgecolor="white", linewidth=0.4))

ax.set_xlim(102, 109.6)
ax.set_ylim(8.2, 23.6)
ax.set_aspect(1 / np.cos(np.radians(16)))
ax.axis("off")
'''

PY_CHOROPLETH = PY_HEAD + '''
from matplotlib.colors import LinearSegmentedColormap

cmap = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])
counts = {norm(p): v for p, v in zip(dataset["province"], dataset["So_ban_ghi"]) if isinstance(p, str)}
top = max(counts.values()) if counts else 1

def fill(name):
    v = counts.get(norm(name), 0)
    return cmap(np.log1p(v) / np.log1p(top)) if v else "#efeeea"

draw_outline(fill)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, np.log1p(top)))
cb = plt.colorbar(sm, ax=ax, orientation="horizontal", shrink=0.6, pad=0.02, aspect=30)
ticks = [t for t in (1, 10, 100, 1000) if t <= top * 0.6] + [top]
cb.set_ticks([np.log1p(t) for t in ticks])
cb.set_ticklabels([f"{t:,}" for t in ticks])
cb.set_label("Số bản ghi (thang log)")
plt.tight_layout()
plt.show()
'''

PY_POINTS = PY_HEAD + '''
draw_outline()
d = dataset.dropna(subset=["decimalLongitude", "decimalLatitude"])
blur = d["coord_imprecise"].astype(str).str.lower() == "true"
ax.scatter(d.loc[~blur, "decimalLongitude"], d.loc[~blur, "decimalLatitude"], s=16, color="#d03b3b",
           edgecolors="white", linewidths=0.5, alpha=0.85, label="Sai số ≤ 5 km")
ax.scatter(d.loc[blur, "decimalLongitude"], d.loc[blur, "decimalLatitude"], s=30, facecolors="none",
           edgecolors="#d03b3b", linewidths=1.0, label="Sai số > 5 km")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, fontsize=8, title=f"{len(d):,} bản ghi nguy cấp")
plt.tight_layout()
plt.show()
'''


INK, INK2, MUTED, BORDER, SURFACE = "#0b0b0b", "#52514e", "#7a7974", "#e4e3df", "#fcfcfb"


def container(title, style):
    """Khung visual: the trang (nen trang, vien bo goc), the bo loc (tieu de nho, xam) hoac khong khung."""
    o = {}
    if title:
        small = style == "slicer"
        o["title"] = [{"properties": {
            "show": lit(True), "text": lit(title), "alignment": lit("left"), "bold": lit(not small),
            "fontSize": lit(10 if small else 12), "fontColor": solid(MUTED if small else INK)}}]
    boxed = style in ("card", "slicer")
    o["background"] = [{"properties": {"show": lit(boxed), "color": solid("#ffffff"), "transparency": lit(0)}}]
    o["border"] = [{"properties": {"show": lit(boxed), "color": solid(BORDER),
                                   "radius": lit(8 if style == "slicer" else 12), "width": lit(1)}}]
    return o


def labels(size=10):
    # labelDisplayUnits = 1: hien day du so (4.134), khong rut gon thanh 4,1K
    return {"show": lit(True), "fontSize": lit(size), "color": solid(INK), "labelDisplayUnits": lit(1)}


def axes(show_value_axis=False, legend=False):
    """Truc gon: bo luoi, an truc gia tri (da co nhan so), chu truc nho va xam."""
    return {
        "labels": [{"properties": labels()}],
        "valueAxis": [{"properties": {"show": lit(show_value_axis), "gridlineShow": lit(False)}}],
        "categoryAxis": [{"properties": {"fontSize": lit(10), "labelColor": solid(INK2)}}],
        "legend": [{"properties": {"show": lit(legend), "position": lit("Top"), "fontSize": lit(10),
                                   "labelColor": solid(INK2)}}],
    }


class Page:
    def __init__(self, key, name, display, height):
        self.key, self.name, self.display, self.height = key, name, display, height
        self.visuals = []

    def add(self, vtype, x, y, w, h, query_state, *, objects=None, title=None, filters=None, sort=None, sync=None,
            style="card"):
        n = len(self.visuals) + 1
        v = {"visualType": vtype, "query": {"queryState": query_state}, "drillFilterOtherVisuals": True}
        if sort:
            v["query"]["sortDefinition"] = sort
        if objects:
            v["objects"] = objects
        v["visualContainerObjects"] = container(title, style)
        if sync:
            v["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
        out = {"$schema": f"{SCHEMA}visualContainer/{V_VISUAL}/schema.json",
               "name": f"{self.key}v{n:02d}".ljust(20, "0"),
               "position": {"x": x, "y": y, "z": n * 100, "width": w, "height": h, "tabOrder": n * 100},
               "visual": v}
        if filters:
            out["filterConfig"] = {"filters": filters}
        self.visuals.append(out)

    def headline(self, measure):
        self.add("card", 20, 15, 1240, 60, {"Values": {"projections": [proj("Measure", measure)]}},
                 objects={"labels": [{"properties": {"fontSize": lit(20), "color": solid(INK)}}],
                          "categoryLabels": [{"properties": {"show": lit(False)}}]}, style="plain")

    def slicers(self, y=85):
        for i, (col, label) in enumerate([("nam_nhan", "Năm"), ("loai_ban_ghi", "Loại bản ghi"),
                                          ("iucn_group", "Mức IUCN"), ("family", "Họ")]):
            self.add("slicer", 20 + i * 313, y, 300, 62, {"Values": {"projections": [proj("Column", col, True)]}},
                     objects={"data": [{"properties": {"mode": lit("Dropdown")}}],
                              "header": [{"properties": {"show": lit(False)}}]},
                     title=label, sync=f"sync_{col}", style="slicer")

    def python(self, x, y, w, h, projections, code, title, filters=None):
        """Visual Python (matplotlib): ve ban do giong dashboard.html. Du lieu vao la DataFrame `dataset`."""
        code = code.replace("OUTLINE_PATH", str(ROOT / "assets" / "vn_provinces.json"))
        self.add("scriptVisual", x, y, w, h, {"Values": {"projections": projections}},
                 objects={"script": [{"properties": {"source": lit(code), "provider": lit("Python")}}]},
                 title=title, filters=filters)

    def note(self, y, text):
        self.add("textbox", 20, y, 1240, 50, {},
                 objects={"general": [{"properties": {"paragraphs": [{"textRuns": [
                     {"value": text, "textStyle": {"fontSize": "10px", "color": MUTED}}]}]}}]}, style="plain")


LABELS = axes()
SOURCE_NOTE = ("Nguồn: GBIF, thực vật Việt Nam, thu ngày 22/10/2026. Mỗi dòng là một lần ghi nhận, không phải một cây. "
               "Số bản ghi phản ánh nơi có người đi ghi nhận, không phải nơi có nhiều cây. 2026* chưa hết năm.")


def bar(page, x, y, w, h, cat_col, measure, title, *, n=None, top_by=None, color=None, flt=None, extra=None):
    filters = list(flt or [])
    if n:
        filters.append(top_n(cat_col, top_by or measure, n, f"f_{page.key}_{cat_col}"))
    objects = dict(LABELS)
    if color:
        objects["dataPoint"] = [{"properties": {"fill": solid(color)}}] + (extra or [])
    page.add("clusteredBarChart", x, y, w, h,
             {"Category": {"projections": [proj("Column", cat_col, True)]},
              "Y": {"projections": [proj("Measure", measure)]}},
             objects=objects, title=title, filters=filters, sort=sort_by("Measure", measure, "Descending"))


def page_overview():
    p = Page("p1", "a1b2c3d4e5f6a7b8c9d1", "1. Tổng quan", 1240)
    p.headline("Tieu_de_trang1")
    p.slicers()
    for i, (m, label) in enumerate([("So_ban_ghi", "Bản ghi"), ("So_loai", "Loài"), ("So_ho", "Họ"),
                                    ("So_tinh", "Tỉnh có dữ liệu"), ("Ty_le_IUCN", "Có mức IUCN")]):
        p.add("card", 20 + i * 250, 160, 240, 90, {"Values": {"projections": [proj("Measure", m, name=label)]}},
              objects={"labels": [{"properties": {"fontSize": lit(28), "color": solid(INK),
                                                  "labelDisplayUnits": lit(1)}}],
                       "categoryLabels": [{"properties": {"show": lit(True), "fontSize": lit(11),
                                                          "color": solid(INK2)}}]})
    p.python(20, 265, 610, 560, [proj("Column", "province"), proj("Measure", "So_ban_ghi")], PY_CHOROPLETH,
             "Số bản ghi theo tỉnh (bấm một thanh ở biểu đồ top 12 tỉnh để lọc cả trang)")
    bar(p, 650, 265, 610, 275, "family", "So_ban_ghi", "Top 10 họ", n=10, color="#2a78d6")
    bar(p, 650, 550, 610, 275, "species", "So_ban_ghi", "Top 10 loài (chỉ bản ghi định danh đến loài)", n=10,
        top_by="So_ban_ghi_co_loai", color="#2a78d6", flt=[is_true("species_level", "f_p1_species_level")])
    bar(p, 20, 845, 1240, 320, "province", "So_ban_ghi", "Top 12 tỉnh theo số bản ghi", n=12,
        top_by="So_ban_ghi_co_tinh", color="#2a78d6")
    p.note(1180, SOURCE_NOTE)
    return p


def page_time():
    p = Page("p2", "a1b2c3d4e5f6a7b8c9d0", "2. Thời gian và nguồn", 1330)
    p.headline("Tieu_de_trang2")
    p.slicers()
    ycat = lambda col: {"projections": [proj("Column", col, True)]}
    p.add("clusteredColumnChart", 20, 165, 610, 300,
          {"Category": ycat("nam_nhan"), "Y": {"projections": [proj("Measure", "So_ban_ghi")]}},
          objects=LABELS, title="Số bản ghi theo năm (2026* chưa hết năm)",
          sort=sort_by("Column", "nam_nhan", "Ascending"))
    p.add("clusteredColumnChart", 650, 165, 610, 300,
          {"Category": ycat("thang_nhan"), "Y": {"projections": [proj("Measure", "So_ban_ghi")]}},
          objects=LABELS, title="Số bản ghi theo tháng (gộp các năm)",
          filters=[not_blank("thang_nhan", "f_p2_thang")],
          sort=sort_by("Column", "thang_nhan", "Ascending"))
    p.add("hundredPercentStackedColumnChart", 20, 485, 610, 300,
          {"Category": ycat("nam_nhan"), "Series": ycat("loai_ban_ghi"),
           "Y": {"projections": [proj("Measure", "So_ban_ghi")]}},
          objects=axes(show_value_axis=True, legend=True),
          title="Cơ cấu loại bản ghi theo năm", sort=sort_by("Column", "nam_nhan", "Ascending"))
    bar(p, 650, 485, 610, 300, "datasetName", "So_ban_ghi", "Top 5 bộ dữ liệu nguồn (Blank = không rõ nguồn)",
        n=5, color=ORANGE)
    gradient = {"solid": {"color": {"expr": {"FillRule": {
        "Input": field("Measure", "So_ban_ghi"),
        "FillRule": {"linearGradient2": {
            "min": {"color": lit("#cde2fb")["expr"]}, "max": {"color": lit("#0d366b")["expr"]},
            "nullColoringStrategy": {"strategy": lit("asZero")["expr"]}}}}}}}}
    # heatmap to hon: chu 14, cot rong co dinh (tinh 200 + 7 nam x 140 = 1180, vua khung 1240), so can giua o
    width = lambda metadata, value: {"properties": {"value": lit(value)}, "selector": {"metadata": metadata}}
    p.add("pivotTable", 20, 805, 1240, 440,
          {"Rows": {"projections": [proj("Column", "province", True, name="Tỉnh")]},
           "Columns": {"projections": [proj("Column", "nam_nhan", True, name="Năm")]},
           "Values": {"projections": [proj("Measure", "So_ban_ghi")]}},
          objects={"subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}],
                   "grid": [{"properties": {"gridVertical": lit(False), "gridHorizontal": lit(False),
                                            "rowPadding": lit(8)}}],
                   "columnHeaders": [{"properties": {"fontSize": lit(13), "fontColor": solid(INK2),
                                                     "alignment": lit("Center"), "autoSizeColumnWidth": lit(False)}}],
                   "rowHeaders": [{"properties": {"fontSize": lit(13), "fontColor": solid(INK)}}],
                   "columnWidth": [width(f"{ENT}.So_ban_ghi", 140), width(f"{ENT}.province", 200)],
                   "values": [{"properties": {"fontSize": lit(14), "alignment": lit("Center")}},
                              {"properties": {"backColor": gradient},
                               "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                            "metadata": f"{ENT}.So_ban_ghi"}}]},
          title="Top 10 tỉnh theo năm (số bản ghi)",
          filters=[top_n("province", "So_ban_ghi_co_tinh", 10, "f_p2_province")],
          sort=sort_by("Measure", "So_ban_ghi", "Descending"))
    p.note(1265, SOURCE_NOTE + " Các đợt tăng vọt theo tỉnh thường do một dự án ghi nhận tập trung.")
    return p


def page_conservation():
    p = Page("p3", "a1b2c3d4e5f6a7b8c9d2", "3. Bảo tồn", 900)
    p.headline("Tieu_de_trang3")
    p.slicers()
    bar(p, 20, 165, 610, 300, "iucn_group", "So_ban_ghi", "Nhóm mức độ bảo tồn (IUCN)", color=GRAY,
        extra=[point_color("iucn_group", "Nguy cấp", RED)])
    bar(p, 650, 165, 610, 300, "province", "So_nguy_cap", "Loài nguy cấp: top 8 tỉnh", n=8,
        top_by="So_nguy_cap_co_tinh", color=RED)
    bar(p, 20, 485, 610, 320, "family", "So_nguy_cap", "Loài nguy cấp: top 8 họ", n=8, color=RED)
    p.python(650, 485, 610, 320,
             [proj("Column", "decimalLongitude"), proj("Column", "decimalLatitude"),
              proj("Column", "coord_imprecise"), proj("Column", "gbifID")], PY_POINTS,
             "Vị trí các bản ghi nguy cấp (chấm rỗng: sai số tọa độ trên 5 km, chỉ cho biết khu vực chung)",
             filters=[is_true("is_threatened", "f_p3_is_threatened")])
    p.note(825, "Nguy cấp gồm CR, EN, VU. Chưa đánh giá: loài chưa có trong danh mục IUCN. Mẫu nguy cấp ít (khoảng 500 bản, "
                "92 loài). Sai số tọa độ lớn ở loài nguy cấp có thể do nơi cung cấp cố ý làm mờ vị trí. " + SOURCE_NOTE)
    return p


def build_report(pages):
    shutil.rmtree(REPORT_DIR, ignore_errors=True)
    d = REPORT_DIR / "definition"
    write_json(REPORT_DIR / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(d / "version.json", {"$schema": f"{SCHEMA}versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    ver = {"visual": V_VISUAL, "report": V_REPORT, "page": V_PAGE}
    write_json(d / "report.json", {
        "$schema": f"{SCHEMA}report/{V_REPORT}/schema.json",
        "themeCollection": {"customTheme": {"name": "theme_thucvat.json", "reportVersionAtImport": ver,
                                            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "theme_thucvat.json", "path": "theme_thucvat.json", "type": "CustomTheme"}]}]})
    res = REPORT_DIR / "StaticResources" / "RegisteredResources"
    res.mkdir(parents=True, exist_ok=True)
    shutil.copy(PB / "theme_thucvat.json", res / "theme_thucvat.json")
    write_json(d / "pages" / "pages.json", {"$schema": f"{SCHEMA}pagesMetadata/{V_PAGES}/schema.json",
                                            "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    for p in pages:
        write_json(d / "pages" / p.name / "page.json", {
            "$schema": f"{SCHEMA}page/{V_PAGE}/schema.json", "name": p.name, "displayName": p.display,
            "displayOption": "FitToPage", "height": p.height, "width": 1280,
            "objects": {"background": [{"properties": {"color": solid(SURFACE), "transparency": lit(0)}}],
                        "outspace": [{"properties": {"color": solid(SURFACE)}}]}})
        for v in p.visuals:
            write_json(d / "pages" / p.name / "visuals" / v["name"] / "visual.json", v)


def main():
    shutil.rmtree(MODEL_DIR, ignore_errors=True)
    write_json(MODEL_DIR / "definition.pbism", {"version": "1.0"})
    write_json(MODEL_DIR / "model.bim", build_model())
    pages = [page_overview(), page_time(), page_conservation()]
    build_report(pages)
    write_json(PB / f"{NAME}.pbip", {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                     "settings": {"enableAutoRecovery": True}})
    print(f"Da tao powerbi/{NAME}.pbip: 1 bang, {len(parse_measures())} measure, {len(pages)} trang, "
          f"{sum(len(p.visuals) for p in pages)} visual")


if __name__ == "__main__":
    main()
