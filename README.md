# Dietary Guidelines for Chinese Residents Workspace

本地完整仓库保存《中国居民膳食指南（2022）》扫描版 PDF 的 OCR、表格复核、正文校订、verified Markdown 产物，以及基于这些资料整理出的 Codex skill。

公开 GitHub 仓库只发布脱敏后的 skill package，不发布源 PDF、OCR 全文、verified 全书 Markdown、页图、QA 原始校订材料或任何私人饮食数据。

## Public Skill Package

公开发布内容仅包含：

- `skills/chinese-dietary-guidelines/`
- `VERSION`
- `CHANGELOG.md`
- `scripts/validate_skill.sh`
- `.github/workflows/validate.yml`
- public README and repository metadata

公开包的目标是提供一个 Codex skill，用于：

- 建立饮食画像
- 记录和纠正每日饮食
- 分析最近 1/7/14/30 天饮食结构
- 按《中国居民膳食指南（2022）》原则生成相对计算和行动优先级
- 生成具体可做的 7 天餐食计划、购物清单和备餐计划
- 给出食堂、外卖、便利店、聚餐等外食建议
- 复盘执行情况并调整下一轮计划

私人饮食数据只保存在本机：

```text
~/.codex/data/chinese-dietary-guidelines/
```

公开仓库不包含、也不应提交这些文件。

## Skill Installation

开发完成后，将 skill 源码复制到本机 Codex skill 目录：

```bash
cp -R skills/chinese-dietary-guidelines ~/.codex/skills/chinese-dietary-guidelines
```

## Safety Boundary

该 skill 面向日常膳食记录、结构分析和指南级饮食建议，不提供医疗诊断、疾病治疗、临床营养处方、孕期/儿童减重建议或补剂剂量处方。慢病、孕产风险、儿童生长异常、吞咽困难、快速体重变化等场景应提示医生或注册营养师评估。

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

公开 GitHub 仓库额外不纳入：

- OCR 文本目录
- verified 全书 Markdown
- QA 原始校订和审计材料
- 源 PDF 或任何页面图片
- 本机安装目录副本
- `~/.codex/data/chinese-dietary-guidelines/` 下的私人饮食数据

## Release And Validation

当前版本见 `VERSION`。发布前运行：

```bash
bash scripts/validate_skill.sh
```

公开仓库 CI 使用严格模式：

```bash
STRICT_PUBLIC=1 bash scripts/validate_skill.sh
```

严格模式会拒绝 OCR/PDF/QA/full Markdown 抽取产物进入公开包。

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
