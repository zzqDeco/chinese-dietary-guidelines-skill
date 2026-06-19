# Extraction Methodology

This project converts a scanned 374-page PDF of the Chinese Dietary Guidelines for Chinese Residents (2022) into traceable Markdown corpus files.

## Inputs

- Source: local scanned PDF, not tracked in git.
- Page count: 374.
- Text layer: none; extraction depends on rendered page images and OCR.

## OCR Workflow

The v2 OCR pass renders PDF pages with Poppler and runs Tesseract with Chinese and English language models:

```bash
python3 scripts/extraction/ocr_pdf_to_text.py 1711104221187059.pdf \
  --out-dir corpus/ocr/v2 \
  --pdftoppm /path/to/pdftoppm \
  --tessdata .ocr_tessdata \
  --dpi 220 \
  --lang chi_sim+eng
```

The generated output is page-oriented:

- `corpus/ocr/v2/page_NNN.txt`
- `corpus/ocr/v2/all_pages.md`

The older OCR baseline is kept under `corpus/ocr/v1/` for comparison.

## Markdown Outputs

The extraction scripts build two levels of corpus:

- `corpus/extracted/`: OCR-derived Markdown and table summaries before the final verified pass.
- `corpus/verified/`: corrected full text, corrected table summary, and key content with source page references.

The full verified file keeps one marker per PDF page:

```text
<!-- pdf-page:NNN -->
```

The expected marker count is 374.

## Table Review

The table workflow identifies 99 OCR table candidates, then reviews their status and structure:

- `converted`: real table converted into Markdown.
- `merged_continuation`: continuation or cross-page table segment.
- `not_a_table_after_review`: OCR false positive or body-text reference.

Table-related artifacts are stored in:

- `corpus/verified/tables.md`
- `qa/indexes/table_index.csv`
- `qa/indexes/table_review.csv`
- `qa/corrections/table_cell_corrections.csv`

Page images and manual crops are not tracked in git, but QA files may retain their historical local image paths for provenance.

## Correction Logs

Corrections are additive and traceable:

- `qa/corrections/ocr_term_corrections.csv`: high-frequency OCR term corrections.
- `qa/corrections/body_text_corrections.csv`: page-image or Vision OCR based body-text corrections.
- `qa/corrections/numeric_sentinel_check.csv`: key numeric sentinel checks.

The source OCR files are preserved rather than overwritten.

## Audit

The main audit report is:

```text
qa/audit/extraction_audit.md
```

It records OCR settings, page coverage, table coverage, known correction scope, and remaining OCR risk. The verified corpus is suitable for traceable reference and skill grounding, but it is not a publisher-grade layout reproduction or a claim of perfect OCR accuracy.
