#!/usr/bin/env python3
"""Local diet log and Chinese Dietary Guidelines summary/recommendation helper."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


DEFAULT_DATA_DIR = Path("~/.codex/data/chinese-dietary-guidelines").expanduser()
SCHEMA_VERSION = 1

GROUPS = {
    "grains",
    "whole_grains_legumes",
    "tubers",
    "vegetables",
    "dark_vegetables",
    "fruits",
    "dairy",
    "fish",
    "poultry",
    "meat",
    "eggs",
    "soy",
    "fermented_soy",
    "nuts",
    "fungi_algae",
    "oil",
    "salt",
    "added_sugar",
    "water",
    "alcohol",
    "other",
}

MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack", "day", "other"}
NO_HIGH_GROUPS = {"soy", "soy_nuts", "fermented_soy", "nuts", "dairy"}

UNIT_GRAMS = {
    "g": 1,
    "gram": 1,
    "grams": 1,
    "克": 1,
    "kg": 1000,
    "公斤": 1000,
    "千克": 1000,
    "bowl": 250,
    "碗": 250,
    "cup": 250,
    "杯": 250,
    "serving": 100,
    "份": 100,
    "piece": 50,
    "个": 50,
    "只": 50,
    "egg": 50,
    "枚": 50,
    "handful": 25,
    "把": 25,
    "spoon": 10,
    "勺": 10,
}

KEYWORDS = [
    ("whole_grains_legumes", ["燕麦", "糙米", "玉米", "全麦", "荞麦", "红豆", "绿豆", "杂豆", "鹰嘴豆"]),
    ("tubers", ["土豆", "马铃薯", "红薯", "甘薯", "山药", "芋头"]),
    ("dark_vegetables", ["菠菜", "油菜", "西兰花", "胡萝卜", "南瓜", "苋菜", "芥蓝", "空心菜"]),
    ("vegetables", ["蔬菜", "白菜", "生菜", "黄瓜", "番茄", "西红柿", "茄子", "菜花"]),
    ("fruits", ["苹果", "香蕉", "橙", "橘", "梨", "葡萄", "水果", "草莓", "蓝莓"]),
    ("dairy", ["牛奶", "酸奶", "奶酪", "奶粉", "乳"]),
    ("fish", ["鱼", "虾", "蟹", "贝", "海鲜"]),
    ("poultry", ["鸡", "鸭", "鹅"]),
    ("meat", ["猪", "牛", "羊", "肉", "火腿", "香肠"]),
    ("eggs", ["鸡蛋", "鸭蛋", "蛋"]),
    ("fermented_soy", ["腐乳", "豆豉", "纳豆", "发酵豆"]),
    ("soy", ["豆腐", "豆浆", "大豆", "黄豆", "豆干", "豆皮"]),
    ("nuts", ["坚果", "核桃", "花生", "杏仁", "腰果", "瓜子"]),
    ("fungi_algae", ["蘑菇", "香菇", "木耳", "海带", "紫菜", "菌", "藻"]),
    ("grains", ["米饭", "米", "面", "面条", "馒头", "包子", "面包", "粥", "粉"]),
    ("oil", ["油"]),
    ("salt", ["盐"]),
    ("added_sugar", ["糖", "甜饮料", "可乐", "奶茶", "甜点"]),
    ("water", ["水", "茶"]),
    ("alcohol", ["酒", "啤酒", "葡萄酒", "白酒"]),
]


RULES: dict[str, dict[str, Any]] = {
    "adult": {
        "label": "一般成人",
        "sources": "PDF 003, 009-011, 153",
        "targets": {
            "grains": (200, 300),
            "whole_grains_legumes": (50, 150),
            "tubers": (50, 100),
            "vegetables": (300, 500),
            "fruits": (200, 350),
            "dairy": (300, 500),
            "animal_foods": (120, 200),
            "soy_nuts": (25, 35),
            "oil": (None, 30),
            "salt": (None, 5),
            "added_sugar": (None, 50),
            "alcohol": (None, 15),
        },
        "water": {"male": 1700, "female": 1500, "default": 1500},
        "weekly": {"fish": (300, 500), "food_variety": (25, None)},
        "notes": [
            "每天 12 种以上食物、每周 25 种以上。",
            "深色蔬菜宜占蔬菜约 1/2。",
            "每周至少 150 分钟中等强度身体活动，主动活动约 6000 步/日。",
        ],
    },
    "pregnant_early": {
        "label": "备孕/孕早期",
        "sources": "PDF 192, 197",
        "targets": {
            "grains": (200, 250),
            "tubers": (50, 50),
            "vegetables": (300, 500),
            "fruits": (200, 300),
            "animal_foods": (130, 180),
            "dairy": (300, 300),
            "soy": (15, 15),
            "nuts": (10, 10),
            "oil": (None, 25),
            "salt": (None, 5),
        },
        "water": {"default": 1700},
        "weekly": {},
        "notes": ["不做减重建议；关注含铁食物、碘盐、叶酸和维生素 D。"],
    },
    "pregnant_mid": {
        "label": "孕中期",
        "sources": "PDF 192, 197",
        "targets": {
            "grains": (200, 250),
            "tubers": (75, 75),
            "vegetables": (400, 500),
            "fruits": (200, 300),
            "animal_foods": (150, 200),
            "dairy": (300, 500),
            "soy": (20, 20),
            "nuts": (10, 10),
            "oil": (None, 25),
            "salt": (None, 5),
        },
        "water": {"default": 1700},
        "weekly": {},
        "notes": ["不做减重建议；适量增加奶、鱼、禽、蛋、瘦肉。"],
    },
    "pregnant_late": {
        "label": "孕晚期",
        "sources": "PDF 192, 197",
        "targets": {
            "grains": (225, 275),
            "tubers": (75, 75),
            "vegetables": (400, 500),
            "fruits": (200, 350),
            "animal_foods": (175, 225),
            "dairy": (300, 500),
            "soy": (20, 20),
            "nuts": (10, 10),
            "oil": (None, 25),
            "salt": (None, 5),
        },
        "water": {"default": 1700},
        "weekly": {},
        "notes": ["不做减重建议；保持孕期体重适宜增长。"],
    },
    "lactating": {
        "label": "哺乳期",
        "sources": "PDF 200, 202-204",
        "targets": {
            "grains": (225, 275),
            "tubers": (75, 75),
            "vegetables": (400, 500),
            "fruits": (200, 350),
            "animal_foods": (175, 225),
            "dairy": (300, 500),
            "soy": (25, 25),
            "nuts": (10, 10),
            "oil": (None, 25),
            "salt": (None, 5),
        },
        "water": {"default": 2100},
        "weekly": {},
        "notes": ["增加汤水和饮水；忌烟酒，限制浓茶和咖啡。"],
    },
    "preschool_2_3": {
        "label": "2-3 岁学龄前儿童",
        "sources": "PDF 260-261",
        "targets": {
            "grains": (75, 125),
            "vegetables": (100, 200),
            "fruits": (100, 200),
            "meat_fish_poultry": (50, 75),
            "eggs": (50, 50),
            "dairy": (350, 500),
            "soy": (5, 15),
            "oil": (None, 20),
            "salt": (None, 2),
        },
        "water": {"default": 650},
        "weekly": {},
        "notes": ["不做减重建议；每天三次正餐和两次加餐，户外活动至少 120 分钟。"],
    },
    "preschool_4_5": {
        "label": "4-5 岁学龄前儿童",
        "sources": "PDF 260-261",
        "targets": {
            "grains": (100, 150),
            "vegetables": (150, 300),
            "fruits": (150, 250),
            "meat_fish_poultry": (50, 75),
            "eggs": (50, 50),
            "dairy": (350, 500),
            "soy": (15, 20),
            "oil": (None, 25),
            "salt": (None, 3),
        },
        "water": {"default": 750},
        "weekly": {},
        "notes": ["不做减重建议；每天三次正餐和两次加餐，户外活动至少 120 分钟。"],
    },
    "school_age": {
        "label": "6-17 岁学龄儿童青少年",
        "sources": "PDF 266-267",
        "targets": {
            "dairy": (300, None),
            "added_sugar": (None, 50),
            "alcohol": (None, 0),
        },
        "water": {"default": 1200},
        "weekly": {},
        "notes": ["每天至少 60 分钟中高强度身体活动；早餐应包含 3 类及以上食物。"],
    },
    "older_adult": {
        "label": "65-79 岁老年人",
        "sources": "PDF 277-284",
        "targets": {
            "animal_foods": (120, 150),
            "fish": (40, 50),
            "meat": (40, 50),
            "eggs": (40, 50),
            "dairy": (300, 400),
            "soy": (15, 15),
            "salt": (None, 5),
        },
        "water": {"default": 1500},
        "weekly": {},
        "notes": ["保持食物细软、多样和足量蛋白；适宜 BMI 约 20.0-26.9 kg/m²。"],
    },
    "very_old": {
        "label": "80 岁及以上高龄老年人",
        "sources": "PDF 277-284",
        "targets": {
            "animal_foods": (120, 150),
            "dairy": (300, 400),
            "soy": (15, 15),
            "salt": (None, 5),
        },
        "water": {"default": 1500},
        "weekly": {},
        "notes": ["选择细软、能量和营养素密度高的食物；体重下降或摄入不足应就医评估。"],
    },
    "vegan": {
        "label": "全素成年人",
        "sources": "PDF 294-299",
        "targets": {
            "grains": (250, 400),
            "whole_grains_legumes": (120, 200),
            "tubers": (50, 125),
            "vegetables": (300, 500),
            "fungi_algae": (5, 10),
            "fruits": (200, 350),
            "soy": (50, 80),
            "fermented_soy": (5, 10),
            "nuts": (20, 30),
            "oil": (None, 30),
            "salt": (None, 5),
        },
        "water": {"default": 1500},
        "weekly": {"food_variety": (25, None)},
        "notes": ["关注维生素 B12、维生素 D、钙、铁、锌和 n-3 脂肪酸。"],
    },
    "lacto_ovo_vegetarian": {
        "label": "蛋奶素成年人",
        "sources": "PDF 294-299",
        "targets": {
            "grains": (225, 350),
            "whole_grains_legumes": (100, 150),
            "tubers": (50, 125),
            "vegetables": (300, 500),
            "fungi_algae": (5, 10),
            "fruits": (200, 350),
            "soy": (25, 60),
            "nuts": (15, 25),
            "oil": (None, 30),
            "dairy": (300, 300),
            "eggs": (40, 50),
            "salt": (None, 5),
        },
        "water": {"default": 1500},
        "weekly": {"food_variety": (25, None)},
        "notes": ["关注维生素 B12、维生素 D、钙、铁、锌和 n-3 脂肪酸。"],
    },
}


def data_paths(data_dir: Path) -> dict[str, Path]:
    return {
        "root": data_dir,
        "profile": data_dir / "profile.json",
        "log": data_dir / "diet_log.jsonl",
        "recommendations": data_dir / "recommendations",
    }


def ensure_dirs(data_dir: Path) -> None:
    paths = data_paths(data_dir)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["recommendations"].mkdir(parents=True, exist_ok=True)


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD date, got {value!r}") from exc


def load_json_arg(value: str) -> Any:
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def infer_group(name: str) -> str:
    for group, words in KEYWORDS:
        if any(word in name for word in words):
            return group
    return "other"


def estimate_grams(amount: Any, unit: str | None, group: str) -> tuple[float | None, str]:
    if amount in (None, ""):
        return None, "low"
    try:
        numeric = float(amount)
    except (TypeError, ValueError):
        return None, "low"
    if numeric < 0:
        return numeric, "low"
    normalized = (unit or "g").strip()
    if normalized in {"ml", "毫升"}:
        if group in {"water", "dairy", "alcohol"}:
            return numeric, "medium"
        return numeric, "low"
    factor = UNIT_GRAMS.get(normalized)
    if factor is None:
        return None, "low"
    confidence = "high" if factor == 1 else "medium"
    return round(numeric * factor, 1), confidence


def normalize_food(raw: dict[str, Any]) -> dict[str, Any]:
    name = str(raw.get("name", "")).strip()
    if not name:
        raise ValueError("food.name is required")
    group = str(raw.get("group") or infer_group(name)).strip()
    if group not in GROUPS:
        raise ValueError(f"unknown food group {group!r} for {name!r}")
    amount = raw.get("amount")
    unit = raw.get("unit") or "g"
    grams = raw.get("estimated_grams")
    inferred_confidence = "high"
    if grams in (None, ""):
        grams, inferred_confidence = estimate_grams(amount, unit, group)
    else:
        try:
            grams = round(float(grams), 1)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid estimated_grams for {name!r}") from exc
    confidence = raw.get("confidence") or inferred_confidence
    if confidence not in {"high", "medium", "low"}:
        raise ValueError(f"invalid confidence {confidence!r} for {name!r}")
    return {
        "name": name,
        "amount": amount,
        "unit": unit,
        "estimated_grams": grams,
        "group": group,
        "subgroup": raw.get("subgroup", ""),
        "preparation": raw.get("preparation", ""),
        "confidence": confidence,
    }


def parse_food_spec(spec: str) -> dict[str, Any]:
    parts = [part.strip() for part in spec.split("|")]
    if len(parts) not in {1, 4}:
        raise ValueError("--food must be 'name|amount|unit|group' or just 'name'")
    if len(parts) == 1:
        return normalize_food({"name": parts[0]})
    return normalize_food({"name": parts[0], "amount": parts[1], "unit": parts[2], "group": parts[3]})


def load_profile(data_dir: Path, required: bool = False) -> dict[str, Any]:
    profile_path = data_paths(data_dir)["profile"]
    if not profile_path.exists():
        if required:
            raise SystemExit(
                f"Profile not found at {profile_path}. Run: diet_log.py init-profile --sex ... --age ... --life-stage adult"
            )
        return {}
    return json.loads(profile_path.read_text(encoding="utf-8"))


def write_profile(args: argparse.Namespace) -> None:
    data_dir = args.data_dir
    ensure_dirs(data_dir)
    profile_path = data_paths(data_dir)["profile"]
    profile = load_profile(data_dir, required=False)
    updates = {
        "sex": args.sex,
        "age": args.age,
        "height_cm": args.height_cm,
        "weight_kg": args.weight_kg,
        "activity_level": args.activity_level,
        "life_stage": args.life_stage,
        "vegetarian_type": args.vegetarian_type,
        "allergies": args.allergy or [],
        "avoid_foods": args.avoid_food or [],
        "chronic_condition_notes": args.chronic_condition_note or "",
    }
    for key, value in updates.items():
        if value not in (None, "", []):
            profile[key] = value
    profile.setdefault("life_stage", "adult")
    profile.setdefault("vegetarian_type", "none")
    profile["updated_at"] = datetime.now().isoformat(timespec="seconds")
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote profile: {profile_path}")


def build_entry(args: argparse.Namespace) -> dict[str, Any]:
    foods: list[dict[str, Any]] = []
    for spec in args.food or []:
        foods.append(parse_food_spec(spec))
    for raw in args.food_json or []:
        foods.append(normalize_food(load_json_arg(raw)))
    if args.foods_json:
        raw_foods = load_json_arg(args.foods_json)
        if not isinstance(raw_foods, list):
            raise ValueError("--foods-json must be a JSON array")
        foods.extend(normalize_food(item) for item in raw_foods)
    metrics = {
        "water_ml": args.water_ml,
        "alcohol_g": args.alcohol_g,
        "oil_g": args.oil_g,
        "salt_g": args.salt_g,
        "added_sugar_g": args.added_sugar_g,
        "activity_steps": args.activity_steps,
    }
    if not foods and all(value is None for value in metrics.values()):
        raise ValueError("add at least one food or metric")
    entry_date = args.date.isoformat()
    return {
        "schema_version": SCHEMA_VERSION,
        "id": f"{entry_date}-{args.meal_type}-{datetime.now().strftime('%H%M%S')}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "date": entry_date,
        "meal_type": args.meal_type,
        "foods": foods,
        **metrics,
        "notes": args.notes or "",
    }


def add_entry(args: argparse.Namespace) -> None:
    ensure_dirs(args.data_dir)
    entry = build_entry(args)
    errors = validate_entry(entry)
    if errors:
        raise SystemExit("Invalid entry:\n- " + "\n- ".join(errors))
    log_path = data_paths(args.data_dir)["log"]
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Appended entry: {log_path}")
    print(entry["id"])


def load_entries(data_dir: Path) -> list[dict[str, Any]]:
    log_path = data_paths(data_dir)["log"]
    if not log_path.exists():
        return []
    entries = []
    for line_no, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{log_path}:{line_no}: invalid JSON: {exc}") from exc
    return entries


def validate_entry(entry: dict[str, Any]) -> list[str]:
    errors = []
    if entry.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    try:
        parse_date(str(entry.get("date", "")))
    except argparse.ArgumentTypeError as exc:
        errors.append(str(exc))
    if entry.get("meal_type") not in MEAL_TYPES:
        errors.append(f"meal_type must be one of {sorted(MEAL_TYPES)}")
    foods = entry.get("foods")
    if not isinstance(foods, list):
        errors.append("foods must be a list")
    else:
        for index, food in enumerate(foods):
            if not isinstance(food, dict):
                errors.append(f"foods[{index}] must be an object")
                continue
            if not food.get("name"):
                errors.append(f"foods[{index}].name is required")
            if food.get("group") not in GROUPS:
                errors.append(f"foods[{index}].group is unknown: {food.get('group')!r}")
            grams = food.get("estimated_grams")
            if grams is not None:
                try:
                    if float(grams) < 0:
                        errors.append(f"foods[{index}].estimated_grams must not be negative")
                except (TypeError, ValueError):
                    errors.append(f"foods[{index}].estimated_grams must be numeric or null")
    for key in ["water_ml", "alcohol_g", "oil_g", "salt_g", "added_sugar_g", "activity_steps"]:
        value = entry.get(key)
        if value is not None:
            try:
                if float(value) < 0:
                    errors.append(f"{key} must not be negative")
            except (TypeError, ValueError):
                errors.append(f"{key} must be numeric or null")
    return errors


def select_rule(profile: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    stage = profile.get("life_stage") or "adult"
    vegetarian = profile.get("vegetarian_type") or "none"
    if stage in RULES and stage != "adult":
        return stage, RULES[stage]
    if vegetarian == "vegan":
        return "vegan", RULES["vegan"]
    if vegetarian in {"lacto_ovo", "lacto_ovo_vegetarian"}:
        return "lacto_ovo_vegetarian", RULES["lacto_ovo_vegetarian"]
    return "adult", RULES["adult"]


def in_period(entry: dict[str, Any], start: date, end: date) -> bool:
    try:
        day = parse_date(str(entry.get("date")))
    except argparse.ArgumentTypeError:
        return False
    return start <= day <= end


def add_total(totals: defaultdict[str, float], group: str, grams: float) -> None:
    totals[group] += grams
    if group == "whole_grains_legumes":
        totals["grains"] += grams
    if group == "dark_vegetables":
        totals["vegetables"] += grams
    if group in {"fish", "poultry", "meat", "eggs"}:
        totals["animal_foods"] += grams
    if group in {"fish", "poultry", "meat"}:
        totals["meat_fish_poultry"] += grams
    if group in {"soy", "fermented_soy", "nuts"}:
        totals["soy_nuts"] += grams
        if group == "fermented_soy":
            totals["soy"] += grams


def summarize(data_dir: Path, days: int, until: date | None = None) -> dict[str, Any]:
    profile = load_profile(data_dir, required=True)
    until = until or date.today()
    start = until - timedelta(days=days - 1)
    entries = [entry for entry in load_entries(data_dir) if in_period(entry, start, until)]
    totals: defaultdict[str, float] = defaultdict(float)
    daily_foods: defaultdict[str, set[str]] = defaultdict(set)
    confidence = Counter()
    metric_keys = ["water_ml", "alcohol_g", "oil_g", "salt_g", "added_sugar_g", "activity_steps"]
    for entry in entries:
        day = entry["date"]
        for food in entry.get("foods", []):
            grams = food.get("estimated_grams")
            confidence[food.get("confidence", "low")] += 1
            daily_foods[day].add(food.get("name", ""))
            if grams is None:
                continue
            add_total(totals, food["group"], float(grams))
        for key in metric_keys:
            value = entry.get(key)
            if value is not None:
                target_key = key.removesuffix("_g").removesuffix("_ml")
                totals[target_key] += float(value)
    recorded_days = len({entry["date"] for entry in entries})
    divisor = max(recorded_days, 1)
    averages = {key: round(value / divisor, 1) for key, value in sorted(totals.items())}
    weekly = {key: round(value, 1) for key, value in sorted(totals.items())}
    weekly_food_variety = len({food for foods in daily_foods.values() for food in foods if food})
    daily_variety = {day: len(foods) for day, foods in sorted(daily_foods.items())}
    rule_key, rule = select_rule(profile)
    gaps = compare_against_rule(averages, weekly, weekly_food_variety, profile, rule)
    return {
        "profile_rule": rule_key,
        "profile_label": rule["label"],
        "sources": rule["sources"],
        "period": {"start": start.isoformat(), "end": until.isoformat(), "requested_days": days, "recorded_days": recorded_days},
        "entries": len(entries),
        "daily_averages": averages,
        "period_totals": weekly,
        "daily_food_variety": daily_variety,
        "weekly_food_variety": weekly_food_variety,
        "confidence_counts": dict(confidence),
        "gaps": gaps,
        "notes": rule.get("notes", []),
    }


def compare_against_rule(
    averages: dict[str, float],
    weekly: dict[str, float],
    weekly_food_variety: int,
    profile: dict[str, Any],
    rule: dict[str, Any],
) -> list[dict[str, Any]]:
    gaps = []
    for key, bounds in rule["targets"].items():
        lower, upper = bounds
        value = averages.get(key, 0.0)
        if lower is not None and value < lower:
            gaps.append({"item": key, "status": "low", "actual": value, "target": format_bounds(lower, upper)})
        check_upper = upper is not None and key not in NO_HIGH_GROUPS and not (lower is not None and lower == upper)
        if check_upper and value > upper:
            gaps.append({"item": key, "status": "high", "actual": value, "target": format_bounds(lower, upper)})
    water_target = water_minimum(profile, rule)
    water_value = averages.get("water", 0.0)
    if water_target and water_value and water_value < water_target:
        gaps.append({"item": "water", "status": "low", "actual": water_value, "target": f">={water_target} ml/day"})
    for key, bounds in rule.get("weekly", {}).items():
        lower, upper = bounds
        value = weekly_food_variety if key == "food_variety" else weekly.get(key, 0.0)
        if lower is not None and value < lower:
            unit = "types/week" if key == "food_variety" else "g/week"
            gaps.append({"item": key, "status": "low", "actual": value, "target": f">={lower} {unit}"})
        if upper is not None and value > upper:
            gaps.append({"item": key, "status": "high", "actual": value, "target": f"<={upper} g/week"})
    return gaps


def water_minimum(profile: dict[str, Any], rule: dict[str, Any]) -> int | None:
    water = rule.get("water", {})
    sex = profile.get("sex")
    return water.get(sex) or water.get("default")


def format_bounds(lower: float | None, upper: float | None) -> str:
    if lower is None:
        return f"<={upper} g/day"
    if upper is None:
        return f">={lower} g/day"
    if lower == upper:
        return f"{lower} g/day"
    return f"{lower}-{upper} g/day"


SUGGESTIONS = {
    "grains": "安排足量谷类，优先把部分精米面替换为全谷物。",
    "whole_grains_legumes": "增加燕麦、糙米、全麦、玉米或杂豆。",
    "tubers": "每周安排红薯、土豆、山药等薯类。",
    "vegetables": "每餐加入蔬菜，深色蔬菜尽量占一半。",
    "dark_vegetables": "增加深绿色、红黄色蔬菜。",
    "fruits": "每天安排新鲜水果，不用果汁替代。",
    "dairy": "每天安排牛奶、酸奶或等量奶制品。",
    "animal_foods": "适量安排鱼、禽、蛋、瘦肉，避免深加工肉。",
    "meat_fish_poultry": "安排适量鱼禽畜肉，优先鱼和禽。",
    "fish": "未来 7 天安排 2 次鱼虾类，总量向 300-500 g 靠近。",
    "meat": "畜禽肉选择瘦肉，避免过量。",
    "eggs": "一般可每天 1 个鸡蛋，不弃蛋黄；儿童和老年规则按对应目标。",
    "soy_nuts": "增加豆腐、豆浆、大豆、坚果等。",
    "soy": "增加大豆及其制品。",
    "fermented_soy": "全素者安排腐乳、豆豉、纳豆等发酵豆制品。",
    "nuts": "少量安排原味坚果。",
    "fungi_algae": "素食者安排菌菇、海带、紫菜等。",
    "oil": "控制烹调油，优先蒸煮炖，减少油炸。",
    "salt": "继续减盐，少用咸菜、酱料和加工食品。",
    "added_sugar": "减少含糖饮料、甜点和额外加糖。",
    "alcohol": "不建议饮酒；孕妇、乳母、儿童青少年应避免酒精。",
    "water": "以白水或淡茶为主，分次补足饮水。",
    "food_variety": "扩大食物种类，目标每天 12 种以上、每周 25 种以上。",
}


def render_summary_md(summary: dict[str, Any]) -> str:
    lines = [
        f"# Diet Summary ({summary['period']['start']} to {summary['period']['end']})",
        "",
        f"- Rule profile: {summary['profile_label']} ({summary['profile_rule']})",
        f"- Sources: {summary['sources']}",
        f"- Entries: {summary['entries']}",
        f"- Recorded days: {summary['period']['recorded_days']}/{summary['period']['requested_days']}",
        f"- Weekly food variety: {summary['weekly_food_variety']}",
        f"- Confidence counts: {summary['confidence_counts']}",
        "",
        "## Daily Averages",
        "",
        "| Item | Average |",
        "|---|---:|",
    ]
    for key, value in summary["daily_averages"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Gaps", ""])
    if summary["gaps"]:
        lines.append("| Item | Status | Actual | Target |")
        lines.append("|---|---|---:|---|")
        for gap in summary["gaps"]:
            lines.append(f"| {gap['item']} | {gap['status']} | {gap['actual']} | {gap['target']} |")
    else:
        lines.append("No major food-group gap detected from recorded data.")
    if summary["notes"]:
        lines.extend(["", "## Rule Notes", ""])
        lines.extend(f"- {note}" for note in summary["notes"])
    return "\n".join(lines) + "\n"


def render_recommendation(summary: dict[str, Any], profile: dict[str, Any], days: int) -> str:
    gaps = summary["gaps"]
    avoid_foods = set(profile.get("avoid_foods", [])) | set(profile.get("allergies", []))
    lines = [
        f"# {days}-Day Guideline-Based Diet Recommendation",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- Based on: {summary['profile_label']} ({summary['profile_rule']})",
        f"- Guideline sources: {summary['sources']}",
        f"- Recent records: {summary['entries']} entries across {summary['period']['recorded_days']}/{summary['period']['requested_days']} requested days",
        "",
    ]
    if summary["period"]["recorded_days"] < min(days, 7):
        lines.append("> Records are sparse; treat this as a low-confidence adjustment plan until more meals are logged.")
        lines.append("")
    if profile.get("chronic_condition_notes"):
        lines.append("> Medical note present: use this only as guideline-level support and review condition-specific needs with a clinician or registered dietitian.")
        lines.append("")
    if avoid_foods:
        lines.append(f"> Avoid/allergy foods recorded: {', '.join(sorted(avoid_foods))}. Exclude these from examples and substitute within the same food group.")
        lines.append("")

    lines.extend(["## Priority Adjustments", ""])
    if gaps:
        for gap in gaps:
            suggestion = SUGGESTIONS.get(gap["item"], "按对应食物组目标调整。")
            direction = "补足" if gap["status"] == "low" else "减少"
            lines.append(f"- {direction} `{gap['item']}`：最近约 {gap['actual']}，目标 {gap['target']}。{suggestion}")
    else:
        lines.append("- 维持当前记录中的主要食物组结构，继续提高食物多样性并稳定记录。")

    lines.extend(["", "## 7-Day Meal Direction", ""])
    lines.extend(
        [
            "- 每天：三餐规律；每餐包含谷薯类、蔬菜和优质蛋白来源；饮水分次完成。",
            "- 蔬果：餐餐有蔬菜，天天有水果；深色蔬菜优先。",
            "- 主食：至少一餐使用全谷物、杂豆或薯类替代部分精米面。",
            "- 蛋白：鱼禽蛋瘦肉或豆制品轮换；素食者用大豆、发酵豆制品、坚果、菌藻类补足。",
            "- 奶豆坚果：每天安排奶类或对应替代；每天少量大豆/坚果。",
            "- 控制项：盐、油、添加糖和酒精按规则上限管理，不把饮酒作为推荐内容。",
        ]
    )
    lines.extend(["", "## Shopping Focus", ""])
    shopping = shopping_focus({gap["item"] for gap in gaps}, summary["profile_rule"])
    lines.extend(f"- {item}" for item in shopping)
    lines.extend(["", "## Safety Boundaries", ""])
    lines.extend(
        [
            "- This is dietary-guideline support, not diagnosis or medical nutrition therapy.",
            "- Do not use this to treat disease, pregnancy complications, child growth concerns, frailty, dysphagia, or eating disorders without clinician review.",
            "- If grams were missing or estimated, improve future logs with weighed portions or package labels.",
        ]
    )
    return "\n".join(lines) + "\n"


def shopping_focus(gap_items: set[str], rule_key: str) -> list[str]:
    items = []
    if not gap_items:
        items.append("按现有结构补充多样食材：蔬菜、水果、奶类、全谷物、豆制品、鱼禽蛋瘦肉。")
    if gap_items & {"vegetables", "dark_vegetables"}:
        items.append("深色叶菜、胡萝卜/南瓜、西兰花、番茄等蔬菜。")
    if "fruits" in gap_items:
        items.append("苹果、橙、香蕉、浆果等新鲜水果。")
    if gap_items & {"dairy"}:
        items.append("牛奶、无糖酸奶或等量奶制品。")
    if gap_items & {"whole_grains_legumes", "grains", "tubers"}:
        items.append("燕麦、糙米、全麦、玉米、红薯、土豆、杂豆。")
    if gap_items & {"fish", "animal_foods", "meat_fish_poultry"}:
        items.append("鱼虾、禽肉、鸡蛋和瘦肉。")
    if gap_items & {"soy", "soy_nuts", "fermented_soy", "nuts"} or "vegetarian" in rule_key or rule_key == "vegan":
        items.append("豆腐、豆浆、大豆、腐乳/豆豉、原味坚果。")
    if gap_items & {"fungi_algae"}:
        items.append("香菇、木耳、海带、紫菜。")
    return items


def cmd_summary(args: argparse.Namespace) -> None:
    summary = summarize(args.data_dir, args.days, args.until)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(render_summary_md(summary))


def cmd_recommend(args: argparse.Namespace) -> None:
    ensure_dirs(args.data_dir)
    profile = load_profile(args.data_dir, required=True)
    summary = summarize(args.data_dir, args.lookback_days, args.until)
    content = render_recommendation(summary, profile, args.days)
    out_dir = data_paths(args.data_dir)["recommendations"]
    out_path = out_dir / f"{date.today().isoformat()}_{args.days}day.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"Wrote recommendation: {out_path}")
    if args.print:
        print()
        print(content)


def cmd_validate(args: argparse.Namespace) -> None:
    errors = []
    profile = load_profile(args.data_dir, required=False)
    if not profile:
        errors.append("profile.json missing")
    elif (profile.get("life_stage") or "adult") not in RULES and profile.get("life_stage") != "adult":
        errors.append(f"unknown life_stage: {profile.get('life_stage')}")
    log_path = data_paths(args.data_dir)["log"]
    entries = load_entries(args.data_dir)
    for index, entry in enumerate(entries, 1):
        for error in validate_entry(entry):
            errors.append(f"{log_path}:{index}: {error}")
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"OK: profile={bool(profile)} entries={len(entries)}")


def cmd_export_md(args: argparse.Namespace) -> None:
    until = args.until or date.today()
    start = until - timedelta(days=args.days - 1)
    entries = [entry for entry in load_entries(args.data_dir) if in_period(entry, start, until)]
    lines = [f"# Diet Log Export ({start} to {until})", ""]
    for entry in entries:
        lines.append(f"## {entry['date']} {entry['meal_type']}")
        if entry.get("foods"):
            lines.append("")
            lines.append("| Food | Group | Grams | Confidence |")
            lines.append("|---|---|---:|---|")
            for food in entry["foods"]:
                lines.append(
                    f"| {food['name']} | {food['group']} | {food.get('estimated_grams', '')} | {food.get('confidence', '')} |"
                )
        metrics = [
            f"{key}={entry[key]}"
            for key in ["water_ml", "alcohol_g", "oil_g", "salt_g", "added_sugar_g", "activity_steps"]
            if entry.get(key) is not None
        ]
        if metrics:
            lines.append("")
            lines.append("- " + "; ".join(metrics))
        if entry.get("notes"):
            lines.append(f"- notes: {entry['notes']}")
        lines.append("")
    output = "\n".join(lines).rstrip() + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote export: {args.output}")
    else:
        print(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("CDG_DATA_DIR", DEFAULT_DATA_DIR)))
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-profile", help="create or update profile.json")
    init.add_argument("--sex", choices=["male", "female", "other"])
    init.add_argument("--age", type=int)
    init.add_argument("--height-cm", type=float)
    init.add_argument("--weight-kg", type=float)
    init.add_argument("--activity-level", choices=["low", "medium", "high"], default=None)
    init.add_argument("--life-stage", choices=sorted(RULES), default=None)
    init.add_argument("--vegetarian-type", choices=["none", "vegan", "lacto_ovo"], default=None)
    init.add_argument("--allergy", action="append")
    init.add_argument("--avoid-food", action="append")
    init.add_argument("--chronic-condition-note")
    init.set_defaults(func=write_profile)

    add = sub.add_parser("add", help="append a meal/day record")
    add.add_argument("--date", type=parse_date, default=date.today())
    add.add_argument("--meal-type", choices=sorted(MEAL_TYPES), required=True)
    add.add_argument("--food", action="append", help="'name|amount|unit|group' or just 'name'")
    add.add_argument("--food-json", action="append", help="JSON object or @file")
    add.add_argument("--foods-json", help="JSON array or @file")
    add.add_argument("--water-ml", type=float)
    add.add_argument("--alcohol-g", type=float)
    add.add_argument("--oil-g", type=float)
    add.add_argument("--salt-g", type=float)
    add.add_argument("--added-sugar-g", type=float)
    add.add_argument("--activity-steps", type=float)
    add.add_argument("--notes")
    add.set_defaults(func=add_entry)

    summary = sub.add_parser("summary", help="summarize recent records")
    summary.add_argument("--days", type=int, default=7)
    summary.add_argument("--until", type=parse_date)
    summary.add_argument("--json", action="store_true")
    summary.set_defaults(func=cmd_summary)

    recommend = sub.add_parser("recommend", help="write a guideline-based recommendation")
    recommend.add_argument("--days", type=int, default=7)
    recommend.add_argument("--lookback-days", type=int, default=7)
    recommend.add_argument("--until", type=parse_date)
    recommend.add_argument("--print", action="store_true")
    recommend.set_defaults(func=cmd_recommend)

    validate = sub.add_parser("validate", help="validate profile and JSONL records")
    validate.set_defaults(func=cmd_validate)

    export = sub.add_parser("export-md", help="export records to Markdown")
    export.add_argument("--days", type=int, default=7)
    export.add_argument("--until", type=parse_date)
    export.add_argument("--output", type=Path)
    export.set_defaults(func=cmd_export_md)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.data_dir = args.data_dir.expanduser()
    try:
        args.func(args)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
