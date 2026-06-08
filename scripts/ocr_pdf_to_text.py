#!/usr/bin/env python3
import argparse
import concurrent.futures
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader


def run(cmd, *, env=None):
    return subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


def ocr_page(args):
    pdf_path, out_dir, pdftoppm, tessdata, page_num, dpi, lang, psm, force = args
    page_txt = out_dir / f"page_{page_num:03d}.txt"
    if page_txt.exists() and page_txt.stat().st_size > 0 and not force:
        return page_num, "cached"

    env = os.environ.copy()
    env["OMP_THREAD_LIMIT"] = "1"

    with tempfile.TemporaryDirectory(prefix=f"dgcr_{page_num:03d}_") as td:
        prefix = Path(td) / "page"
        run(
            [
                pdftoppm,
                "-f",
                str(page_num),
                "-l",
                str(page_num),
                "-r",
                str(dpi),
                "-png",
                str(pdf_path),
                str(prefix),
            ],
            env=env,
        )
        images = sorted(Path(td).glob("page-*.png"))
        if not images:
            raise RuntimeError(f"no rendered image for page {page_num}")

        tess = subprocess.run(
            [
                "tesseract",
                str(images[0]),
                "stdout",
                "--tessdata-dir",
                str(tessdata),
                "-l",
                lang,
                "--psm",
                str(psm),
                "-c",
                f"user_defined_dpi={dpi}",
                "-c",
                "preserve_interword_spaces=1",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    text = "\n".join(line.rstrip() for line in tess.stdout.splitlines()).strip()
    page_txt.write_text(text + "\n", encoding="utf-8")
    return page_num, "ocr"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("ocr_text"))
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--tessdata", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=170)
    parser.add_argument("--lang", default="chi_sim+eng")
    parser.add_argument("--psm", type=int, default=6)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--from-page", type=int, default=1)
    parser.add_argument("--to-page", type=int)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    page_count = len(PdfReader(str(args.pdf)).pages)
    to_page = args.to_page or page_count
    page_nums = list(range(args.from_page, min(to_page, page_count) + 1))

    jobs = [
        (
            args.pdf.resolve(),
            args.out_dir.resolve(),
            args.pdftoppm,
            args.tessdata.resolve(),
            p,
            args.dpi,
            args.lang,
            args.psm,
            args.force,
        )
        for p in page_nums
    ]

    completed = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
        for page_num, status in ex.map(ocr_page, jobs):
            completed += 1
            print(f"{completed:>4}/{len(jobs)} page {page_num:03d} {status}", flush=True)

    combined = args.out_dir / "all_pages.md"
    with combined.open("w", encoding="utf-8") as f:
        for p in range(1, page_count + 1):
            page_txt = args.out_dir / f"page_{p:03d}.txt"
            if page_txt.exists():
                f.write(f"\n\n<!-- page:{p:03d} -->\n\n")
                f.write(page_txt.read_text(encoding="utf-8").strip())
                f.write("\n")

    print(f"combined: {combined}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.stderr.write("Command failed:\n")
        sys.stderr.write(" ".join(map(str, e.cmd)) + "\n")
        if e.stderr:
            sys.stderr.write(e.stderr)
        raise
