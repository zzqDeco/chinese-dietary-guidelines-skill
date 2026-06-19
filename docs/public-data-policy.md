# Public Data Policy

This repository is public and intentionally includes the extracted guideline corpus needed by the skill.

## Tracked

The following files are intended to be tracked:

- skill source under `skills/chinese-dietary-guidelines/`
- verified Markdown corpus under `corpus/verified/`
- extracted Markdown corpus under `corpus/extracted/`
- OCR text under `corpus/ocr/`
- QA indexes, audit notes, and correction logs under `qa/`
- extraction and validation scripts under `scripts/`
- project documentation under `docs/`

## Not Tracked

The following files must not be committed:

- source PDF files
- rendered page images
- manual image crops
- `.codex/` directories
- `diet_log.jsonl`
- `profile.json`
- any file under `~/.codex/data/chinese-dietary-guidelines/`
- Python caches, OCR runtime caches, and temporary release staging output

The validation script rejects common private or binary artifacts:

```bash
bash scripts/validate_skill.sh
```

## Personal Diet Data

The skill stores personal diet data outside the repository:

```text
~/.codex/data/chinese-dietary-guidelines/
```

Those files are private local state. They are not required to build, validate, or publish this repository.

## Source Notice

The corpus is derived from the Chinese Dietary Guidelines for Chinese Residents (2022). No broad repository license is declared yet because the guideline-derived corpus and the project code may require separate licensing decisions.

Until a license is added, treat the corpus as a public reference artifact for this project, not as newly relicensed guideline text.
