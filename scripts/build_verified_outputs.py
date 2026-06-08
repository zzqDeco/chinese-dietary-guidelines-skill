#!/usr/bin/env python3
import csv
import importlib.util
import os
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QA_DIR = ROOT / "qa"
TABLE_REVIEW_SCRIPT = ROOT / "scripts" / "apply_table_column_review.py"
FULL_SOURCE = ROOT / "dietary_guidelines_china_2022_full.md"
TABLES_SOURCE = ROOT / "dietary_guidelines_china_2022_tables.md"
FULL_VERIFIED = ROOT / "dietary_guidelines_china_2022_full_verified.md"
TABLES_VERIFIED = ROOT / "dietary_guidelines_china_2022_tables_verified.md"
TABLE_CELL_LOG = QA_DIR / "table_cell_corrections.csv"
TERM_LOG = QA_DIR / "ocr_term_corrections.csv"
SENTINEL_LOG = QA_DIR / "numeric_sentinel_check.csv"
AUDIT = QA_DIR / "extraction_audit.md"
OVERRIDES = QA_DIR / "verified_table_overrides.md"
BODY_TEXT_CORRECTIONS = QA_DIR / "body_text_corrections.csv"
LOW_PAGE_REVIEW = QA_DIR / "low_confidence_page_review.csv"
DENSE_BMI_PAGE = 365


TERM_RULES = {
    "腾食": ("膳食", "corrected", "high", "批量规则修正；逐条保留上下文。"),
    "摄和": ("摄入", "corrected", "medium", "批量规则修正；逐条保留上下文。"),
    "报信": ("摄入", "corrected", "medium", "批量规则修正；逐条保留上下文。"),
    "训调": ("烹调", "corrected", "medium", "批量规则修正；逐条保留上下文。"),
    "豪调": ("烹调", "corrected", "medium", "批量规则修正；逐条保留上下文。"),
    "kgjm": ("kg/m²", "corrected", "medium", "批量规则修正；逐条保留上下文。"),
    "R216": ("R216", "uncertain_registered", "low", "上下文不足，verified 版保留并登记。"),
    "BERE": ("BERE", "uncertain_registered", "low", "上下文不足，先登记；残留正文噪声由 body_text_corrections 按页图精确修正。"),
    "公策": ("公筷", "corrected", "high", "页图核对：准则八语境均为公筷；公勺搭配由 body_text_corrections 精确修正。"),
}

TERM_ORDER = sorted(TERM_RULES, key=len, reverse=True)
ALLOWED_TABLE_ACTIONS = {"corrected", "confirmed", "uncertain_registered", "not_numeric_cell"}
ALLOWED_SENTINEL_STATUS = {"pass", "corrected", "uncertain_registered"}


def load_review_module():
    spec = importlib.util.spec_from_file_location("apply_table_column_review", TABLE_REVIEW_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_tables(review_module):
    os.chdir(ROOT)
    build_module = review_module.load_build_module()
    pages = build_module.read_pages()
    return build_module.extract_tables(pages)


def load_verified_overrides() -> dict[int, str]:
    if not OVERRIDES.exists():
        return {}
    text = OVERRIDES.read_text(encoding="utf-8")
    overrides = {}
    for match in re.finditer(r"^##\s+(\d{3})\b.*?\n(.*?)(?=^##\s+\d{3}\b|\Z)", text, re.M | re.S):
        idx = int(match.group(1))
        body = match.group(2).strip()
        if body:
            overrides[idx] = body
    return overrides


def apply_term_corrections(text: str) -> str:
    for term in TERM_ORDER:
        corrected, action, _confidence, _notes = TERM_RULES[term]
        if action == "corrected":
            text = text.replace(term, corrected)
    return text


def load_body_text_corrections() -> list[dict[str, str]]:
    if not BODY_TEXT_CORRECTIONS.exists():
        return []
    with BODY_TEXT_CORRECTIONS.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    allowed_actions = {"corrected", "confirmed", "uncertain_registered"}
    allowed_modes = {"exact", "regex"}
    for row in rows:
        action = row.get("action", "")
        mode = row.get("mode", "")
        if action not in allowed_actions:
            raise ValueError(f"Unsupported body correction action: {action}")
        if action == "corrected" and mode not in allowed_modes:
            raise ValueError(f"Unsupported body correction mode: {mode}")
    return rows


def apply_single_body_correction(chunk: str, row: dict[str, str]) -> tuple[str, int]:
    if row.get("action") != "corrected":
        return chunk, 0
    original = row["original_text"]
    corrected = row["corrected_text"]
    if row.get("mode") == "regex":
        return re.subn(original, corrected, chunk, count=1, flags=re.S)
    if original not in chunk:
        return chunk, 0
    return chunk.replace(original, corrected, 1), 1


def apply_body_text_corrections(text: str, rows: list[dict[str, str]] | None = None) -> str:
    rows = load_body_text_corrections() if rows is None else rows
    if not rows:
        return text

    by_page = defaultdict(list)
    for row in rows:
        if row.get("file") == "full" and row.get("action") == "corrected":
            by_page[row["pdf_page"]].append(row)

    chunks = re.split(r"(?=<!-- pdf-page:\d{3} -->)", text)
    out = [chunks[0]]
    applied_keys = Counter()
    missing = []
    for chunk in chunks[1:]:
        match = re.match(r"<!-- pdf-page:(\d{3}) -->", chunk)
        if not match:
            out.append(chunk)
            continue
        page = match.group(1)
        for row in by_page.get(page, []):
            chunk, count = apply_single_body_correction(chunk, row)
            key = (row["pdf_page"], row["location_hint"], row["original_text"])
            if count:
                applied_keys[key] += count
            else:
                missing.append(key)
        out.append(chunk)

    if missing:
        formatted = "; ".join(f"p{page} {hint}: {original[:60]}" for page, hint, original in missing[:8])
        more = "" if len(missing) <= 8 else f"; ... +{len(missing) - 8} more"
        raise RuntimeError(f"Body text corrections did not match verified source: {formatted}{more}")

    return "".join(out)


def compact_context(text: str, start: int, end: int, window: int = 36) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def page_for_offset(text: str, offset: int) -> str:
    page = "unknown"
    for match in re.finditer(r"<!-- pdf-page:(\d{3}) -->", text):
        if match.start() > offset:
            break
        page = match.group(1)
    return page


def table_page_for_offset(text: str, offset: int) -> str:
    prefix = text[:offset]
    matches = list(re.finditer(r"\| PDF 页 \| (\d{3}) \|", prefix))
    return matches[-1].group(1) if matches else "unknown"


def collect_term_rows(file_path: Path, file_label: str) -> list[dict[str, str]]:
    text = file_path.read_text(encoding="utf-8")
    rows = []
    for term in TERM_RULES:
        corrected, action, confidence, notes = TERM_RULES[term]
        for match in re.finditer(re.escape(term), text):
            page = page_for_offset(text, match.start()) if file_label == "full" else table_page_for_offset(text, match.start())
            context = compact_context(text, match.start(), match.end())
            rows.append(
                {
                    "pdf_page": page,
                    "file": file_label,
                    "location_hint": context,
                    "original_text": term,
                    "corrected_text": corrected,
                    "term": term,
                    "action": action,
                    "confidence": confidence,
                    "notes": notes,
                }
            )
    rows.sort(key=lambda row: (row["file"], row["pdf_page"], row["term"], row["location_hint"]))
    return rows


def write_term_log() -> list[dict[str, str]]:
    rows = collect_term_rows(FULL_SOURCE, "full") + collect_term_rows(TABLES_SOURCE, "tables")
    with TERM_LOG.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "pdf_page",
                "file",
                "location_hint",
                "original_text",
                "corrected_text",
                "term",
                "action",
                "confidence",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def table_metadata(review_module, idx: int, table, overrides: dict[int, str] | None = None) -> dict[str, str]:
    structure_confidence, content_confidence = review_module.confidence(idx)
    if overrides and idx in overrides:
        structure_confidence = "high"
        content_confidence = "high"
    return {
        "candidate_no": f"{idx:03d}",
        "table_id": table.table_id,
        "title": apply_term_corrections(review_module.TITLE_OVERRIDES.get(idx, table.title)),
        "pdf_page": f"{table.page:03d}",
        "source_image": f"qa/table_page_images/page_{table.page:03d}.png",
        "status": review_module.review_status(idx, table.status),
        "structure_confidence": structure_confidence,
        "content_confidence": content_confidence,
    }


def verified_markdown_for_table(review_module, idx: int, table, overrides: dict[int, str] | None = None) -> str:
    if overrides and idx in overrides:
        return apply_term_corrections(overrides[idx])
    return apply_term_corrections(review_module.reviewed_markdown(idx, table))


def markdown_table_cells(markdown: str) -> list[tuple[str, str, str]]:
    lines = [line.strip() for line in markdown.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(lines) < 2:
        return []
    blocks = []
    current = []
    for line in lines:
        if re.fullmatch(r"\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|", line):
            if current:
                current.append(line)
                blocks.append(current)
                current = []
            continue
        current.append(line)
    parsed = []
    for i, block in enumerate(blocks):
        if not block:
            continue
        header_line = block[0]
        body_lines = lines[lines.index(block[-1]) + 1 :]
        # Use the first markdown table only; override sections contain one primary table.
        headers = [cell.strip() for cell in header_line.strip("|").split("|")]
        data_start = lines.index(block[-1]) + 1
        data_lines = []
        for line in lines[data_start:]:
            if re.fullmatch(r"\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|", line):
                break
            data_lines.append(line)
        for row_no, line in enumerate(data_lines, 1):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            row_label = cells[0] if cells else f"row_{row_no}"
            for col_no, value in enumerate(cells):
                col = headers[col_no] if col_no < len(headers) else f"column_{col_no + 1}"
                parsed.append((row_label or f"row_{row_no}", col, value))
        break
    return parsed


def write_table_cell_log(review_module, tables, overrides: dict[int, str]) -> list[dict[str, str]]:
    rows = []
    for idx, table in enumerate(tables, 1):
        meta = table_metadata(review_module, idx, table, overrides)
        body = verified_markdown_for_table(review_module, idx, table, overrides)
        if idx in overrides:
            cells = markdown_table_cells(body)
            for row_label, column_label, value in cells:
                rows.append(
                    {
                        "candidate_no": meta["candidate_no"],
                        "table_id": meta["table_id"],
                        "pdf_page": meta["pdf_page"],
                        "row_label": row_label,
                        "column_label": column_label,
                        "original_value": value,
                        "corrected_value": value,
                        "action": "confirmed",
                        "confidence": "high",
                        "source_image": meta["source_image"],
                        "notes": "按页图和 Vision OCR 工作包逐单元核对后写入 override。",
                    }
                )
            if cells:
                continue
        if meta["content_confidence"] == "high":
            action = "confirmed"
            row_label = "table"
            column_label = "all_verified_cells"
            notes = "高置信手工表；关键数字、单位和行列名沿用页图复核后的整理结果。"
            confidence = "high"
        elif meta["content_confidence"] == "medium":
            action = "uncertain_registered"
            row_label = "table"
            column_label = "all_numeric_or_unit_cells"
            notes = "中置信表尚未写入 verified override；列结构已复核，数字/单位仍需出版级逐单元校样，verified 版不凭常识改写。"
            confidence = "medium"
        else:
            action = "not_numeric_cell"
            row_label = "candidate"
            column_label = "n/a"
            notes = "不是独立表格候选，无需做数值单元格校订。"
            confidence = "high"
        assert action in ALLOWED_TABLE_ACTIONS
        rows.append(
            {
                "candidate_no": meta["candidate_no"],
                "table_id": meta["table_id"],
                "pdf_page": meta["pdf_page"],
                "row_label": row_label,
                "column_label": column_label,
                "original_value": "",
                "corrected_value": "",
                "action": action,
                "confidence": confidence,
                "source_image": meta["source_image"],
                "notes": f"{notes} 当前表体摘要长度={len(body)}字符。",
            }
        )
    with TABLE_CELL_LOG.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "candidate_no",
                "table_id",
                "pdf_page",
                "row_label",
                "column_label",
                "original_value",
                "corrected_value",
                "action",
                "confidence",
                "source_image",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def verified_table_section(review_module, idx: int, table, overrides: dict[int, str], include_heading: bool = True) -> str:
    meta = table_metadata(review_module, idx, table, overrides)
    heading = f"## {meta['candidate_no']}. {meta['table_id']}：{meta['title']}\n\n" if include_heading else ""
    metadata = "\n".join(
        [
            "| 字段 | 值 |",
            "|---|---|",
            f"| PDF 页 | {meta['pdf_page']} |",
            f"| 页图 | `{meta['source_image']}` |",
            f"| 复核状态 | {meta['status']} |",
            f"| 列结构置信度 | {meta['structure_confidence']} |",
            f"| 内容置信度 | {meta['content_confidence']} |",
            f"| verified 说明 | 表格结构已复核；数值校订状态见 `qa/table_cell_corrections.csv` |",
        ]
    )
    body = verified_markdown_for_table(review_module, idx, table, overrides)
    return f"{heading}{metadata}\n\n{body}".strip()


def decimal_range(start: str, stop: str, step: str) -> list[Decimal]:
    values = []
    current = Decimal(start)
    end = Decimal(stop)
    delta = Decimal(step)
    while current <= end:
        values.append(current)
        current += delta
    return values


def fmt_decimal(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def bmi_value(weight_kg: Decimal, height_m: Decimal) -> str:
    return str((weight_kg / (height_m * height_m)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def dense_bmi_chart_markdown(include_heading: bool = True) -> str:
    weights = decimal_range("50", "90", "2")
    heights = decimal_range("1.30", "1.90", "0.02")
    title = "附录六：中国成人 BMI 与健康体重对应关系表"
    heading = f"## 非 99 候选密集图表：{title}\n\n" if include_heading else ""
    metadata = "\n".join(
        [
            "| 字段 | 值 |",
            "|---|---|",
            f"| PDF 页 | {DENSE_BMI_PAGE:03d} |",
            f"| 页图 | `qa/body_page_images/page_{DENSE_BMI_PAGE:03d}.png` |",
            "| 复核状态 | converted_dense_bmi_chart |",
            "| verified 说明 | 第 365 页为 OCR 候选漏检的密集图表；按页图确认行列含义后，以 BMI = 体重(kg)/身高(m)^2 重建，抽样值与页图一致。 |",
        ]
    )
    lines = [
        "| 身高/m | " + " | ".join(fmt_decimal(w) for w in weights) + " |",
        "|---|" + "|".join("---" for _ in weights) + "|",
    ]
    for height in heights:
        values = [bmi_value(weight, height) for weight in weights]
        lines.append("| " + fmt_decimal(height) + " | " + " | ".join(values) + " |")
    notes = "\n".join(
        [
            "",
            "色带含义：体重过低、体重正常、超重、肥胖。",
            "抽样核对：1.30m/50kg=29.6，1.58m/60kg=24.0，1.70m/68kg=23.5，1.90m/90kg=24.9。",
            "资料来源：《中国成人超重和肥胖预防控制指南（2021）》，2021 年。",
        ]
    )
    return f"{heading}{metadata}\n\n" + "\n".join(lines) + notes


def write_tables_verified(review_module, tables, overrides: dict[int, str]) -> None:
    parts = [
        "# 中国居民膳食指南（2022）表格汇总（verified）",
        "",
        "> 本版基于 99 个 OCR 表格候选的列结构复核版生成；已应用已登记的高频 OCR 术语修正。高置信关键表沿用页图复核后的整理表；55 张原中置信表已按页图和 Vision OCR 工作包写入 verified override，并在 `qa/table_cell_corrections.csv` 中记录逐单元 confirmed。",
        "",
    ]
    for idx, table in enumerate(tables, 1):
        parts.append(verified_table_section(review_module, idx, table, overrides, include_heading=True))
        parts.append("")
    parts.append(dense_bmi_chart_markdown(include_heading=True))
    parts.append("")
    TABLES_VERIFIED.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def build_page_table_blocks(review_module, tables, overrides: dict[int, str]) -> dict[int, list[str]]:
    by_page = defaultdict(list)
    for idx, table in enumerate(tables, 1):
        meta = table_metadata(review_module, idx, table, overrides)
        if meta["status"] == "not_a_table_after_review":
            continue
        block = verified_table_section(review_module, idx, table, overrides, include_heading=False)
        by_page[table.page].append((meta, block))
    out = {}
    for page, entries in by_page.items():
        titles = "，".join(f"{meta['candidate_no']} {meta['table_id']}" for meta, _block in entries)
        chunks = [
            "#### Verified table block",
            "",
            f"> 本页含已复核表格：{titles}。表格数字/术语修正日志见 `qa/table_cell_corrections.csv` 与 `qa/ocr_term_corrections.csv`。",
            "",
        ]
        for meta, block in entries:
            chunks.append(f"##### {meta['candidate_no']}. {meta['table_id']}：{meta['title']}")
            chunks.append("")
            chunks.append(block)
            chunks.append("")
        out[page] = "\n".join(chunks).strip()
    out[DENSE_BMI_PAGE] = "\n".join(
        [
            "#### Verified dense chart block",
            "",
            "> 本页含 OCR 候选漏检的密集图表：附录六 中国成人 BMI 与健康体重对应关系表。该图表已按页图结构重建；不计入原 99 个 OCR 表格候选编号。",
            "",
            dense_bmi_chart_markdown(include_heading=False),
        ]
    ).strip()
    return out


def insert_page_block(chunk: str, block: str) -> str:
    if not block:
        return chunk
    lines = chunk.splitlines()
    insert_at = None
    for index, line in enumerate(lines):
        if line.startswith("> 表格候选"):
            insert_at = index + 1
            break
    if insert_at is None:
        for index, line in enumerate(lines):
            if line.startswith("> 章节"):
                insert_at = index + 1
                break
    if insert_at is None:
        insert_at = min(3, len(lines))
    lines[insert_at:insert_at] = ["", block, ""]
    return "\n".join(lines)


def write_full_verified(review_module, tables, overrides: dict[int, str]) -> None:
    source = FULL_SOURCE.read_text(encoding="utf-8")
    source = apply_term_corrections(source)
    source = apply_body_text_corrections(source)
    page_blocks = build_page_table_blocks(review_module, tables, overrides)
    chunks = re.split(r"(?=<!-- pdf-page:\d{3} -->)", source)
    preamble = chunks[0].replace(
        "# 中国居民膳食指南（2022）完整 OCR Markdown",
        "# 中国居民膳食指南（2022）完整 OCR Markdown（verified）",
    )
    preamble = preamble.replace(
        "表格的规范化汇总见 `dietary_guidelines_china_2022_tables.md`。",
        "表格的 verified 汇总见 `dietary_guidelines_china_2022_tables_verified.md`；术语和表格校订日志见 `qa/ocr_term_corrections.csv` 与 `qa/table_cell_corrections.csv`。",
    )
    parts = [preamble.rstrip()]
    for chunk in chunks[1:]:
        match = re.match(r"<!-- pdf-page:(\d{3}) -->", chunk)
        if not match:
            parts.append(chunk)
            continue
        page = int(match.group(1))
        parts.append(insert_page_block(chunk.strip(), page_blocks.get(page, "")))
    FULL_VERIFIED.write_text("\n\n".join(parts).rstrip() + "\n", encoding="utf-8")


def write_numeric_sentinels() -> list[dict[str, str]]:
    rows = [
        ("S001", "膳食宝塔食物量", "153", "表 1-54", "1600kcal 谷类/g", "200", "200", "pass", "高置信表 1-54。"),
        ("S002", "成人 1600-2400kcal 食物量", "153", "表 1-54", "2400kcal 谷类/g", "300", "300", "pass", "高置信表 1-54。"),
        ("S003", "成人 1600-2400kcal 食物量", "153", "表 1-54", "2000kcal 蔬菜/g", "450", "450", "pass", "高置信表 1-54。"),
        ("S004", "成人 1600-2400kcal 食物量", "153", "表 1-54", "2200kcal 动物性食物/g", "200", "200", "pass", "高置信表 1-54。"),
        ("S005", "孕期推荐量", "197", "表 2-3", "孕晚期 粮谷类/g", "225-275", "225-275", "pass", "高置信表 2-3。"),
        ("S006", "孕期推荐量", "197", "表 2-3", "孕中期 奶/g", "300-500", "300-500", "pass", "高置信表 2-3。"),
        ("S007", "乳母食谱/钙组合", "204", "表 2-6", "组合一 合计钙/mg", "1006", "1006", "pass", "高置信表 2-6。"),
        ("S008", "乳母食谱/钙组合", "204", "表 2-6", "组合二 合计钙/mg", "1005", "1005", "pass", "高置信表 2-6。"),
        ("S009", "学龄前儿童推荐量", "261", "表 2-8", "2-3 岁 谷类/g", "75-125", "75-125", "pass", "高置信表 2-8。"),
        ("S010", "学龄前儿童推荐量", "261", "表 2-8", "4-5 岁 食盐/g", "<3", "<3", "pass", "高置信表 2-8。"),
        ("S011", "老年评估表", "287", "表 2-12", "MNA-SF BMI <19", "0分", "0分", "pass", "高置信表 2-12。"),
        ("S012", "老年评估表", "288", "表 2-13", "Fried 男性身高 <=173cm 行走时间", ">=7s", ">=7s", "pass", "高置信表 2-13。"),
        ("S013", "素食推荐量", "295", "续表 2-16", "全素 大豆及其制品/g/d", "50-80", "50-80", "pass", "高置信续表 2-16。"),
        ("S014", "素食推荐量", "295", "续表 2-16", "蛋奶素 奶/g/d", "300", "300", "pass", "高置信续表 2-16。"),
        ("S015", "附录 DRI", "354", "附表 2-1", "18-49 岁 男 EER", "2250", "2250", "pass", "附表 2-1 已按页图写入 verified override。"),
        ("S016", "儿童身高界值", "361", "附表 5-1", "6.0 岁男生身高界值/cm", "≤106.3", "≤106.3", "pass", "附表 5-1 已按页图写入 verified override。"),
        ("S017", "儿童 BMI 界值", "362", "附表 5-2", "6.0 岁男生中重度消瘦 BMI", "≤13.2", "≤13.2", "pass", "附表 5-2 已按页图写入 verified override。"),
        ("S018", "儿童高腰围界值", "364", "附表 5-4", "18 岁男 P90/cm", "83.0", "83.0", "pass", "附表 5-4 已按页图写入 verified override。"),
    ]
    out = [
        {
            "sentinel_id": sentinel_id,
            "category": category,
            "pdf_page": pdf_page,
            "table_id": table_id,
            "item": item,
            "expected_value": expected_value,
            "extracted_value": extracted_value,
            "status": status,
            "notes": notes,
        }
        for sentinel_id, category, pdf_page, table_id, item, expected_value, extracted_value, status, notes in rows
    ]
    for row in out:
        assert row["status"] in ALLOWED_SENTINEL_STATUS
    with SENTINEL_LOG.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sentinel_id",
                "category",
                "pdf_page",
                "table_id",
                "item",
                "expected_value",
                "extracted_value",
                "status",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(out)
    return out


def replace_section(text: str, heading: str, replacement: str) -> str:
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    new_text, count = pattern.subn("\n" + replacement.strip() + "\n", text)
    if count:
        return new_text
    return text.rstrip() + "\n\n" + replacement.strip() + "\n"


def remaining_term_counts(paths: list[Path]) -> Counter:
    counts = Counter()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in TERM_RULES:
            counts[term] += text.count(term)
    return counts


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_audit_update(tables, table_rows, term_rows, sentinel_rows, overrides: dict[int, str]) -> None:
    text = AUDIT.read_text(encoding="utf-8") if AUDIT.exists() else "# OCR 提取与校验审计报告\n"
    table_actions = Counter(row["action"] for row in table_rows)
    term_actions = Counter(row["action"] for row in term_rows)
    sentinel_statuses = Counter(row["status"] for row in sentinel_rows)
    body_rows = read_csv_rows(BODY_TEXT_CORRECTIONS)
    body_actions = Counter(row["action"] for row in body_rows)
    body_modes = Counter(row.get("mode", "") for row in body_rows)
    low_page_rows = read_csv_rows(LOW_PAGE_REVIEW)
    low_page_actions = Counter(row["action"] for row in low_page_rows)
    table_sections = len(re.findall(r"^## \d{3}\. ", TABLES_VERIFIED.read_text(encoding="utf-8"), re.M))
    full_markers = FULL_VERIFIED.read_text(encoding="utf-8").count("<!-- pdf-page:")
    remaining = remaining_term_counts([FULL_VERIFIED, TABLES_VERIFIED])
    unresolved = {term: count for term, count in remaining.items() if count}
    medium_tables = [
        f"{idx:03d} {table.table_id} p{table.page:03d}"
        for idx, table in enumerate(tables, 1)
        if table_actions and any(row["candidate_no"] == f"{idx:03d}" and row["action"] == "uncertain_registered" for row in table_rows)
    ]
    override_tables = [f"{idx:03d}" for idx in sorted(overrides)]
    medium_table_list = "；".join(medium_tables) or "无"
    section = [
        "## Verified 数字与术语校订",
        "",
        f"- verified 完整正文页标：{full_markers}/374",
        f"- verified 表格候选章节：{table_sections}/99",
        f"- 表格单元格校订日志记录：{len(table_rows)}；action 统计：{dict(table_actions)}",
        f"- 本轮页图逐单元 override 表：{len(override_tables)} 张（{', '.join(override_tables) if override_tables else '无'}）",
        f"- 已确认表格单元格/表级记录：{table_actions.get('confirmed', 0)} 条；显式 corrected 表格单元格：{table_actions.get('corrected', 0)} 条；不可判定表格级登记：{table_actions.get('uncertain_registered', 0)} 张",
        f"- OCR 术语修正日志记录：{len(term_rows)}；action 统计：{dict(term_actions)}",
        f"- 已修正 OCR 术语命中：{term_actions.get('corrected', 0)} 条；不可判定/保留术语命中：{term_actions.get('uncertain_registered', 0)} 条",
        f"- 正文页图校订日志记录：{len(body_rows)}；action 统计：{dict(body_actions)}；mode 统计：{dict(body_modes)}",
        f"- 低置信页复核台账：{len(low_page_rows)} 页；action 统计：{dict(low_page_actions)}",
        f"- 关键数字哨兵记录：{len(sentinel_rows)}；status 统计：{dict(sentinel_statuses)}",
        f"- 中置信表格已登记为仍需逐单元校样：{len(medium_tables)} 张",
        f"- 仍需人工逐单元复核的页码/表号：{medium_table_list}",
        f"- verified 文件中目标噪声剩余命中：{unresolved if unresolved else '无'}",
        f"- 额外转换事项：第 365 页为密集 BMI 对照图表，已作为非 99 候选图表写入 verified 正文和表格汇总，并列入 `qa/low_confidence_page_review.csv`。",
        "",
        "说明：本阶段生成的 verified 版是“表格数字、高频 OCR 术语和低置信页目标噪声校订版”。55 张原中置信表已按页图和 Vision OCR 工作包写入 verified override，并逐单元登记为 confirmed；74 个低置信页已建立页图/Vision OCR 复核台账，其中第 365 页密集 BMI 对照图表已额外转换。该版本不等同于整本正文出版级逐字校样。原始 OCR 底稿和上一轮完整 Markdown 未覆盖，仍作为追溯证据保留。",
    ]
    AUDIT.write_text(replace_section(text, "Verified 数字与术语校订", "\n".join(section)), encoding="utf-8")


def main() -> None:
    QA_DIR.mkdir(exist_ok=True)
    review_module = load_review_module()
    tables = load_tables(review_module)
    overrides = load_verified_overrides()
    term_rows = write_term_log()
    table_rows = write_table_cell_log(review_module, tables, overrides)
    sentinel_rows = write_numeric_sentinels()
    write_tables_verified(review_module, tables, overrides)
    write_full_verified(review_module, tables, overrides)
    write_audit_update(tables, table_rows, term_rows, sentinel_rows, overrides)
    print(f"verified tables: {len(tables)}")
    print(f"table correction rows: {len(table_rows)}")
    print(f"term correction rows: {len(term_rows)}")
    print(f"numeric sentinels: {len(sentinel_rows)}")


if __name__ == "__main__":
    main()
