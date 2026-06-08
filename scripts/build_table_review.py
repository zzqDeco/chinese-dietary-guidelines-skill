#!/usr/bin/env python3
import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_guidelines_deliverables.py"
QA_DIR = ROOT / "qa"
IMAGE_DIR = QA_DIR / "table_page_images"
OUT_CSV = QA_DIR / "table_review.csv"
OUT_MD = QA_DIR / "table_review_work.md"


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_guidelines_deliverables", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main():
    module = load_build_module()
    pages = module.read_pages()
    tables = module.extract_tables(pages)
    QA_DIR.mkdir(exist_ok=True)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "candidate_no",
                "table_id",
                "title_original",
                "pdf_page",
                "status_original",
                "verified_original",
                "page_image",
                "review_status",
                "review_notes",
            ],
        )
        writer.writeheader()
        for idx, table in enumerate(tables, 1):
            image = IMAGE_DIR / f"page_{table.page:03d}.png"
            writer.writerow(
                {
                    "candidate_no": idx,
                    "table_id": table.table_id,
                    "title_original": table.title,
                    "pdf_page": f"{table.page:03d}",
                    "status_original": table.status,
                    "verified_original": str(table.verified).lower(),
                    "page_image": str(image.relative_to(ROOT)) if image.exists() else "",
                    "review_status": "pending",
                    "review_notes": "",
                }
            )

    parts = [
        "# 表格逐张复核工作清单",
        "",
        "本文件把 `qa/table_index.csv` 的候选表格、原 OCR 行块和渲染页图路径放在一起，用于逐表列结构复核。",
        "",
    ]
    for idx, table in enumerate(tables, 1):
        image = IMAGE_DIR / f"page_{table.page:03d}.png"
        parts.extend(
            [
                f"## {idx:03d}. {table.table_id} / PDF 第 {table.page:03d} 页",
                "",
                f"- 原题：{table.title}",
                f"- 原状态：{table.status}",
                f"- 原 verified：{str(table.verified).lower()}",
                f"- 页图：`{image.relative_to(ROOT) if image.exists() else 'missing'}`",
                "- 复核状态：pending",
                "",
                "```text",
                "\n".join(table.block),
                "```",
                "",
            ]
        )
    OUT_MD.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    print(f"tables {len(tables)}")


if __name__ == "__main__":
    main()
