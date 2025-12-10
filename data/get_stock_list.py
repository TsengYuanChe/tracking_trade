import csv
import json
import re

FILES = ["StockList1.csv", "StockList.csv"]
OUTPUT = "company_names.json"

company_dict = {}

def normalize(col: str):
    """移除 BOM、空白、雙引號"""
    return col.replace("\ufeff", "").strip().strip('"').strip()


def clean_code(raw_code: str):
    """
    清理代號，例如 = "0050" → 0050
    """
    raw_code = raw_code.strip()

    if raw_code.startswith("=\"") and raw_code.endswith("\""):
        raw_code = raw_code[2:-1]

    return normalize(raw_code)


def is_valid_stock_code(code: str):
    """只接受4位數字股票代號"""
    return bool(re.fullmatch(r"\d{4}", code))


def process_csv(file):
    print(f"Parsing {file} ...")

    try:
        with open(file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)

            header = next(reader, None)
            if not header:
                print("⚠ 無法讀取 header")
                return

            # 正規化欄位名稱（移除 BOM + 雙引號）
            header = [normalize(h) for h in header]

            # 尋找欄位 index
            try:
                code_idx = header.index("代號")
                name_idx = header.index("名稱")
            except ValueError:
                print("⚠ 找不到欄位：代號 / 名稱")
                print("header =", header)
                return

            # 處理每一列
            for row in reader:
                if len(row) <= max(code_idx, name_idx):
                    continue

                raw_code = clean_code(row[code_idx])
                name = normalize(row[name_idx])

                if is_valid_stock_code(raw_code):
                    company_dict[raw_code] = name

    except FileNotFoundError:
        print(f"⚠ 找不到檔案：{file}")


# 主流程
for f in FILES:
    process_csv(f)

# 輸出
with open(OUTPUT, "w", encoding="utf-8") as outfile:
    json.dump(company_dict, outfile, ensure_ascii=False, indent=2)

print("\nSaved:", OUTPUT)
print("Total companies:", len(company_dict))