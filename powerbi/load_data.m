// Power Query (ngôn ngữ M): nạp vn_plants_clean.csv vào Power BI.
// Cách dùng: Home > Transform data > chuột phải vào bảng > Advanced Editor > dán toàn bộ nội dung này.
// Đổi DuongDan cho đúng vị trí file trên máy bạn, rồi Close & Apply. Đặt tên bảng là ban_ghi.
let
    DuongDan = "C:\DS111\miniseminar\vn_plants_clean.csv",
    Nguon = Csv.Document(File.Contents(DuongDan), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    TieuDe = Table.PromoteHeaders(Nguon, [PromoteAllScalars = true]),

    // Ô trống trong CSV thành null để Power BI coi là Blank (nếu không, DISTINCTCOUNT đếm thêm một giá trị rỗng)
    LamSach = Table.ReplaceValue(TieuDe, "", null, Replacer.ReplaceValue, Table.ColumnNames(TieuDe)),

    // Ép kiểu; culture en-US để dấu chấm thập phân được đọc đúng
    Kieu = Table.TransformColumnTypes(LamSach, {
        {"gbifID", Int64.Type}, {"year", Int64.Type}, {"month", Int64.Type}, {"day", Int64.Type},
        {"decimalLatitude", type number}, {"decimalLongitude", type number},
        {"coordinateUncertaintyInMeters", type number},
        {"is_assessed", type logical}, {"is_threatened", type logical},
        {"species_level", type logical}, {"coord_imprecise", type logical}
    }, "en-US"),

    // Nhãn tiếng Việt và cột thứ tự để sắp xếp trên biểu đồ
    NamNhan = Table.AddColumn(Kieu, "nam_nhan", each if [year] = 2026 then "2026*" else Text.From([year]), type text),
    ThangNhan = Table.AddColumn(NamNhan, "thang_nhan", each if [month] = null then null else "T" & Text.From([month]), type text),
    LoaiBanGhi = Table.AddColumn(ThangNhan, "loai_ban_ghi", each
        if [source_type] = "Quan sat" then "Quan sát"
        else if [source_type] = "Tieu ban" then "Tiêu bản"
        else "Khác", type text),
    LoaiThuTu = Table.AddColumn(LoaiBanGhi, "loai_ban_ghi_thu_tu", each
        if [loai_ban_ghi] = "Quan sát" then 1 else if [loai_ban_ghi] = "Tiêu bản" then 2 else 3, Int64.Type),
    IucnThuTu = Table.AddColumn(LoaiThuTu, "iucn_thu_tu", each
        List.PositionOf({"Chưa đánh giá", "Ít quan ngại", "Nguy cấp", "Thiếu dữ liệu", "Khác"}, [iucn_group]) + 1, Int64.Type),

    // Tên địa điểm kèm quốc gia, để bản đồ Bing xác định đúng tỉnh của Việt Nam
    DiaDiem = Table.AddColumn(IucnThuTu, "dia_diem", each
        if [province] = null then null else [province] & ", Việt Nam", type text)
in
    DiaDiem
