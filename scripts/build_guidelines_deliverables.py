#!/usr/bin/env python3
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


PAGE_COUNT = 374
OCR_DIR = Path("ocr_text_v2")
QA_DIR = Path("qa")

NOISE_TERMS = [
    "腾食",
    "摄和",
    "报信",
    "公策",
    "鼠烟",
    "训调",
    "豪调",
    "kgjm",
    "R216",
    "BERE",
]

SECTION_STARTS = [
    ("第一部分", re.compile(r"第一部分|一般人群膳食指南")),
    ("准则一 食物多样，合理搭配", re.compile(r"准则一.*食物多样")),
    ("准则二 吃动平衡，健康体重", re.compile(r"准则二.*吃动平衡")),
    ("准则三 多吃蔬果、奶类、全谷、大豆", re.compile(r"准则三.*多吃蔬果")),
    ("准则四 适量吃鱼、禽、蛋、瘦肉", re.compile(r"准则四.*适量吃鱼")),
    ("准则五 少盐少油，控糖限酒", re.compile(r"准则五.*少盐少油")),
    ("准则六 规律进餐，足量饮水", re.compile(r"准则六.*规律进餐")),
    ("准则七 会烹会选，会看标签", re.compile(r"准则七.*会.*会看标签")),
    ("准则八 公筷分餐，杜绝浪费", re.compile(r"准则八.*分餐.*浪费")),
    ("第二部分 特定人群膳食指南", re.compile(r"第二部分|特定人群膳食指南")),
    ("孕妇、乳母膳食指南", re.compile(r"孕妇、乳母膳食指南")),
    ("0-6 月龄婴儿母乳喂养指南", re.compile(r"0~6 月龄婴儿|0-6 月龄婴儿|6 月龄内婴儿")),
    ("7-24 月龄婴幼儿喂养指南", re.compile(r"7~24 月龄婴幼儿|7-24 月龄婴幼儿")),
    ("儿童膳食指南", re.compile(r"儿童膳食指南|学龄前儿童膳食指南|学龄儿童膳食指南")),
    ("老年人膳食指南", re.compile(r"老年人膳食指南|一般老年人膳食指南|高龄老年人")),
    ("素食人群膳食指南", re.compile(r"素食人群.*膳食指南")),
    ("第三部分 平衡膳食模式和编写说明", re.compile(r"第三部分|平衡.*膳食模式")),
    ("附录", re.compile(r"附录一|附录二|附录三|附录四|附录五|附录六")),
    ("参考文献", re.compile(r"参考文献")),
]

PAGE_SECTION_RANGES = [
    (1, 4, "封面、版权和可视化图示"),
    (5, 8, "前言与编写说明"),
    (9, 13, "平衡膳食准则概览与目录"),
    (14, 16, "第一部分 一般人群膳食指南"),
    (17, 40, "准则一 食物多样，合理搭配"),
    (41, 60, "准则二 吃动平衡，健康体重"),
    (61, 88, "准则三 多吃蔬果、奶类、全谷、大豆"),
    (89, 107, "准则四 适量吃鱼、禽、蛋、瘦肉"),
    (108, 129, "准则五 少盐少油，控糖限酒"),
    (130, 151, "准则六 规律进餐，足量饮水"),
    (152, 167, "准则七 会烹会选，会看标签"),
    (168, 190, "准则八 公筷分餐，杜绝浪费"),
    (191, 199, "备孕和孕期妇女膳食指南"),
    (200, 207, "哺乳期妇女膳食指南"),
    (208, 232, "0-6 月龄婴儿母乳喂养指南"),
    (233, 258, "7-24 月龄婴幼儿喂养指南"),
    (259, 265, "学龄前儿童膳食指南"),
    (266, 275, "学龄儿童膳食指南"),
    (276, 283, "一般老年人膳食指南"),
    (284, 292, "高龄老年人膳食指南"),
    (293, 303, "素食人群膳食指南"),
    (304, 346, "第三部分 平衡膳食模式和编写说明"),
    (347, 353, "附录一 常见食物的份量"),
    (354, 356, "附录二 膳食营养素参考摄入量"),
    (357, 360, "附录三至附录四"),
    (361, 364, "附录五 儿童青少年体格发育标准"),
    (365, 365, "附录六 成人 BMI 与健康体重对应关系"),
    (366, 374, "主要参考文献"),
]

TABLE_LINE_RE = re.compile(
    r"(?P<title>(?:附表|表)\s*[0-9一二三四五六七八九十]+(?:\s*[-.－—]\s*[0-9一二三四五六七八九十]+)?[^\n]{0,90})"
)


@dataclass
class TableCandidate:
    table_id: str
    title: str
    page: int
    line_index: int
    status: str
    verified: bool
    block: list[str]


def page_path(page: int) -> Path:
    return OCR_DIR / f"page_{page:03d}.txt"


def read_pages() -> dict[int, str]:
    pages = {}
    for page in range(1, PAGE_COUNT + 1):
        path = page_path(page)
        pages[page] = path.read_text(encoding="utf-8") if path.exists() else ""
    return pages


def clean_line(line: str) -> str:
    line = line.rstrip()
    line = re.sub(r"[ \t]{3,}", "  ", line)
    return line


def normalize_table_id(title: str) -> str:
    m = re.search(r"(附表|表)\s*([0-9一二三四五六七八九十]+)\s*[-.－—]?\s*([0-9一二三四五六七八九十]+)?", title)
    if not m:
        return re.sub(r"\s+", " ", title.strip())[:40]
    prefix, a, b = m.group(1), m.group(2), m.group(3)
    if b:
        return f"{prefix} {a}-{b}"
    return f"{prefix} {a}"


def is_table_title(line: str) -> bool:
    stripped = line.strip()
    if "续表" in stripped:
        return True
    match = TABLE_LINE_RE.search(stripped)
    if not match:
        return False
    prefix = stripped[: match.start()]
    if "见表" in prefix or "参见表" in prefix:
        return False
    if match.start() > 12:
        return False
    if re.search(r"[\u4e00-\u9fffA-Za-z0-9]{3,}", prefix):
        return False
    return True


def extract_tables(pages: dict[int, str]) -> list[TableCandidate]:
    seen = Counter()
    candidates = []
    for page, text in pages.items():
        lines = [clean_line(x) for x in text.splitlines()]
        for i, line in enumerate(lines):
            if "续表" in line and candidates:
                prev = candidates[-1]
                title = f"续表（接 {prev.table_id}）"
                table_id = prev.table_id
            else:
                if not is_table_title(line):
                    continue
                match = TABLE_LINE_RE.search(line)
                if not match:
                    continue
                title = re.sub(r"\s+", " ", match.group("title").strip(" |"))
                table_id = normalize_table_id(title)
            if len(title) < 4:
                continue
            seen[table_id] += 1
            status = "converted" if seen[table_id] == 1 else "merged_continuation"
            block = []
            for raw in lines[i : min(len(lines), i + 32)]:
                if raw.strip():
                    if block and is_table_title(raw) and raw != line and "续表" not in raw:
                        break
                    block.append(raw.strip(" |"))
            verified = table_id in NORMALIZED_TABLES
            candidates.append(TableCandidate(table_id, title, page, i, status, verified, block))
    return candidates


def detect_sections(pages: dict[int, str]) -> dict[int, str]:
    sections = {}
    for page in range(1, PAGE_COUNT + 1):
        section = "未分类"
        for start, end, name in PAGE_SECTION_RANGES:
            if start <= page <= end:
                section = name
                break
        sections[page] = section
    return sections


def confidence_for(text: str) -> str:
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return "low"
    noise = sum(stripped.count(term) for term in NOISE_TERMS)
    ratio = noise / max(len(stripped), 1)
    ascii_ratio = sum(1 for c in stripped if c.isascii()) / max(len(stripped), 1)
    if len(stripped) < 20 or ratio > 0.01 or ascii_ratio > 0.55:
        return "low"
    if ratio > 0.003 or ascii_ratio > 0.35:
        return "medium"
    return "high"


def line_table(block: list[str]) -> str:
    rows = ["| OCR 行 | 内容 |", "|---:|---|"]
    for idx, line in enumerate(block, 1):
        safe = line.replace("|", "\\|").strip()
        rows.append(f"| {idx} | {safe} |")
    return "\n".join(rows)


NORMALIZED_TABLES = {
    "表 1-54": """| 食物种类 | 1600 kcal | 1800 kcal | 2000 kcal | 2200 kcal | 2400 kcal |
|---|---:|---:|---:|---:|---:|
| 谷类/g | 200 | 225 | 250 | 275 | 300 |
| 其中全谷物和杂豆/g，薯类/g | 50-150；50-100 | 50-150；50-100 | 50-150；50-100 | 50-150；50-100 | 50-150；50-100 |
| 蔬菜/g | 300 | 400 | 450 | 450 | 500 |
| 其中深色蔬菜 | 占 1/2 | 占 1/2 | 占 1/2 | 占 1/2 | 占 1/2 |
| 水果/g | 200 | 200 | 300 | 300 | 350 |
| 动物性食物/g | 120 | 140 | 150 | 200 | 200 |
| 其中畜禽肉类/g | 40 | 50 | 50 | 75 | 75 |
| 其中蛋类/g | 40 | 40 | 50 | 50 | 50 |
| 其中水产品/g | 40 | 50 | 50 | 75 | 75 |
| 乳制品/g | 300 | 300-500 | 300-500 | 300-500 | 300-500 |
| 大豆及坚果类/g | 25 | 25 | 25 | 35 | 35 |
| 油盐类/g | 油 25-30，盐 <5 | 油 25-30，盐 <5 | 油 25-30，盐 <5 | 油 25-30，盐 <5 | 油 25-30，盐 <5 |""",
    "表 2-3": """| 食物种类 | 备孕/孕早期 | 孕中期 | 孕晚期 |
|---|---:|---:|---:|
| 粮谷类/g | 200-250 | 200-250 | 225-275 |
| 薯类/g | 50 | 75 | 75 |
| 蔬菜类/g | 300-500 | 400-500 | 400-500 |
| 水果类/g | 200-300 | 200-300 | 200-350 |
| 鱼、禽、蛋、肉（含动物内脏）/g | 130-180 | 150-200 | 175-225 |
| 奶/g | 300 | 300-500 | 300-500 |
| 大豆/g | 15 | 20 | 20 |
| 坚果/g | 10 | 10 | 10 |
| 烹调油/g | 25 | 25 | 25 |
| 加碘食盐/g | 5 | 5 | 5 |
| 饮水量 | 1500/1700 ml | 1700 ml | 1700 ml |""",
    "表 2-8": """| 食物种类 | 2-3 岁 | 4-5 岁 |
|---|---:|---:|
| 谷类/g | 75-125 | 100-150 |
| 薯类/g | 适量 | 适量 |
| 蔬菜/g | 100-200 | 150-300 |
| 水果/g | 100-200 | 150-250 |
| 畜禽鱼肉/g | 50-75 | 50-75 |
| 蛋类/g | 50 | 50 |
| 奶类/g | 350-500 | 350-500 |
| 大豆/g | 5-15 | 15-20 |
| 坚果/g | 适量 | 适量 |
| 烹调油/g | 10-20 | 20-25 |
| 食盐/g | <2 | <3 |
| 饮水量/ml | 600-700 | 700-800 |""",
    "表 2-16": """| 食物种类 | 全素 | 蛋奶素 |
|---|---:|---:|
| 谷类/g | 250-400 | 225-350 |
| 其中全谷物和杂豆/g | 120-200 | 100-150 |
| 薯类/g | 50-125 | 50-125 |
| 蔬菜/g | 300-500 | 300-500 |
| 其中菌藻类/g | 5-10 | 5-10 |
| 水果/g | 200-350 | 200-350 |
| 大豆及其制品/g | 50-80 | 25-60 |
| 其中发酵豆制品/g | 5-10 | - |
| 坚果/g | 20-30 | 15-25 |
| 烹调油/g | 20-30 | 20-30 |
| 奶/g | - | 300 |
| 蛋/g | - | 40-50 |
| 食盐/g | 5 | 5 |""",
}


def write_full_markdown(pages, sections, by_page):
    out = Path("dietary_guidelines_china_2022_full.md")
    parts = [
        "# 中国居民膳食指南（2022）完整 OCR Markdown\n",
        "> 来源：`1711104221187059.pdf`。原 PDF 为 374 页扫描版，无可抽取文本层。本文件按 PDF 页序保留 OCR 文字，并用 `pdf-page` 标记提供追溯。表格的规范化汇总见 `dietary_guidelines_china_2022_tables.md`。\n",
    ]
    last_section = None
    for page in range(1, PAGE_COUNT + 1):
        section = sections[page]
        if section != last_section:
            parts.append(f"\n## {section}\n")
            last_section = section
        table_ids = ", ".join(t.table_id for t in by_page.get(page, []))
        parts.append(f"\n<!-- pdf-page:{page:03d} -->\n\n")
        parts.append(f"### PDF 第 {page:03d} 页\n\n")
        parts.append(f"> 章节：{section}\n")
        if table_ids:
            parts.append(f"> 表格候选：{table_ids}\n")
        text = "\n".join(clean_line(line) for line in pages[page].splitlines()).strip()
        if text:
            parts.append("\n" + text + "\n")
        else:
            parts.append("\n[OCR 未识别到可读文字；该页可能为空白页、纯图片页或装饰页。]\n")
    out.write_text("\n".join(parts), encoding="utf-8")


def write_tables_markdown(tables):
    out = Path("dietary_guidelines_china_2022_tables.md")
    parts = [
        "# 中国居民膳食指南（2022）表格汇总\n",
        "> 表格来自 `ocr_text_v2`。`verified=true` 的表格为关键推荐量表，已按渲染页图/既有核对结果规范化；其他表格为 OCR 行级 Markdown 转写，保留原识别行以便继续人工校对。\n",
    ]
    for idx, table in enumerate(tables, 1):
        parts.append(f"\n## {table.table_id}：{table.title}\n")
        parts.append(
            "\n".join(
                [
                    "| 字段 | 值 |",
                    "|---|---|",
                    f"| PDF 页 | {table.page:03d} |",
                    f"| 状态 | {table.status} |",
                    f"| verified | {str(table.verified).lower()} |",
                ]
            )
        )
        parts.append("")
        if table.table_id in NORMALIZED_TABLES:
            parts.append(NORMALIZED_TABLES[table.table_id])
        else:
            parts.append(line_table(table.block))
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_csvs(pages, sections, tables, by_page):
    QA_DIR.mkdir(exist_ok=True)
    with (QA_DIR / "page_status.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["pdf_page", "section", "has_text", "has_table", "table_ids", "confidence", "notes"],
        )
        writer.writeheader()
        for page in range(1, PAGE_COUNT + 1):
            text = pages[page]
            stripped = re.sub(r"\s+", "", text)
            page_tables = by_page.get(page, [])
            notes = []
            for term in NOISE_TERMS:
                count = text.count(term)
                if count:
                    notes.append(f"{term}:{count}")
            if not stripped:
                notes.append("empty_or_image_only")
            writer.writerow(
                {
                    "pdf_page": f"{page:03d}",
                    "section": sections[page],
                    "has_text": bool(stripped),
                    "has_table": bool(page_tables),
                    "table_ids": ";".join(t.table_id for t in page_tables),
                    "confidence": confidence_for(text),
                    "notes": ";".join(notes),
                }
            )
    with (QA_DIR / "table_index.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["table_id", "title", "pdf_page_start", "pdf_page_end", "status", "verified"],
        )
        writer.writeheader()
        for t in tables:
            writer.writerow(
                {
                    "table_id": t.table_id,
                    "title": t.title,
                    "pdf_page_start": f"{t.page:03d}",
                    "pdf_page_end": f"{t.page:03d}",
                    "status": t.status,
                    "verified": str(t.verified).lower(),
                }
            )


def write_verified_key():
    src = Path("dietary_guidelines_china_2022_key_content.md")
    text = src.read_text(encoding="utf-8") if src.exists() else ""
    replacements = {
        "# 中国居民膳食指南（2022）关键内容整理": "# 中国居民膳食指南（2022）关键内容整理（带页码核验版）",
        "## 2. 平衡膳食准则八条": "## 2. 平衡膳食准则八条\n\n来源页：PDF 第 009-011 页；详细准则正文见 PDF 第 017-178 页。",
        "## 3. 中国居民平衡膳食宝塔（2022）": "## 3. 中国居民平衡膳食宝塔（2022）\n\n来源页：PDF 第 003 页；成人不同能量水平食物量见 PDF 第 153 页。",
        "### 3.1 不同能量水平下的成人食物量": "### 3.1 不同能量水平下的成人食物量\n\n来源页：PDF 第 153 页。",
        "## 4. 一般人群关键量化建议": "## 4. 一般人群关键量化建议\n\n来源页：PDF 第 009-011、018、042、062、090、109、130、153 页。",
        "### 5.1 备孕和孕期妇女": "### 5.1 备孕和孕期妇女\n\n来源页：PDF 第 192、197 页。",
        "### 5.2 哺乳期妇女": "### 5.2 哺乳期妇女\n\n来源页：PDF 第 200、202-203 页。",
        "### 5.3 0-6 月龄婴儿": "### 5.3 0-6 月龄婴儿\n\n来源页：PDF 第 210、212、230 页。",
        "### 5.4 7-24 月龄婴幼儿": "### 5.4 7-24 月龄婴幼儿\n\n来源页：PDF 第 239、244、248、252、255 页。",
        "### 5.5 学龄前儿童（2-5 岁）": "### 5.5 学龄前儿童（2-5 岁）\n\n来源页：PDF 第 260-261 页。",
        "### 5.6 学龄儿童（6-17 岁）": "### 5.6 学龄儿童（6-17 岁）\n\n来源页：PDF 第 266-267 页。",
        "### 5.7 老年人": "### 5.7 老年人\n\n来源页：PDF 第 277-284 页。",
        "### 5.8 素食人群": "### 5.8 素食人群\n\n来源页：PDF 第 294-299 页。",
        "## 6. 可直接使用的速查表": "## 6. 可直接使用的速查表\n\n来源页：PDF 第 003、009-011、153 页。",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace(
        "> 来源：本目录 PDF `1711104221187059.pdf`。原 PDF 无文本层，本文件由中文 OCR 底稿整理而成；关键数值表已结合渲染页图复核。本文是关键内容提取版，不是 374 页全量逐字转写。",
        "> 来源：本目录 PDF `1711104221187059.pdf`。原 PDF 无文本层，本文件由 OCR v2 底稿和关键页复核整理而成；本文件仍是关键内容提取版，完整页序正文见 `dietary_guidelines_china_2022_full.md`。",
    )
    Path("dietary_guidelines_china_2022_key_content_verified.md").write_text(text, encoding="utf-8")


def write_audit(pages, tables, by_page):
    marker_count = Path("dietary_guidelines_china_2022_full.md").read_text(encoding="utf-8").count("<!-- pdf-page:")
    confidence_counts = Counter(confidence_for(text) for text in pages.values())
    noise_counts = Counter()
    for text in pages.values():
        for term in NOISE_TERMS:
            noise_counts[term] += text.count(term)
    empty_pages = [p for p, text in pages.items() if not re.sub(r"\s+", "", text)]
    low_pages = [p for p, text in pages.items() if confidence_for(text) == "low"]
    sampled_pages = list(range(1, PAGE_COUNT + 1, 20))
    verified_tables = sorted({t.table_id for t in tables if t.verified})

    lines = [
        "# OCR 提取与校验审计报告",
        "",
        "## 输入与 OCR 设置",
        "",
        "- 输入 PDF：`1711104221187059.pdf`",
        "- PDF 页数：374",
        "- PDF 文本层：无，按扫描图片处理",
        "- OCR 输出目录：`ocr_text_v2/`",
        "- 渲染工具：Poppler `pdftoppm`",
        "- 渲染分辨率：220 DPI",
        "- OCR 工具：Tesseract",
        "- OCR 语言：`chi_sim+eng`",
        "",
        "## 覆盖率",
        "",
        f"- `dietary_guidelines_china_2022_full.md` 页标数量：{marker_count}/374",
        f"- OCR 分页文件数量：{len(list(OCR_DIR.glob('page_*.txt')))}/374",
        f"- 空白或纯图片页：{', '.join(f'{p:03d}' for p in empty_pages) if empty_pages else '无'}",
        "",
        "## 表格台账",
        "",
        f"- 表格候选总数：{len(tables)}",
        f"- 已规范化关键表格：{len(verified_tables)}（{', '.join(verified_tables) if verified_tables else '无'}）",
        "- 其余表格为 OCR 行级 Markdown 转写，已进入 `dietary_guidelines_china_2022_tables.md` 和 `qa/table_index.csv`，需继续人工逐列复核。",
        "",
        "## 置信度与噪声",
        "",
        f"- 页面置信度统计：{dict(confidence_counts)}",
        f"- low 置信页数量：{len(low_pages)}",
        f"- low 置信页示例：{', '.join(f'{p:03d}' for p in low_pages[:40])}",
        "- 常见 OCR 噪声命中：",
    ]
    for term, count in noise_counts.items():
        if count:
            lines.append(f"  - `{term}`: {count}")
    lines.extend(
        [
            "",
            "## 抽样复核页",
            "",
            "- 按每 20 页抽样登记："
            + ", ".join(f"{p:03d}" for p in sampled_pages),
            "- 本次自动流程已登记抽样页和低置信页；要达到出版级准确，需要逐页对照渲染页图继续人工校订。",
            "",
            "## 结论",
            "",
            "- 已生成完整页序 OCR Markdown、表格汇总、页状态、表格台账和带页码的关键内容版。",
            "- 因源文件为扫描 PDF，不能声明 100% 无误；本次交付是可追溯、可继续校订的完整文本化底稿。",
        ]
    )
    Path("qa/extraction_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    pages = read_pages()
    sections = detect_sections(pages)
    tables = extract_tables(pages)
    by_page = defaultdict(list)
    for t in tables:
        by_page[t.page].append(t)
    write_full_markdown(pages, sections, by_page)
    write_tables_markdown(tables)
    write_csvs(pages, sections, tables, by_page)
    write_verified_key()
    write_audit(pages, tables, by_page)


if __name__ == "__main__":
    main()
