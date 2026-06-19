#!/usr/bin/env python3
import csv
import importlib.util
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "scripts" / "extraction" / "build_guidelines_deliverables.py"
QA_DIR = ROOT / "qa"
IMAGE_DIR = QA_DIR / "table_page_images"
EXTRACTED_DIR = ROOT / "corpus" / "extracted"
QA_AUDIT_DIR = QA_DIR / "audit"
QA_INDEX_DIR = QA_DIR / "indexes"


FALSE_POSITIVES = {
    11: "正文引用“见表 1-14”，不是表题。",
    22: "正文同时引用表 1-26 和表 1-27，不是独立表题。",
    41: "正文引用“表 1-47”，不是可见表格。",
    49: "正文引用表 1-54，不是新表或续表。",
    50: "正文继续说明表 1-54，不是新表或续表。",
    61: "正文引用“表 2-7”，不是表题。",
    63: "正文引用“表 2-9”，不是表题。",
    67: "正文引用“表 2-11”，不是表题。",
    69: "正文引用“见表 2-12”，不是表题。",
    72: "正文引用“表 2-14”，不是表题。",
    77: "正文引用“表 3-1”，不是表题。",
    82: "正文引用表 3-5 和表 3-6，不是独立表题。",
    90: "正文引用附表 1-2、附表 1-3 和附表 1-4，不是表题。",
}


TITLE_OVERRIDES = {
    1: "表 1-1 不同人群谷薯类食物建议摄入量",
    2: "表 1-4 不同食物搭配后蛋白质的生物价（BV）",
    3: "表 1-5 人体必需营养素和其他膳食成分",
    4: "表 1-6 中国成年人膳食宏量营养素供能比适宜范围",
    5: "表 1-7 不同种类食物中富含的营养素",
    6: "续表 1-7 不同种类食物中富含的营养素",
    7: "表 1-8 全国居民人均主要食品消费量",
    8: "表 1-9 我国平均每标准人日各类食物摄入量",
    9: "表 1-10 我国城乡居民膳食能量的食物来源比例",
    10: "表 1-11 我国居民每标准人日膳食三大营养素平均摄入量",
    12: "表 1-14 推荐的成年人身体活动量",
    13: "表 1-16 成年人每天身体活动量相当于快走 6000 步的活动时间",
    14: "表 1-17 可选择的运动方案",
    15: "表 1-18 成年男性、女性的健康体脂范围",
    16: "表 1-19 体重与疾病关系的证据分析",
    17: "表 1-21 运动强度的判断",
    18: "表 1-22 不同人群蔬菜水果、全谷物、奶类、大豆、坚果类食物建议摄入量",
    19: "表 1-23 常见蔬菜种类",
    20: "表 1-24 日常全谷物营养成分与精制谷物的比较（每 100g 可食部）",
    21: "表 1-25 300ml 牛奶提供的营养价值",
    23: "表 1-26 蔬菜、水果与健康的关系",
    24: "续表 1-26 蔬菜、水果与健康的关系",
    25: "表 1-27 奶类及其制品、大豆及其制品和坚果与健康的关系",
    26: "表 1-28 各国膳食指南中成年人乳及乳制品的建议摄入量",
    27: "表 1-31 常见动物性食物蛋白质含量比较（每 100g 可食部）",
    28: "表 1-32 常见鱼中 EPA 和 DHA 含量",
    29: "表 1-33 鸡蛋白和鸡蛋黄营养素含量比较",
    30: "表 1-35 常见动物性食物胆固醇含量（每 100g 可食部）",
    31: "表 1-37 鲍鱼和其他水产类食物主要营养素含量比较（每 100g 可食部）",
    32: "表 1-38 不同人群食盐、烹调油、添加糖的推荐摄入量和酒精的控制摄入量",
    33: "表 1-39 食用油的营养型分类",
    34: "表 1-40 含有 15g 酒精的不同酒量",
    35: "表 1-41 我国居民烹调油、食盐和钠摄入量变化",
    36: "表 1-42 2015-2017 年我国成年人饮酒率",
    37: "表 1-43 2015-2017 年我国成年饮酒者每日酒精摄入水平分布",
    38: "表 1-44 盐、油、酒、糖与人体健康的证据",
    39: "表 1-45 常见包装食品反式脂肪酸含量",
    40: "表 1-46 常见高盐（钠）食品表（每 100g）",
    42: "表 1-48 零食推荐食用种类",
    43: "表 1-49 饮水量与健康的证据体分析",
    44: "表 1-51 正常成年人每天水的出入平衡量",
    45: "表 1-52 茶的分类",
    46: "表 1-54 平衡膳食宝塔的各类食物量",
    47: "表 1-55 各类食物提供的主要营养素",
    48: "表 1-56 不同年龄轻体力劳动者的能量需要量（EER）",
    51: "表 1-57 2000kcal 能量的一日餐举例",
    52: "表 1-58 建议“多吃”和“少吃”的食物举例",
    53: "表 1-59 烹饪对蔬菜中维生素 C 含量的影响",
    54: "表 1-60 西餐中常见的牛肉成熟度和辨认方法",
    55: "表 2-1 妊娠期妇女体重增长范围和妊娠中晚期周增重推荐值",
    56: "表 2-2 孕中、晚期一日食谱举例",
    57: "续表 2-2 孕中、晚期一日食谱举例",
    58: "表 2-3 妇女备孕和孕期一日食物推荐量（低至中度身体活动水平）",
    59: "表 2-4 乳母一天食谱举例（能量 2250kcal/d）",
    60: "表 2-6 获得 1000mg 钙的食物组合",
    62: "表 2-7 吸出母乳的保存条件和允许保存时间",
    64: "表 2-8 学龄前儿童每日各类食物建议摄入量",
    65: "表 2-9 一日食谱举例",
    66: "表 2-10 推荐和限制的零食",
    68: "表 2-11 学龄儿童一周身体活动示例",
    70: "表 2-12 微型营养评估简表（MNA-SF）",
    71: "表 2-13 Fried 衰弱评估方法",
    73: "表 2-14 饮水试验及结果判断",
    74: "表 2-15 高龄老年人一周活动举例",
    75: "表 2-16 全素和蛋奶素成年人的推荐膳食组成",
    76: "续表 2-16 全素和蛋奶素成年人的推荐膳食组成",
    78: "表 3-1 食物与健康文献证据综合评价表",
    79: "表 3-3 常见膳食定性术语和概念描述",
    80: "表 3-4 常见食物定性和定量描述",
    81: "续表 3-4 常见食物定性和定量描述",
    83: "表 3-6 不同能量需要水平下的平衡膳食模式所提供的能量和营养素",
    84: "表 3-7 不同能量需要水平的平衡膳食模式所提供能量和来源构成比",
    85: "续表 一日三餐举例（2250kcal）",
    86: "续表 一日三餐举例（2400kcal）",
    87: "续表 一日三餐举例（2250kcal）",
    88: "续表 一日三餐举例（2300kcal）",
    89: "附表 1-1 常见食物的标准份量（以可食部计）",
    91: "附表 1-2 标准物品定义和用途",
    92: "附表 1-3 参考手势的定义和用途",
    93: "附表 1-4 食物标准份量示意图",
    94: "续附表 1-4 食物标准份量示意图",
    95: "续附表 1-4 食物标准份量示意图",
    96: "附表 2-1 中国居民膳食能量需要量（EER）、宏量营养素可接受范围（AMDR）、蛋白质推荐摄入量（RNI）",
    97: "附表 5-1 6-18 岁学龄儿童青少年生长迟缓的年龄别身高界值范围",
    98: "附表 5-2 6-18 岁学龄儿童青少年营养状况的 BMI 界值范围",
    99: "附表 5-4 用于筛查 7-18 岁学龄儿童青少年高腰围的界值范围",
}


HEADER_OVERRIDES = {
    1: ["食物类别", "单位", "2岁-", "4岁-", "7岁-", "11岁-", "14岁-", "18岁-", "65岁-"],
    4: ["宏量营养素", "适宜范围（%E）"],
    7: ["年份", "谷物（g/d）", "畜禽鱼蛋类（g/d）", "食用油（g/d）"],
    8: ["年份", "谷类（g）", "薯类（g）", "蔬菜（g）", "水果（g）", "畜禽鱼蛋（g）", "奶（g）", "食用油（g）"],
    9: ["食物来源", "1982年", "1992年", "2002年", "2010-2012年", "2015-2017年"],
    10: ["营养素", "1982年", "1992年", "2002年", "2010-2012年", "2015-2017年"],
    12: ["类别", "身体活动建议", "推荐量/频次"],
    13: ["身体活动", "相当于快走 6000 步的活动时间（min）"],
    15: ["性别/范围", "必要脂肪", "健康体脂范围"],
    16: ["关系/结论", "证据体", "可信等级"],
    17: ["强度", "最大心率百分比（%）", "摄氧量百分比（%）", "自觉用力程度", "MET"],
    18: ["食物/单位", "2岁-", "4岁-", "7岁-", "11岁-", "14岁-", "18岁-", "65岁-"],
    19: ["蔬菜类别", "常见食物"],
    21: ["营养素", "300ml 牛奶提供量", "成人男性 RNI/AI 占比（%）", "成人女性 RNI/AI 占比（%）"],
    23: ["食物类别", "健康关系", "证据体", "证据级别"],
    24: ["食物类别", "健康关系", "证据体", "证据级别"],
    25: ["食物类别", "健康关系", "证据体", "证据级别"],
    26: ["国家/地区", "建议摄入量", "国家/地区", "建议摄入量"],
    27: ["食物", "蛋白质（g）", "食物", "蛋白质（g）", "食物", "蛋白质（g）"],
    28: ["鱼类", "EPA（g/100g）", "DHA（g/100g）", "EPA+DHA（g/100g）"],
    29: ["营养素", "鸡蛋黄", "鸡蛋白"],
    30: ["食物", "胆固醇（mg）", "食物", "胆固醇（mg）", "食物", "胆固醇（mg）"],
    31: ["营养素", "鲍鱼", "海参", "带鱼", "对虾"],
    32: ["项目", "2岁-", "4岁-", "7岁-", "11岁-", "14岁-", "18岁-", "65岁-"],
    33: ["营养型分类", "代表油脂", "主要特点"],
    34: ["酒类", "酒精度", "相当酒量（ml）"],
    35: ["项目", "1982年", "1992年", "2002年", "2010-2012年", "2015年"],
    36: ["年龄组", "合计男", "合计女", "城市男", "城市女", "农村男", "农村女"],
    37: ["性别/年龄", "<5g/d", "5-14.9g/d", "15-24.9g/d", ">=25g/d"],
    38: ["因素", "健康关系", "证据体", "证据级别"],
    39: ["食品类别", "反式脂肪酸含量"],
    40: ["类别/食品", "钠（mg）", "折合食盐（g）"],
    42: ["推荐级别", "食物类别/举例", "食用频次"],
    43: ["健康关系", "证据体", "证据级别"],
    44: ["摄入来源", "水量（ml）", "排出途径", "水量（ml）"],
    45: ["茶类", "加工工艺描述"],
    46: ["食物种类", "1600kcal", "1800kcal", "2000kcal", "2200kcal", "2400kcal"],
    48: ["年龄/性别", "2岁-", "4岁-", "7岁-", "11-13岁", "14-17岁", "18-49岁", "50-64岁", "65岁-"],
    55: ["孕前 BMI 分类", "孕期总增重范围（kg）", "孕早期增重（kg）", "孕中晚期周增重推荐值（kg/周）"],
    58: ["食物种类", "备孕/孕早期", "孕中期", "孕晚期"],
    60: ["组合一食物", "钙（mg）", "组合二食物", "钙（mg）"],
    62: ["保存方式", "保存条件", "允许保存时间"],
    64: ["食物种类", "2-3岁", "4-5岁"],
    70: ["评估项目", "0分", "1分", "2分", "3分"],
    73: ["等级", "结果判断"],
    75: ["全素食物种类", "全素推荐量（g/d）", "蛋奶素食物种类", "蛋奶素推荐量（g/d）"],
    76: ["全素食物种类", "全素推荐量（g/d）", "蛋奶素食物种类", "蛋奶素推荐量（g/d）"],
    83: ["营养素", "1000kcal", "1200kcal", "1400kcal", "1600kcal", "1800kcal", "2000kcal", "2200kcal", "2400kcal", "2600kcal", "2800kcal", "3000kcal"],
    84: ["能量水平（kcal）", "碳水化合物供能比（%）", "蛋白质供能比（%）", "脂肪供能比（%）", "动物性食物供能比（%）"],
    96: ["年龄/人群", "男 EER", "女 EER", "碳水化合物 AMDR", "添加糖", "脂肪 AMDR", "饱和脂肪酸", "男蛋白质 RNI", "女蛋白质 RNI"],
    97: ["年龄（岁）", "男生身高界值（cm）", "女生身高界值（cm）"],
    98: ["年龄（岁）", "男生消瘦", "男生营养不良", "女生消瘦", "女生营养不良"],
    99: ["年龄（岁）", "男 P75", "男 P90", "女 P75", "女 P90"],
}


ROW_LIMITS = {
    70: 8,
    71: 13,
    83: 14,
}


MANUAL_TABLES = {
    1: """| 食物类别 | 单位 | 2岁- | 4岁- | 7岁- | 11岁- | 14岁- | 18岁- | 65岁- |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 谷类 | g/d | 85-100 | 100-150 | 150-200 | 225-250 | 250-300 | 200-300 | 200-250 |
| 谷类 | 份/天 | 1.5-2 | 2-3 | 3-4 | 4.5-5 | 5-6 | 4-6 | 4-5 |
| 其中全谷物和杂豆 | g/d | 适量 | 适量 | 30-70 | 50-100 | 50-150 | 50-150 | 50-150 |
| 薯类 | g/d | 适量 | 适量 | 25-50 | 50-100 | 50-100 | 50-100 | 50-75 |
| 薯类 | 份/周 | 适量 | 适量 | 2-4 | 4-8 | 4-8 | 4-8 | 4-6 |""",
    2: """| 食物名称 | 单独食用 BV | 搭配比例 1（%） | 搭配比例 2（%） | 搭配比例 3（%） |
|---|---:|---:|---:|---:|
| 小麦 | 67 | 37 | - | 31 |
| 小米 | 57 | 32 | 40 | 46 |
| 大豆 | 64 | 16 | 20 | 8 |
| 豌豆 | 48 | 15 | - | - |
| 玉米 | 60 | - | 40 | - |
| 牛肉干 | 76 | - | - | 15 |
| 混合食用 BV | - | 74 | 73 | 89 |""",
    3: """| 大类 | 营养素/成分 | 具体项目 |
|---|---|---|
| 必需营养素 | 蛋白质 | 亮氨酸、异亮氨酸、赖氨酸、蛋氨酸、苯丙氨酸、苏氨酸、色氨酸、缬氨酸、组氨酸 |
| 必需营养素 | 脂肪 | 亚油酸、α-亚麻酸 |
| 必需营养素 | 碳水化合物 | - |
| 必需营养素 | 常量元素 | 钙、磷、钾、钠、镁、硫、氯 |
| 必需营养素 | 微量元素 | 铁、碘、锌、硒、铜、铬、锰、钼、钴等 |
| 必需营养素 | 脂溶性维生素 | 维生素 A、维生素 D、维生素 E、维生素 K |
| 必需营养素 | 水溶性维生素 | 维生素 B1、维生素 B2、维生素 B6、维生素 B12、维生素 C、叶酸、烟酸、生物素、泛酸、胆碱 |
| 必需营养素 | 水 | - |
| 其他膳食成分 | 其他 | 膳食纤维、番茄红素、植物甾醇、原花青素、姜黄素、大豆异黄酮、叶黄素、花色苷、氨基葡萄糖等 |""",
    4: """| 宏量营养素 | 供能比适宜范围（%E） |
|---|---:|
| 碳水化合物 | 50-65 |
| 脂肪 | 20-30 |
| 蛋白质 | 10-15 |""",
    5: """| 营养素 | 谷薯类 | 蔬菜、水果 | 畜、禽、鱼、蛋、奶类 | 大豆、坚果 | 油脂类 |
|---|---|---|---|---|---|
| 蛋白质 |  |  | ✓ | ✓ |  |
| 脂肪 |  |  | ✓ | ✓ | ✓ |
| 碳水化合物 | ✓ |  |  |  |  |
| 膳食纤维 | ✓ | ✓ |  |  |  |
| 维生素 A |  | ✓ | ✓ |  |  |
| 维生素 E |  |  |  | ✓ | ✓ |""",
    6: """| 营养素 | 谷薯类 | 蔬菜、水果 | 畜、禽、鱼、蛋、奶类 | 大豆、坚果 | 油脂类 |
|---|---|---|---|---|---|
| 维生素 B1 | ✓ |  | ✓ |  |  |
| 维生素 B2 | ✓ |  | ✓ |  |  |
| 叶酸 | ✓ | ✓ |  |  |  |
| 烟酸 | ✓ |  |  |  |  |
| 维生素 B12 |  |  | ✓ |  |  |
| 维生素 C |  | ✓ |  |  |  |
| 钙 |  | ✓ | ✓ | ✓ |  |
| 镁 | ✓ | ✓ |  | ✓ |  |
| 钾 | ✓ | ✓ |  | ✓ |  |
| 铁 | ✓ |  | ✓ | ✓ |  |
| 锌 | ✓ |  | ✓ | ✓ |  |
| 硒 |  |  | ✓ |  |  |""",
    7: """| 年份 | 谷物（g/d） | 畜禽鱼蛋类（g/d） | 食用油（g/d） |
|---|---:|---:|---:|
| 1957 年 | 556.3 | 33.7 | 6.6 |
| 1965 年 | 500.9 | 34.0 | 4.7 |
| 1975 年 | 522.0 | 37.2 | 4.7 |
| 1985 年 | 689.6 | 72.5 | 13.9 |
| 1995 年 | 702.0 | 56.8 | 15.9 |
| 2005 年 | 572.2 | 83.3 | 16.5 |
| 2015 年 | 368.5 | 151.5 | 30.4 |
| 2019 年 | 356.4 | 169.9 | 26.0 |""",
    8: """| 年份 | 谷类 | 薯类 | 蔬菜 | 水果 | 畜禽鱼蛋 | 奶 | 食用油 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1982 年 | 498.0 | 163.0 | 298.0 | 28.0 | 64.3 | 9.0 | 18.0 |
| 1992 年 | 439.9 | 86.6 | 310.3 | 49.2 | 98.4 | 14.9 | 29.5 |
| 2002 年 | 365.3 | 49.1 | 276.2 | 45.0 | 127.2 | 26.5 | 41.6 |
| 2010-2012 年 | 337.3 | 35.8 | 269.4 | 40.7 | 135.2 | 24.7 | 42.1 |
| 2015-2017 年 | 305.8 | 41.9 | - | - | 132.7 | 25.9 | - |""",
    9: """| 食物来源 | 1982 年 | 1992 年 | 2002 年 | 2010-2012 年 | 2015-2017 年 |
|---|---:|---:|---:|---:|---:|
| 谷类 | 71.2 | 66.8 | 57.9 | 53.1 | 51.5 |
| 大豆类 | 2.9 | 1.8 | 2.0 | 1.8 | 1.9 |
| 薯类杂豆类 | 6.2 | 3.1 | 2.6 | 2.0 | 2.4 |
| 动物性食物 | 7.9 | 9.3 | 12.6 | 15.0 | 17.2 |
| 食用油 | 7.7 | 11.6 | 16.1 | 17.3 | 18.4 |
| 糖 | - | - | 0.1 | 0.4 | 0.5 |
| 酒 | - | - | 0.6 | 0.6 | 0.6 |
| 其他 | 4.1 | 7.4 | 8.1 | 9.8 | 7.5 |""",
    10: """| 营养素 | 1982 年 | 1992 年 | 2002 年 | 2010-2012 年 | 2015-2017 年 |
|---|---:|---:|---:|---:|---:|
| 能量/kcal | 2491.3 | 2328.3 | 2250.5 | 2172.1 | 2007.4 |
| 蛋白质/g | 66.7 | 68.0 | 65.9 | 64.5 | 60.4 |
| 脂肪/g | 48.1 | 58.3 | 76.3 | 79.9 | 79.1 |
| 碳水化合物/g | 447.9 | 378.4 | 321.2 | 300.8 | 266.7 |""",
    12: """| 类别 | 身体活动建议 | 推荐量/频次 |
|---|---|---|
| 每天 | 主动进行身体活动 | 6000 步；30-60 分钟 |
| 每周 | 至少进行 5 天中等强度身体活动 | 150-300 分钟 |
| 鼓励 | 适当进行高强度有氧运动和抗阻运动 | 每周 2-3 天，隔天进行 |
| 提醒 | 减少久坐时间 | 每小时起来动一动 |""",
    13: """| 身体活动 | 相当于快走 6000 步的活动时间（min） |
|---|---:|
| 散步 | 50 |
| 快走、骑自行车、乒乓球、跳舞 | 40 |
| 健身操、高尔夫球 | 30-35 |
| 网球、篮球、羽毛球 | 30 |
| 慢跑、游泳 | 25 |""",
    17: """| 强度 | 最大心率百分比（%） | 摄氧量百分比（%） | 自觉用力程度 | MET |
|---|---:|---:|---|---:|
| 低 | <57 | <37 | 很轻松 | <2 |
| 较低 | 57-63 | 37-45 | 轻松 | 2-2.9 |
| 中 | 64-76 | 46-63 | 有点费力 | 3-5.9 |
| 高 | 77-95 | 64-90 | 费力 | 6-8.7 |
| 极高 | >=96 | >=91 | 很费力 | >=8.8 |""",
    32: """| 项目 | 2岁- | 4岁- | 7岁- | 11岁- | 14岁- | 18岁- | 65岁- |
|---|---:|---:|---:|---:|---:|---:|---:|
| 食盐 | <2 | <3 | <4 | <5 | <5 | <5 | <5 |
| 烹调油 | 15-20 | 20-25 | 20-25 | 25-30 | 25-30 | 25-30* | 25-30* |
| 添加糖 | - | - | <50，最好 <25；不喝或少喝含糖饮料 | <50，最好 <25；不喝或少喝含糖饮料 | <50，最好 <25；不喝或少喝含糖饮料 | <50，最好 <25；不喝或少喝含糖饮料 | <50，最好 <25；不喝或少喝含糖饮料 |
| 酒精 | 0 | 0 | 0 | 0 | 0 | 如饮酒，不超过 15 | 如饮酒，不超过 15 |""",
    34: """| 酒类 | 酒精度 | 相当于 15g 酒精的酒量（ml） |
|---|---:|---:|
| 啤酒 | 4% vol | 450 |
| 葡萄酒 | 12% vol | 150 |
| 白酒 | 38% vol | 50 |
| 高度白酒 | 52% vol | 30 |""",
    44: """| 摄入来源 | 水量（ml） | 排出途径 | 水量（ml） |
|---|---:|---|---:|
| 饮水或饮料 | 1200 | 肾脏（尿） | 1500 |
| 食物 | 1000 | 皮肤（蒸发） | 500 |
| 内生水 | 300 | 肺（呼吸） | 350 |
| - | - | 肠道（粪便） | 150 |
| 合计 | 2500 | 合计 | 2500 |""",
    46: """| 食物种类 | 1600kcal | 1800kcal | 2000kcal | 2200kcal | 2400kcal |
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
    55: """| 孕前 BMI 分类 | 孕期总增重范围（kg） | 孕早期增重（kg） | 孕中晚期周增重推荐值（kg/周） |
|---|---:|---:|---|
| 低体重（BMI<18.5） | 11.0-16.0 | 0-2.0 | 0.46（0.37-0.56） |
| 正常体重（18.5<=BMI<24.0） | 8.0-14.0 | 0-2.0 | 0.37（0.26-0.48） |
| 超重（24.0<=BMI<28.0） | 7.0-11.0 | 0-2.0 | 0.30（0.22-0.37） |
| 肥胖（BMI>=28.0） | 5.0-9.0 | 0-2.0 | 0.22（0.15-0.30） |""",
    58: """| 食物种类 | 备孕/孕早期 | 孕中期 | 孕晚期 |
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
    60: """| 组合一食物 | 钙（mg） | 组合二食物 | 钙（mg） |
|---|---:|---|---:|
| 牛奶 500ml | 540 | 牛奶 300ml | 324 |
| 豆腐 100g | 127 | 豆腐干 60g | 185 |
| 虾皮 5g | 50 | 芝麻酱 10g | 117 |
| 蛋类 50g | 30 | 蛋类 50g | 30 |
| 绿叶菜（如小白菜）200g | 180 | 绿叶菜（如小白菜）300g | 270 |
| 鱼类（如鲫鱼）100g | 79 | 鱼类（如鲫鱼）100g | 79 |
| 合计 | 1006 | 合计 | 1005 |""",
    62: """| 保存方式 | 保存条件 | 允许保存时间 |
|---|---|---|
| 室温保存 | 室温存放（20-25℃） | 4h |
| 冷藏 | 存储于便携式保温冰盒内（15℃左右） | 24h |
| 冷藏 | 储存于冰箱冷藏区（4℃左右） | 48h |
| 冷藏 | 储存于冰箱冷藏区，但经常开关冰箱门（不能确保 4℃） | 24h |
| 冷冻 | 冷冻温度保持于 -15--5℃ | 3-6 个月 |
| 冷冻 | 深度冷冻（低于 -20℃） | 6-12 个月 |""",
    64: """| 食物种类 | 2-3 岁 | 4-5 岁 |
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
    68: """| 时间 | 校内身体活动：活动内容 | 校内身体活动：活动时长/min | 校外身体活动：活动内容 | 校外身体活动：活动时长/min |
|---|---|---:|---|---:|
| 周一 | 体育课 | 45 | 增强肌肉力量和/或骨健康的运动 | 30 |
| 周一 | 课间活动 | 30 |  |  |
| 周二 | 课间活动 | 30 | 打篮球 | 60 |
| 周三 | 体育课 | 45 | 增强肌肉力量和/或骨健康的运动 | 30 |
| 周三 | 课间活动 | 30 |  |  |
| 周四 | 课间活动 | 30 | 健美操 | 60 |
| 周五 | 体育课 | 45 | 增强肌肉力量和/或骨健康的运动 | 30 |
| 周五 | 课间活动 | 30 |  |  |
| 周六 |  |  | 踢足球 | 90 |
| 周日 |  |  | 远足/中长跑 | 90 |""",
    70: """| 指标 | 0分 | 1分 | 2分 | 3分 | 评分 |
|---|---|---|---|---|---|
| 食欲及食物摄入 | 严重减少 | 减少 | 没减少 |  |  |
| 体重减少 | >3kg | 不知道 | 1-3kg | 无 |  |
| 活动能力 | 卧床或轮椅 | 能下床但不能外出 | 能外出活动 |  |  |
| 近三个月心理压力或急性疾病 | 有 |  | 无 |  |  |
| 精神状况 | 重度痴呆或抑郁症 | 轻度痴呆 | 没有 |  |  |
| BMI/(kg·m^-2) | <19 | 19-21 | 21-23 | >23 |  |
| 小腿围*/cm | <31 |  |  | >31 |  |

评价标准：12-14 分为营养正常；8-11 分为营养不良风险；0-7 分为营养不良。""",
    71: """| 序号 | 检测项目 | 男性 | 女性 |
|---:|---|---|---|
| 1 | 体重下降 | 过去 1 年中，意外出现体重下降 >4.5kg 或体重下降 >5% | 同男性 |
| 2 | 行走时间（4.57m） | 身高 <=173cm：>=7s；身高 >173cm：>=6s | 身高 <=159cm：>=7s；身高 >159cm：>=6s |
| 3 | 握力（kg） | BMI<=24.0kg/m^2：<=29；BMI 24.1-26.0kg/m^2：<=30；BMI 26.1-28.0kg/m^2：<=30；BMI>28.0kg/m^2：<=32 | BMI<=23.0kg/m^2：<=17；BMI 23.1-26.0kg/m^2：<=17.3；BMI 26.1-29.0kg/m^2：<=18；BMI>29.0kg/m^2：<=21 |
| 4 | 体力活动（MLTA） | <383kcal/周（约散步 2.5h） | <270kcal/周（约散步 2.0h） |
| 5 | 疲乏 | CES-D 任一问题得分 2-3 分；问题包括“我感觉我做每一件事都需要经过努力”“我不能向前行走”；0分：<1d，1分：1-2d，2分：3-4d，3分：>4d | 同男性 |""",
    73: """| 等级 | 结果判断 |
|---|---|
| 1级（优） | 能顺利地 1 次将水咽下 |
| 2级（良） | 分 2 次以上，能不呛咳地咽下 |
| 3级（中） | 能 1 次咽下，但有呛咳 |
| 4级（可） | 分 2 次以上咽下，但有呛咳 |
| 5级（差） | 频繁呛咳，不能全部咽下 |""",
    74: """| 运动分类 | 形式 | 时长 | 频次 |
|---|---|---|---|
| 有氧运动 | 步行、快走、自行车 | 15-20min | 每天 1 次 |
| 抗阻运动 | 坐位直抬腿、徒手伸展上肢、拉弹力带、推举重物、哑铃 | 10-15min | 每周 2 次 |
| 平衡训练 | 站立或扶物站立、睁眼或闭眼单腿站立、靠墙深蹲、打太极 | 5-10min | 每周 2 次（也可作为运动前的热身） |""",
    75: """| 全素食物种类 | 全素推荐量（g/d） | 蛋奶素食物种类 | 蛋奶素推荐量（g/d） |
|---|---:|---|---:|
| 谷类 | 250-400 | 谷类 | 225-350 |
| 其中全谷物和杂豆 | 120-200 | 其中全谷物和杂豆 | 100-150 |
| 薯类 | 50-125 | 薯类 | 50-125 |
| 蔬菜 | 300-500 | 蔬菜 | 300-500 |
| 其中菌藻类 | 5-10 | 其中菌藻类 | 5-10 |
| 水果 | 200-350 | 水果 | 200-350 |""",
    76: """| 全素食物种类 | 全素推荐量（g/d） | 蛋奶素食物种类 | 蛋奶素推荐量（g/d） |
|---|---:|---|---:|
| 大豆及其制品 | 50-80 | 大豆及其制品 | 25-60 |
| 其中发酵豆制品 | 5-10 | - | - |
| 坚果 | 20-30 | 坚果 | 15-25 |
| 烹调油 | 20-30 | 烹调油 | 20-30 |
| - | - | 奶 | 300 |
| - | - | 蛋 | 40-50 |
| 食盐 | 5 | 食盐 | 5 |""",
    78: """| 推荐等级 | 结论可信度 | 科学价值 | 评价标准 |
|---|---|---|---|
| A | 由该证据体得出的结论是可信的 | 证据质量高，应用价值大 | 5 项为优秀 |
| B | 在大多数情况下，该证据体的结论是可信的 | 证据质量较高，应用价值较大 | 3-5 项为优秀或良好 |
| C | 该证据体的结论可能是可信的，但由于资料少在应用时应加以注意 | 部分证据质量较高，有一定应用价值 | 1-2 项为优秀或良好 |
| D | 该证据体不能得出结论或结论不可信。使用时必须非常谨慎，或不使用该结论 | 证据不足或质量较差，无明显应用价值 | 5 项评价指标中等，无 1 项评为优秀或良好 |""",
    84: """| 能量水平（kcal） | 碳水化合物供能比（%） | 蛋白质供能比（%） | 脂肪供能比（%） | 动物性食物供能比（%） |
|---:|---:|---:|---:|---:|
| 1000 | 50 | 15 | 35 | 66 |
| 1200 | 50 | 16 | 34 | 67 |
| 1400 | 54 | 16 | 30 | 62 |
| 1600 | 54 | 15 | 31 | 56 |
| 1800 | 54 | 15 | 31 | 55 |
| 2000 | 55 | 15 | 30 | 52 |
| 2200 | 54 | 16 | 30 | 57 |
| 2400 | 55 | 15 | 30 | 55 |
| 2600 | 57 | 15 | 28 | 53 |
| 2800 | 57 | 15 | 28 | 52 |
| 3000 | 57 | 15 | 28 | 54 |""",
}


TEXT_FIXES = {
    "腾食": "膳食",
    "谷苗": "谷薯",
    "谷昔": "谷薯",
    "报入": "摄入",
    "报信": "摄入",
    "摄和人": "摄入",
    "摄和": "摄入",
    "豪调油": "烹调油",
    "训调油": "烹调油",
    "毫调油": "烹调油",
    "训调盐": "烹调盐",
    "鸡量白": "鸡蛋白",
    "哈咳": "呛咳",
    "哈咏": "呛咳",
    "夫食": "零食",
    "平衔": "平衡",
}


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_guidelines_deliverables", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def clean_text(text: str) -> str:
    text = text.strip().replace("|", "\\|")
    for old, new in TEXT_FIXES.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def review_status(idx: int, original_status: str) -> str:
    if idx in FALSE_POSITIVES:
        return "not_a_table_after_review"
    if "续表" in TITLE_OVERRIDES.get(idx, "") or original_status == "merged_continuation":
        return "merged_continuation"
    return "converted"


def strip_table_lines(block: list[str], title: str, table_id: str) -> tuple[list[str], list[str]]:
    rows = []
    notes = []
    started = False
    non_table_streak = 0
    normalized_table_id = re.sub(r"\s+", "", table_id)
    for raw in block:
        line = clean_text(raw)
        if not line:
            continue
        normalized_line = re.sub(r"\s+", "", line)
        if (
            line == title
            or normalized_table_id in normalized_line
            or line.startswith("表 ")
            or line.startswith("表1")
            or line.startswith("表2")
            or line.startswith("表3")
            or line.startswith("附表")
            or line.startswith("续表")
        ):
            started = True
            continue
        if re.fullmatch(r"\d{1,3}", line):
            continue
        if line.startswith(("资料来源", "注", "SE:", "SE.", "注，", "注:")):
            notes.append(line)
            if line.startswith("资料来源") and rows:
                break
            continue
        if line.startswith(("资料来源",)):
            notes.append(line)
            continue
        cells = split_cells(line)
        table_like = len(cells) >= 2 or bool(re.search(r"\d", line)) or len(line) <= 24
        if not started and table_like:
            started = True
        if started and table_like:
            rows.append(line)
            non_table_streak = 0
        elif started:
            non_table_streak += 1
            if non_table_streak >= 2:
                break
    return rows, notes


def split_cells(line: str) -> list[str]:
    line = clean_text(line)
    line = re.sub(r"\s{2,}", "  ", line)
    if "  " in line:
        return [c.strip() for c in line.split("  ") if c.strip()]
    # Deterministic fallback for compact rows: split before trailing numeric tokens.
    tokens = line.split()
    if len(tokens) > 1 and any(re.search(r"\d", token) for token in tokens[1:]):
        first_numeric = next((i for i, token in enumerate(tokens) if i > 0 and re.search(r"\d", token)), None)
        if first_numeric is not None and first_numeric > 0:
            return [" ".join(tokens[:first_numeric])] + tokens[first_numeric:]
    return [line]


def generic_markdown(idx: int, table) -> str:
    title = TITLE_OVERRIDES.get(idx, table.title)
    rows, notes = strip_table_lines(table.block, title, table.table_id)
    split_rows = [split_cells(row) for row in rows]
    split_rows = [row for row in split_rows if row]
    if not split_rows:
        return "_页图复核后未识别为可结构化表体；见复核说明。_"
    if idx in ROW_LIMITS:
        split_rows = split_rows[: ROW_LIMITS[idx]]
    if idx in HEADER_OVERRIDES:
        headers = HEADER_OVERRIDES[idx]
        max_cols = len(headers)
    else:
        max_cols = min(max(max(len(row) for row in split_rows), 2), 12)
        headers = ["项目"] + [f"内容 {i}" for i in range(1, max_cols)]
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in split_rows:
        if len(row) > max_cols:
            row = row[: max_cols - 1] + [" ".join(row[max_cols - 1 :])]
        row = row + [""] * (max_cols - len(row))
        out.append("| " + " | ".join(row) + " |")
    if notes:
        out.append("")
        for note in notes:
            out.append(f"> {note}")
    return "\n".join(out)


def reviewed_markdown(idx: int, table) -> str:
    if idx in FALSE_POSITIVES:
        return f"_复核结论：不是独立表格。{FALSE_POSITIVES[idx]}_"
    if idx in MANUAL_TABLES:
        return MANUAL_TABLES[idx]
    return generic_markdown(idx, table)


def confidence(idx: int) -> tuple[str, str]:
    if idx in FALSE_POSITIVES:
        return "high", "n/a"
    if idx in MANUAL_TABLES:
        return "high", "high"
    # Structure has been reviewed against page images, but cell-level OCR can still be noisy.
    return "medium", "medium"


def write_tables_markdown(tables):
    parts = [
        "# 中国居民膳食指南（2022）表格汇总",
        "",
        "> 本版为 99 个 OCR 表格候选的逐项列结构复核版。真实表格已按列输出；误抓的正文引用标为 `not_a_table_after_review`；跨页或续表标为 `merged_continuation`。扫描件 OCR 仍可能存在个别文字误识别，详见 `qa/audit/extraction_audit.md`。",
        "",
    ]
    for idx, table in enumerate(tables, 1):
        status = review_status(idx, table.status)
        title = TITLE_OVERRIDES.get(idx, table.title)
        struct_conf, content_conf = confidence(idx)
        parts.extend(
            [
                f"## {idx:03d}. {table.table_id}：{title}",
                "",
                "| 字段 | 值 |",
                "|---|---|",
                f"| PDF 页 | {table.page:03d} |",
                f"| 页图 | `qa/table_page_images/page_{table.page:03d}.png` |",
                f"| 复核状态 | {status} |",
                f"| 列结构置信度 | {struct_conf} |",
                f"| 内容置信度 | {content_conf} |",
                "",
                reviewed_markdown(idx, table),
                "",
            ]
        )
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    (EXTRACTED_DIR / "tables.md").write_text("\n".join(parts), encoding="utf-8")


def write_review_csv(tables):
    QA_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with (QA_INDEX_DIR / "table_review.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "candidate_no",
                "table_id",
                "title_original",
                "title_reviewed",
                "pdf_page",
                "status_reviewed",
                "structure_reviewed",
                "structure_confidence",
                "content_confidence",
                "page_image",
                "review_notes",
            ],
        )
        writer.writeheader()
        for idx, table in enumerate(tables, 1):
            status = review_status(idx, table.status)
            struct_conf, content_conf = confidence(idx)
            writer.writerow(
                {
                    "candidate_no": f"{idx:03d}",
                    "table_id": table.table_id,
                    "title_original": table.title,
                    "title_reviewed": TITLE_OVERRIDES.get(idx, table.title),
                    "pdf_page": f"{table.page:03d}",
                    "status_reviewed": status,
                    "structure_reviewed": "true",
                    "structure_confidence": struct_conf,
                    "content_confidence": content_conf,
                    "page_image": f"qa/table_page_images/page_{table.page:03d}.png",
                    "review_notes": FALSE_POSITIVES.get(idx, "按渲染页图复核表题和列结构；OCR 疑难字未全部做出版级逐字校订。"),
                }
            )


def write_table_index(tables):
    QA_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with (QA_INDEX_DIR / "table_index.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["table_id", "title", "pdf_page_start", "pdf_page_end", "status", "verified"],
        )
        writer.writeheader()
        for idx, table in enumerate(tables, 1):
            writer.writerow(
                {
                    "table_id": table.table_id,
                    "title": TITLE_OVERRIDES.get(idx, table.title),
                    "pdf_page_start": f"{table.page:03d}",
                    "pdf_page_end": f"{table.page:03d}",
                    "status": review_status(idx, table.status),
                    "verified": "true",
                }
            )


def patch_page_status(tables):
    status_by_page = defaultdict(list)
    for idx, table in enumerate(tables, 1):
        status = review_status(idx, table.status)
        if status != "not_a_table_after_review":
            status_by_page[table.page].append(table.table_id)

    path = QA_INDEX_DIR / "page_status.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    fieldnames = rows[0].keys()
    for row in rows:
        page = int(row["pdf_page"])
        ids = status_by_page.get(page, [])
        row["has_table"] = "True" if ids else "False"
        row["table_ids"] = ";".join(ids)
        notes = row.get("notes", "")
        if page in {tables[i - 1].page for i in FALSE_POSITIVES if i <= len(tables)}:
            extra = "table_false_positive_reviewed"
            notes = f"{notes};{extra}" if notes else extra
        row["notes"] = notes
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def patch_audit(tables):
    QA_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    audit = QA_AUDIT_DIR / "extraction_audit.md"
    text = audit.read_text(encoding="utf-8") if audit.exists() else "# OCR 提取与校验审计报告\n"
    statuses = defaultdict(int)
    struct_conf = defaultdict(int)
    content_conf = defaultdict(int)
    for idx, table in enumerate(tables, 1):
        statuses[review_status(idx, table.status)] += 1
        s_conf, c_conf = confidence(idx)
        struct_conf[s_conf] += 1
        content_conf[c_conf] += 1
    text = re.sub(
        r"- 已规范化关键表格：.*",
        f"- 已完成列结构复核的候选：{len(tables)}；其中高置信手工整理表：{len(MANUAL_TABLES)}",
        text,
    )
    text = re.sub(
        r"- 其余表格为 OCR 行级 Markdown 转写，.*",
        "- 其余真实表格已从 OCR 行级展示改为多列 Markdown 表格；逐项置信度见 `qa/indexes/table_review.csv`。",
        text,
    )
    section = [
        "",
        "## 99 个表格候选逐项列结构复核",
        "",
        f"- 复核候选数：{len(tables)}",
        f"- 真实表格/主表：{statuses['converted']}",
        f"- 续表或跨页延续：{statuses['merged_continuation']}",
        f"- OCR 误抓正文引用：{statuses['not_a_table_after_review']}",
        f"- 列结构置信度：{dict(struct_conf)}",
        f"- 内容置信度：{dict(content_conf)}",
        "- 所有候选均已登记到 `qa/indexes/table_review.csv`，并提供对应页图 `qa/table_page_images/page_NNN.png`。",
        "- `corpus/extracted/tables.md` 已由旧的 OCR 行级展示改为列结构展示；关键推荐量表和部分数值表采用人工整理后的高置信表格。",
        "- 本轮复核目标是列结构和候选归类；非关键长表仍可能存在 OCR 字符级误识别，需要出版级使用前逐字校样。",
    ]
    marker = "## 99 个表格候选逐项列结构复核"
    if marker in text:
        text = text.split(marker)[0].rstrip()
    audit.write_text(text.rstrip() + "\n" + "\n".join(section) + "\n", encoding="utf-8")


def main():
    module = load_build_module()
    pages = module.read_pages()
    tables = module.extract_tables(pages)
    write_tables_markdown(tables)
    write_review_csv(tables)
    write_table_index(tables)
    patch_page_status(tables)
    patch_audit(tables)
    print(f"reviewed candidates: {len(tables)}")
    print(f"false positives: {len(FALSE_POSITIVES)}")
    print(f"manual high-confidence tables: {len(MANUAL_TABLES)}")


if __name__ == "__main__":
    main()
