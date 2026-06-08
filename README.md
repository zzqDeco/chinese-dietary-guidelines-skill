# Dietary Guidelines for Chinese Residents Markdown Extraction

本仓库保存《中国居民膳食指南（2022）》扫描版 PDF 的 OCR、表格复核、正文校订和 verified Markdown 产物。

## 主要产物

- `dietary_guidelines_china_2022_full_verified.md`：完整 verified 正文，保留 374 个 `pdf-page` 标记。
- `dietary_guidelines_china_2022_tables_verified.md`：99 个 OCR 表格候选的 verified 汇总，并额外纳入第 365 页 BMI 密集图表。
- `dietary_guidelines_china_2022_key_content_verified.md`：关键内容 verified 摘要。
- `qa/extraction_audit.md`：OCR、表格、正文低置信页和噪声校订审计报告。
- `qa/table_cell_corrections.csv`：表格单元格校订日志。
- `qa/body_text_corrections.csv`：正文页图校订日志。
- `qa/low_confidence_page_review.csv`：低置信页复核台账。

## 源 PDF

源文件保留在工作目录中，但不进入普通 git 历史，避免超过常见远端仓库的单文件限制。

- 文件名：`1711104221187059.pdf`
- SHA-256：`59a1437cc8986eb07cfbd174bc2e9aebd4b282740cc545f1957cfea500789de9`

如果以后需要推送到 GitHub/GitLab 并同时版本化源 PDF，应先启用 Git LFS，再把 PDF 加入 LFS 跟踪。

## 版本管理策略

纳入 git：

- Markdown 交付物
- OCR 文本底稿
- QA CSV/MD 审计与校订日志
- 构建和复核脚本
- Vision OCR TSV 文本结果

不纳入 git：

- 源 PDF
- Poppler 渲染的页图
- 手工裁图和其他 PNG 二进制中间产物
- Tesseract 语言模型和 Python 缓存

## 常用校验

```bash
python3 scripts/build_body_review_assets.py
python3 scripts/build_verified_outputs.py
```

重建后重点检查：

- `dietary_guidelines_china_2022_full_verified.md` 中 `<!-- pdf-page:` 数量应为 374。
- `dietary_guidelines_china_2022_tables_verified.md` 中原候选表章节应为 99。
- `qa/table_cell_corrections.csv` 中不应有 `uncertain_registered` 表格单元格。
- `qa/extraction_audit.md` 应显示 verified 文件中目标噪声剩余命中为“无”。
