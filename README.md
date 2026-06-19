# Chinese Dietary Guidelines Skill and Corpus

Public Markdown corpus and Codex skill for working with the Chinese Dietary Guidelines for Chinese Residents (2022).

This repository provides two things together:

- A verified Markdown corpus extracted from a 374-page scanned PDF.
- A Codex skill that helps an agent record meals, analyze recent diet patterns, and produce concrete meal plans grounded in the guideline principles.

The layout follows the common open skill repository pattern used by projects such as [openai/skills](https://github.com/openai/skills), [anthropics/skills](https://github.com/anthropics/skills), [awesome-codex-skills](https://github.com/ComposioHQ/awesome-codex-skills), and [troykelly/codex-skills](https://github.com/troykelly/codex-skills): project-level documentation at the root, self-contained skill packages under `skills/`, and supporting corpus or tooling in separate top-level directories.

## What This Project Provides

- `skills/chinese-dietary-guidelines/`: a self-contained Codex skill for daily dietary management.
- `corpus/verified/`: reviewed Markdown outputs, including full text, tables, and key content.
- `corpus/extracted/`: earlier extracted Markdown outputs before the verified pass.
- `corpus/ocr/`: OCR text by page, including the v2 220 DPI Tesseract extraction.
- `qa/`: audit reports, correction logs, page status indexes, and table review indexes.
- `scripts/`: validation entrypoint plus extraction and rebuilding tools.
- `docs/`: methodology, public data policy, and skill usage notes.

## Repository Layout

```text
.
├── README.md
├── CHANGELOG.md
├── VERSION
├── .github/workflows/validate.yml
├── scripts/
│   ├── validate_skill.sh
│   └── extraction/
├── skills/
│   └── chinese-dietary-guidelines/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/
├── corpus/
│   ├── verified/
│   ├── extracted/
│   └── ocr/
├── qa/
│   ├── audit/
│   ├── corrections/
│   └── indexes/
└── docs/
```

## Use The Skill

Install the skill into your local Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/chinese-dietary-guidelines ~/.codex/skills/chinese-dietary-guidelines
```

Private user data is stored outside this repository:

```text
~/.codex/data/chinese-dietary-guidelines/
```

Example prompts:

- "记录今天早餐：牛奶、鸡蛋、全麦面包。"
- "分析我最近 7 天的饮食结构。"
- "按中国居民膳食指南推荐下周 7 天具体餐食。"
- "今天只能吃食堂，怎么选更接近指南？"
- "根据下周菜单生成购物清单和备餐计划。"

The skill is agent-led. It does transparent relative calculations when analyzing or recommending, but it does not include a hidden deterministic diet rule engine or clinical nutrition calculator.

See [docs/skill-usage.md](docs/skill-usage.md) for details.

## Use The Corpus

- [corpus/verified/full.md](corpus/verified/full.md): full verified Markdown with 374 `pdf-page` markers.
- [corpus/verified/tables.md](corpus/verified/tables.md): verified table summary for 99 OCR table candidates, plus the dense BMI chart from page 365.
- [corpus/verified/key-content.md](corpus/verified/key-content.md): key guideline content with page references.
- [corpus/extracted/](corpus/extracted/): extracted Markdown before the verified correction pass.
- [corpus/ocr/v1](corpus/ocr/v1) and [corpus/ocr/v2](corpus/ocr/v2): page-level OCR text.

The corpus is intended for traceable reference and agent grounding. It is not a publisher-grade reproduction of the book layout. Tables and common OCR terminology were reviewed, but scanned-document OCR can still contain residual errors.

See [docs/extraction-methodology.md](docs/extraction-methodology.md) for the extraction and QA process.

## Validation

Run the local validation script:

```bash
bash scripts/validate_skill.sh
```

The check validates:

- skill frontmatter and required references
- core guideline anchors in the skill reference material
- absence of old rule-engine scripts or wording
- absence of TODO/FIXME in the skill package
- verified full-text page marker count
- verified table candidate count
- OCR v2 presence
- absence of tracked PDF, PNG, private diet logs, profiles, `.codex/`, and Python cache files

GitHub Actions runs the same validation on push and pull request.

## Privacy And Safety

This repository does not track private diet logs, local profile files, or the Codex installation directory. Keep files such as `diet_log.jsonl`, `profile.json`, and anything under `~/.codex/data/chinese-dietary-guidelines/` out of git.

The skill supports daily diet logging, food-group analysis, concrete meal planning, shopping/prep planning, eating-out advice, and execution review. It does not provide medical diagnosis, disease treatment, clinical nutrition prescriptions, pregnancy or child weight-loss plans, or supplement dosage prescriptions.

See [docs/public-data-policy.md](docs/public-data-policy.md).

## Versioning

Current version: see [VERSION](VERSION).

Release history is recorded in [CHANGELOG.md](CHANGELOG.md).

Version policy:

- `0.1.x`: documentation, repository organization, validation, schema clarifications, and small workflow fixes.
- `0.2.0`: new skill sub-functions or output schemas.
- `1.0.0`: stable real-world usage with mature installation and validation workflows.

## License / Source Notice

No general open-source license is declared yet. The repository includes corpus text extracted from the Chinese Dietary Guidelines for Chinese Residents (2022), so the code/skill instructions and the guideline-derived corpus may need separate licensing decisions before adding a broad LICENSE file.

Source PDF and page images are intentionally not tracked in normal git history.
