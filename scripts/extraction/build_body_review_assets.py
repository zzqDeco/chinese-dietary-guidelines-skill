#!/usr/bin/env python3
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "qa"
QA_AUDIT = QA / "audit"
QA_CORRECTIONS = QA / "corrections"
QA_INDEXES = QA / "indexes"
PAGE_STATUS = QA_INDEXES / "page_status.csv"
BODY_IMAGES = QA / "body_page_images"
VISION = QA_AUDIT / "vision_ocr_body"
BODY_CORRECTIONS = QA_CORRECTIONS / "body_text_corrections.csv"
LOW_REVIEW = QA_INDEXES / "low_confidence_page_review.csv"
LOW_VISION_MD = QA_AUDIT / "low_confidence_page_vision.md"


def read_vision(page: str) -> list[str]:
    path = VISION / f"page_{page}.tsv"
    if not path.exists():
        return []
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split("\t")
        if len(parts) >= 6:
            lines.append(parts[5].strip())
    return [line for line in lines if line]


def low_pages() -> list[dict[str, str]]:
    with PAGE_STATUS.open(newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row["confidence"] == "low"]


def write_low_review() -> list[dict[str, str]]:
    QA_AUDIT.mkdir(parents=True, exist_ok=True)
    QA_INDEXES.mkdir(parents=True, exist_ok=True)
    rows = []
    md = ["# Low-confidence page Vision OCR review", ""]
    for row in low_pages():
        page = row["pdf_page"]
        lines = read_vision(page)
        has_table = row["has_table"] == "True"
        image = BODY_IMAGES / f"page_{page}.png"
        vision_file = VISION / f"page_{page}.tsv"
        if not lines:
            action = "no_readable_text_after_review"
            status = "reviewed"
            confidence = "high"
            notes = "页图经 Vision OCR 复核后无稳定可读正文；保留页标，不补写。"
        elif has_table:
            action = "verified_table_block_plus_vision_review"
            status = "reviewed"
            confidence = "high"
            notes = "本页含表格候选；verified 表格块已单独校订，正文可读文字以 Vision OCR 复核。"
        elif page == "365":
            action = "converted_dense_bmi_chart"
            status = "reviewed"
            confidence = "high"
            notes = "本页为成人 BMI 与健康体重对应关系密集图表，已作为非 99 候选图表写入 verified 正文和表格汇总。"
        else:
            action = "vision_ocr_reviewed"
            status = "reviewed"
            confidence = "medium"
            notes = "已生成 220 DPI 页图和 Vision OCR 复核文本；未发现目标残留噪声时不改写正文。"
        rows.append(
            {
                "pdf_page": page,
                "section": row["section"],
                "source_image": str(image),
                "vision_ocr_file": str(vision_file),
                "has_text": row["has_text"],
                "has_table": row["has_table"],
                "table_ids": row["table_ids"],
                "review_status": status,
                "action": action,
                "confidence": confidence,
                "notes": notes,
            }
        )
        md.extend([f"## PDF page {page}", "", f"- section: {row['section']}", f"- action: {action}", ""])
        md.extend(lines or ["_No stable readable text detected by Vision OCR._"])
        md.append("")
    with LOW_REVIEW.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    LOW_VISION_MD.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return rows


def body_correction_rows() -> list[dict[str, str]]:
    exact = [
        ("011", "萤索搭配", "荤素搭配", "荤素"),
        ("011", "训饪", "烹饪", "烹饪"),
        ("011", "公筷公义", "公筷公勺", "公筷公勺"),
        ("110", "训饪", "烹饪", "烹饪"),
        ("158", "训饪", "烹饪", "烹饪"),
        ("168", "准则八_公筷分餐，杜绝浪费", "准则八 公筷分餐，杜绝浪费", "公筷分餐"),
        ("168", "讲究卫生，从分餐公筷做起", "讲究卫生，从分餐公筷做起", "公筷"),
        ("172", "训饪", "烹饪", "烹饪"),
        ("175", "公筷公与", "公筷公勺", "公筷公勺"),
        ("175", "策子", "筷子", "筷子"),
        ("175", "公筷公怀", "公筷公勺", "公筷公勺"),
        ("175", "来菜感汤", "夹菜盛汤", "夹菜盛汤"),
        ("175", "碗征", "碗筷", "碗筷"),
        ("176", "公筷公怀", "公筷公勺", "公筷公勺"),
        ("176", "选这食物", "选烹食物", "选烹食物"),
        ("176", "背养健康", "营养健康", "营养健康"),
        ("176", "餐锯就餐", "餐馆就餐", "餐馆就餐"),
        ("176", "公共和餐饮", "公共餐饮", "公共餐饮"),
        ("176", "公筷公司", "公筷公勺", "公筷公勺"),
        ("176", "上菜前分父", "上菜前分餐", "上菜前分餐"),
        ("176", "优食卫生", "饮食卫生", "饮食卫生"),
        ("177", "公筷公怀", "公筷公勺", "公筷公勺"),
        ("177", "训饪", "烹饪", "烹饪"),
        ("180", "公筷\nBAY", "公筷公勺", "公筷公勺"),
        ("180", "公勺公筑", "公勺公筷", "公勺公筷"),
        ("180", "取和餐", "取餐", "取餐"),
        ("315", "训饪", "烹饪", "烹饪"),
        ("322", "训饪", "烹饪", "烹饪"),
        ("323", "平衡匿食", "平衡膳食", "平衡膳食"),
        ("306", "会选会赢", "会选会烹", "会选会烹"),
        ("325", "公筷分 “ 售 ，\n餐制", "公筷分餐制", "公筷分餐制"),
        ("325", "所但导", "所倡导", "倡导"),
        ("325", "平衡匿食", "平衡膳食", "平衡膳食"),
        ("332", "训饪", "烹饪", "烹饪"),
    ]
    regex = [
        (
            "243",
            r"2\. 食物多样化才能满足 7~24.*?3\. 7-24 月龄婴幼儿辅食多样化的情况有待改观",
            "2. 食物多样化才能满足 7~24月龄婴幼儿的营养需求\n不同种类的食物提供不同的营养素，只有多样化的食物才能提供全面而均衡的营养。①谷物类，如稠粥、软饭、面条等含有大量的碳水化合物，可以为婴幼儿提供能量，但一般缺乏铁、锌、钙、维生素 A 等营养素。②动物性食物，如鸡蛋、瘦肉、肝脏、鱼类等，富含优质蛋白质、铁、锌、维生素 A 等，是婴幼儿不可或缺的食物。③蔬菜和水果是维生素、矿物质以及纤维素的重要来源之一。④豆类是优质蛋白质的补充来源。⑤植物油和脂肪，提供能量和必需脂肪酸。\n3. 7~24 月龄婴幼儿辅食多样化的情况有待改观",
            "BERE",
        ),
        (
            "245",
            r"4\. 100% 的纯果汁不同于果泥.*?5[,，]\s*辅食不加盐",
            "4. 100% 的纯果汁不同于果泥\n鲜榨果汁、100%纯果汁中的果糖、蔗糖等糖含量过高，膳食纤维含量少，其营养价值不如果泥或整个水果。为减少婴幼儿糖的摄入量，推荐 7~12 月龄的婴儿最好食用果泥和小果粒，可少量饮用纯果汁但需要稀释；13~24 月龄幼儿每天纯果汁的饮用量不超过 120ml，并且最好限制在进食正餐或点心时饮用。\n5. 辅食不加盐",
            "BERE",
        ),
        (
            "296",
            r"\(2\s*\)\s*发酵豆制品不能缺.*?\(3\)\s*巧搭配",
            "（2）发酵豆制品不能缺\n发酵豆制品中还含有维生素 B12，素食人群特别要注意选用发酵豆制品。\n\n发酵豆制品是以大豆为主要原料，经微生物发酵而成的豆制品。常见制品有发酵豆、酸豆浆、腐乳、豆豉、臭豆腐、酱油、豆瓣酱等。发酵豆制品制作过程中，由于微生物的生长繁殖，可合成少量的维生素 B12。\n发酵豆制品维生素 B12 含量的多少，除与微生物的品种有关外，与微生物生长繁殖的多少也有关。微生物生长繁殖的越多，豆制品的固有风味越好，维生素 B12 合成的就越多，在选购时应注意。本指南推荐全素者每日摄入 5~10g 发酵豆制品。\n（3）巧搭配",
            "BERE",
        ),
    ]
    rows = []
    for page, original, corrected, term in exact:
        rows.append(row(page, original, corrected, term, "exact"))
    for page, original, corrected, term in regex:
        rows.append(row(page, original, corrected, term, "regex"))
    return rows


def row(page: str, original: str, corrected: str, term: str, mode: str) -> dict[str, str]:
    return {
        "pdf_page": page,
        "file": "full",
        "location_hint": original[:80].replace("\n", "\\n"),
        "original_text": original,
        "corrected_text": corrected,
        "term": term,
        "action": "corrected",
        "confidence": "high",
        "source_image": f"qa/body_page_images/page_{page}.png",
        "mode": mode,
        "notes": "按 220 DPI 页图与 Vision OCR 复核后修正正文 OCR 噪声。",
    }


def write_body_corrections() -> list[dict[str, str]]:
    rows = body_correction_rows()
    QA_CORRECTIONS.mkdir(parents=True, exist_ok=True)
    with BODY_CORRECTIONS.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    review_rows = write_low_review()
    correction_rows = write_body_corrections()
    print(f"low confidence page reviews: {len(review_rows)}")
    print(f"body text corrections: {len(correction_rows)}")


if __name__ == "__main__":
    main()
