#!/usr/bin/env python3
"""Generate balanced integer prices in ars for Wind prices site."""

from __future__ import annotations

import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

VERSION = "1.21.11"
ITEMS_URL = (
    "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/"
    f"data/pc/{VERSION}/items.json"
)
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "items.json"

EXCLUDE_EXACT = {
    "air",
    "barrier",
    "bedrock",
    "chain_command_block",
    "command_block",
    "command_block_minecart",
    "debug_stick",
    "dirt_path",
    "end_portal_frame",
    "farmland",
    "frogspawn",
    "jigsaw",
    "knowledge_book",
    "light",
    "petrified_oak_slab",
    "reinforced_deepslate",
    "repeating_command_block",
    "spawner",
    "structure_block",
    "structure_void",
    "suspicious_gravel",
    "suspicious_sand",
    "trial_spawner",
}

EXCLUDE_PREFIX = ("infested_",)
EXCLUDE_SUFFIX = ("_spawn_egg",)

KEYWORD_SETS = {
    "farmable": {
        "bamboo",
        "beetroot",
        "bone",
        "cactus",
        "carrot",
        "chicken",
        "clay",
        "cobblestone",
        "cod",
        "dried_kelp",
        "egg",
        "feather",
        "gunpowder",
        "honey",
        "kelp",
        "leather",
        "melon",
        "mutton",
        "nether_wart",
        "oak",
        "potato",
        "pumpkin",
        "porkchop",
        "rabbit_hide",
        "red_mushroom",
        "rotten_flesh",
        "salmon",
        "scute",
        "seeds",
        "slime",
        "snowball",
        "spider_eye",
        "spruce",
        "string",
        "sugar_cane",
        "totem",
        "wheat",
        "wool",
    },
    "rare": {
        "ancient_debris",
        "beacon",
        "dragon_egg",
        "echo_shard",
        "elytra",
        "enchanted_golden_apple",
        "heart_of_the_sea",
        "mace",
        "music_disc",
        "nether_star",
        "netherite",
        "ominous_trial_key",
        "recovery_compass",
        "sniffer_egg",
        "smithing_template",
        "trident",
        "wither_skeleton_skull",
    },
    "redstone": {
        "comparator",
        "dispenser",
        "dropper",
        "observer",
        "piston",
        "redstone",
        "repeater",
        "sculk_sensor",
        "target",
        "tripwire_hook",
    },
    "food": {
        "apple",
        "beef",
        "beetroot",
        "bread",
        "cake",
        "carrot",
        "chicken",
        "cod",
        "cookie",
        "golden_apple",
        "golden_carrot",
        "mushroom_stew",
        "mutton",
        "porkchop",
        "potato",
        "pumpkin_pie",
        "rabbit_stew",
        "salmon",
        "suspicious_stew",
    },
    "combat": {
        "arrow",
        "axe",
        "bow",
        "crossbow",
        "helmet",
        "chestplate",
        "leggings",
        "boots",
        "shield",
        "sword",
        "trident",
        "mace",
        "tipped_arrow",
        "spectral_arrow",
    },
    "tool": {
        "axe",
        "hoe",
        "pickaxe",
        "shears",
        "shovel",
        "fishing_rod",
        "flint_and_steel",
    },
}

# Float anchors preserve previous relative balance, then rounded to integer ars.
FLOAT_OVERRIDES = {
    "oak_log": 1 / 64,
    "spruce_log": 1 / 64,
    "birch_log": 1 / 64,
    "jungle_log": 1 / 64,
    "acacia_log": 1 / 64,
    "dark_oak_log": 1 / 64,
    "mangrove_log": 1 / 64,
    "cherry_log": 1 / 64,
    "pale_oak_log": 1 / 64,
    "crimson_stem": 1 / 64,
    "warped_stem": 1 / 64,
    "stripped_oak_log": 1 / 64,
    "stripped_spruce_log": 1 / 64,
    "stripped_birch_log": 1 / 64,
    "stripped_jungle_log": 1 / 64,
    "stripped_acacia_log": 1 / 64,
    "stripped_dark_oak_log": 1 / 64,
    "stripped_mangrove_log": 1 / 64,
    "stripped_cherry_log": 1 / 64,
    "stripped_pale_oak_log": 1 / 64,
    "stripped_crimson_stem": 1 / 64,
    "stripped_warped_stem": 1 / 64,
    "bamboo_block": 1 / 64,
    "diamond_ore": 1.0,
    "deepslate_diamond_ore": 1.0,
    "diamond": 1.0,
    "diamond_block": 9.0,
    "raw_iron": 1 / 64,
    "iron_ingot": 1 / 64,
    "iron_block": 9 / 64,
    "raw_copper": 1 / 64,
    "copper_ingot": 1 / 64,
    "copper_block": 9 / 64,
    "raw_gold": 2 / 64,
    "gold_ingot": 2 / 64,
    "gold_block": 18 / 64,
    "emerald": 0.55,
    "emerald_block": 4.9,
    "coal": 1 / 64,
    "charcoal": 1 / 64,
    "lapis_lazuli": 4 / 64,
    "redstone": 2 / 64,
    "quartz": 2 / 64,
    "ancient_debris": 8.0,
    "netherite_scrap": 5.0,
    "netherite_ingot": 20.0,
    "netherite_block": 180.0,
    "totem_of_undying": 8.0,
    "elytra": 180.0,
    "shulker_shell": 12.0,
    "nether_star": 70.0,
    "beacon": 56.0,
    "enchanted_golden_apple": 220.0,
    "trident": 35.0,
    "dragon_egg": 500.0,
    "dragon_head": 110.0,
    "heart_of_the_sea": 30.0,
    "nautilus_shell": 3.0,
    "echo_shard": 8.0,
    "disc_fragment_5": 4.0,
    "recovery_compass": 30.0,
    "bottle_o_enchanting": 2.0,
    "enchanted_book": 6.0,
    "ominous_trial_key": 14.0,
    "wither_skeleton_skull": 7.0,
    "ghast_tear": 2.0,
    "blaze_rod": 0.5,
    "ender_pearl": 0.6,
    "gunpowder": 0.2,
    "slime_ball": 0.35,
    "golden_apple": 4.0,
    "golden_carrot": 1.0,
}

LIMITED_ITEMS = {
    "dragon_egg",
    "elytra",
    "enchanted_golden_apple",
    "heart_of_the_sea",
    "nether_star",
    "ominous_trial_key",
    "sniffer_egg",
}

# Hard integer rules (trade_count, price_ars)
INTEGER_OVERRIDES = {
    "oak_log": (64, 1),
    "spruce_log": (64, 1),
    "birch_log": (64, 1),
    "jungle_log": (64, 1),
    "acacia_log": (64, 1),
    "dark_oak_log": (64, 1),
    "mangrove_log": (64, 1),
    "cherry_log": (64, 1),
    "pale_oak_log": (64, 1),
    "crimson_stem": (64, 1),
    "warped_stem": (64, 1),
    "diamond_ore": (1, 1),
    "deepslate_diamond_ore": (1, 1),
    "diamond": (1, 1),
    "totem_of_undying": (1, 8),
    "golden_apple": (1, 4),
    "ghast_tear": (1, 2),
    "disc_fragment_5": (1, 4),
    "ominous_trial_key": (1, 14),
    "netherite_ingot": (1, 20),
    "beacon": (1, 56),
    "iron_ingot": (64, 1),
    "bread": (64, 1),
}

PER_ITEM_TOKENS = {
    "diamond",
    "netherite",
    "ancient_debris",
    "totem",
    "elytra",
    "trident",
    "shulker_shell",
    "nether_star",
    "beacon",
    "enchanted_golden_apple",
    "heart_of_the_sea",
    "nautilus_shell",
    "echo_shard",
    "recovery_compass",
    "dragon_egg",
    "dragon_head",
    "wither_skeleton_skull",
    "music_disc",
    "disc_fragment",
    "smithing_template",
    "mace",
    "ominous_trial_key",
    "ghast_tear",
    "golden_apple",
}

COMPRESSION_RELATIONS = (
    ("coal", "coal_block", 9.0),
    ("diamond", "diamond_block", 9.0),
    ("emerald", "emerald_block", 9.0),
    ("redstone", "redstone_block", 9.0),
    ("lapis_lazuli", "lapis_block", 9.0),
    ("quartz", "quartz_block", 9.0),
    ("iron_ingot", "iron_block", 9.0),
    ("gold_ingot", "gold_block", 9.0),
    ("copper_ingot", "copper_block", 9.0),
    ("raw_iron", "raw_iron_block", 9.0),
    ("raw_gold", "raw_gold_block", 9.0),
    ("raw_copper", "raw_copper_block", 9.0),
    ("netherite_ingot", "netherite_block", 9.0),
)

# Fortune III expected drop multipliers:
# - single-drop ores ~= 2.2x
# - redstone ~= 9.9x, lapis ~= 14.3x
ORE_FORTUNE_RELATIONS = {
    "coal_ore": ("coal", 2.2),
    "deepslate_coal_ore": ("coal", 2.2),
    "emerald_ore": ("emerald", 2.2),
    "deepslate_emerald_ore": ("emerald", 2.2),
    "iron_ore": ("raw_iron", 2.2),
    "deepslate_iron_ore": ("raw_iron", 2.2),
    "gold_ore": ("raw_gold", 2.2),
    "deepslate_gold_ore": ("raw_gold", 2.2),
    "copper_ore": ("raw_copper", 2.2),
    "deepslate_copper_ore": ("raw_copper", 2.2),
    "nether_quartz_ore": ("quartz", 2.2),
    "redstone_ore": ("redstone", 9.9),
    "deepslate_redstone_ore": ("redstone", 9.9),
    "lapis_ore": ("lapis_lazuli", 14.3),
    "deepslate_lapis_ore": ("lapis_lazuli", 14.3),
    "nether_gold_ore": ("gold_nugget", 8.8),
}

DEEPSLATE_PRICE_LINKS = (
    ("coal_ore", "deepslate_coal_ore"),
    ("emerald_ore", "deepslate_emerald_ore"),
    ("iron_ore", "deepslate_iron_ore"),
    ("gold_ore", "deepslate_gold_ore"),
    ("copper_ore", "deepslate_copper_ore"),
    ("redstone_ore", "deepslate_redstone_ore"),
    ("lapis_ore", "deepslate_lapis_ore"),
)


def fetch_json(url: str) -> object:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def load_ru_lang(version: str) -> dict[str, str]:
    manifest = fetch_json(MANIFEST_URL)
    versions: Iterable[dict[str, str]] = manifest["versions"]  # type: ignore[index]
    version_entry = next(v for v in versions if v["id"] == version)
    version_meta = fetch_json(version_entry["url"])
    asset_index = fetch_json(version_meta["assetIndex"]["url"])  # type: ignore[index]
    lang_meta = asset_index["objects"]["minecraft/lang/ru_ru.json"]  # type: ignore[index]
    lang_url = (
        f"https://resources.download.minecraft.net/"
        f"{lang_meta['hash'][:2]}/{lang_meta['hash']}"
    )
    return fetch_json(lang_url)  # type: ignore[return-value]


def contains_token(name: str, tokens: set[str]) -> bool:
    return any(token in name for token in tokens)


def is_survival_obtainable(name: str) -> bool:
    if name in EXCLUDE_EXACT:
        return False
    if name.startswith(EXCLUDE_PREFIX):
        return False
    if name.endswith(EXCLUDE_SUFFIX):
        return False
    return True


def classify(name: str) -> str:
    if contains_token(name, {"ore", "ingot", "gem", "diamond", "emerald", "netherite"}):
        return "Руды и ресурсы"
    if contains_token(name, KEYWORD_SETS["redstone"]):
        return "Редстоун и механизмы"
    if contains_token(name, KEYWORD_SETS["combat"]) or contains_token(name, KEYWORD_SETS["tool"]):
        return "Инструменты и бой"
    if contains_token(name, KEYWORD_SETS["food"]):
        return "Еда и фермерство"
    if contains_token(name, {"blaze", "ghast", "ender", "chorus", "nether", "wither"}):
        return "Незер и Энд"
    if contains_token(name, {"head", "shell", "totem", "star", "elytra", "disc"}):
        return "Редкие трофеи"
    if contains_token(
        name,
        {
            "stairs",
            "slab",
            "fence",
            "wall",
            "door",
            "trapdoor",
            "planks",
            "brick",
            "glass",
            "terracotta",
            "concrete",
            "carpet",
            "banner",
        },
    ):
        return "Строительные блоки"
    return "Блоки и предметы"


def obtainability(name: str) -> str:
    if name in LIMITED_ITEMS:
        return "Ограниченный"
    if contains_token(name, KEYWORD_SETS["farmable"]):
        return "Фармится"
    return "Обычный"


def fallback_display_name(item_name: str) -> str:
    return item_name.replace("_", " ").title()


def pick_ru_name(item_name: str, en_display_name: str, ru_lang: dict[str, str]) -> str:
    keys = (f"item.minecraft.{item_name}", f"block.minecraft.{item_name}")
    for key in keys:
        if key in ru_lang:
            return str(ru_lang[key])
    return en_display_name if en_display_name else fallback_display_name(item_name)


def infer_price_float(item: dict[str, object]) -> float:
    name = str(item["name"])
    stack_size = int(item.get("stackSize", 64))

    if name in FLOAT_OVERRIDES:
        return FLOAT_OVERRIDES[name]

    if stack_size >= 64:
        price = 0.03
    elif stack_size == 16:
        price = 0.08
    else:
        price = 1.3

    if contains_token(name, KEYWORD_SETS["farmable"]):
        price *= 0.65
    if contains_token(name, KEYWORD_SETS["redstone"]):
        price *= 1.35
    if contains_token(name, KEYWORD_SETS["food"]):
        price *= 0.95
    if contains_token(name, KEYWORD_SETS["rare"]):
        price *= 3.5

    if "ore" in name:
        price *= 1.6
    if "deepslate_" in name:
        price *= 1.12
    if "waxed_" in name or "oxidized_" in name:
        price *= 1.2
    if any(x in name for x in ("stairs", "fence", "trapdoor")):
        price *= 1.15
    if "slab" in name:
        price *= 0.9
    if "wall" in name:
        price *= 1.08
    if "concrete_powder" in name:
        price *= 0.95
    if "smithing_template" in name:
        price *= 8.0
    if any(x in name for x in ("banner_pattern", "pottery_sherd", "music_disc")):
        price *= 4.2
    if any(x in name for x in ("potion", "lingering_potion", "splash_potion")):
        price *= 2.4

    if "wooden_" in name:
        price *= 0.6
    elif "stone_" in name:
        price *= 0.75
    elif "iron_" in name:
        price *= 0.8
    elif "golden_" in name:
        price *= 1.2
    elif "diamond_" in name:
        price *= 2.8
    elif "netherite_" in name:
        price *= 4.0
    elif "chainmail_" in name:
        price *= 1.8

    if name in LIMITED_ITEMS:
        price *= 1.8

    min_price = 0.005 if stack_size >= 64 else 0.02 if stack_size == 16 else 0.8
    max_price = 1200.0
    return min(max(price, min_price), max_price)


def is_wood_bulk(name: str) -> bool:
    return (
        name.endswith("_log")
        or name.endswith("_stem")
        or name.endswith("_wood")
        or name.endswith("_hyphae")
        or name.endswith("_planks")
    )


def should_sell_per_item(name: str, stack_size: int) -> bool:
    if stack_size <= 1:
        return True
    return contains_token(name, PER_ITEM_TOKENS)


def trade_count_and_label(name: str, stack_size: int) -> tuple[int, str]:
    if stack_size <= 1:
        return 1, "шт"
    if is_wood_bulk(name) or name == "bamboo_block":
        return 64, "стак"
    if should_sell_per_item(name, stack_size):
        return 1, "шт"
    if stack_size >= 64:
        return 64, "стак"
    return stack_size, f"{stack_size} шт"


def round_price(value: float) -> int:
    # Classic arithmetic rounding for positive numbers.
    return max(1, int(value + 0.5))


def ceil_price(value: float) -> int:
    return max(1, int(math.ceil(value - 1e-9)))


def infer_integer_offer(item: dict[str, object]) -> tuple[int, str, int]:
    name = str(item["name"])
    if name in INTEGER_OVERRIDES:
        trade_count, price_ars = INTEGER_OVERRIDES[name]
        label = "стак" if trade_count == 64 else "шт" if trade_count == 1 else f"{trade_count} шт"
        return trade_count, label, price_ars

    stack_size = int(item.get("stackSize", 64))
    trade_count, trade_label = trade_count_and_label(name, stack_size)
    unit_estimate = infer_price_float(item) * trade_count
    price_ars = round_price(unit_estimate)
    return trade_count, trade_label, price_ars


def stabilize_economy(rows: list[dict[str, object]]) -> None:
    by_key: dict[str, dict[str, object]] = {str(row["key"]): row for row in rows}

    def unit_price(row: dict[str, object]) -> float:
        return float(row["price_ars"]) / float(row["trade_count"])

    def ensure_total_at_least(row: dict[str, object], min_total: float) -> None:
        row["price_ars"] = max(int(row["price_ars"]), ceil_price(min_total))

    # 1) Keep 9:1 compression prices coherent to prevent craft/uncraft abuse.
    for resource_key, block_key, ratio in COMPRESSION_RELATIONS:
        resource = by_key.get(resource_key)
        block = by_key.get(block_key)
        if not resource or not block:
            continue
        target_total = unit_price(resource) * ratio * float(block["trade_count"])
        block["price_ars"] = round_price(target_total)

    # 2) Ores cannot be cheaper than expected Fortune III output value.
    for ore_key, (drop_key, multiplier) in ORE_FORTUNE_RELATIONS.items():
        ore = by_key.get(ore_key)
        drop = by_key.get(drop_key)
        if not ore or not drop:
            continue
        min_total = unit_price(drop) * multiplier * float(ore["trade_count"])
        ensure_total_at_least(ore, min_total)

    # 3) Deepslate variant should not be cheaper than normal ore.
    for normal_key, deep_key in DEEPSLATE_PRICE_LINKS:
        normal = by_key.get(normal_key)
        deep = by_key.get(deep_key)
        if not normal or not deep:
            continue
        ensure_total_at_least(deep, float(normal["price_ars"]))


def main() -> None:
    items = fetch_json(ITEMS_URL)
    ru_lang = load_ru_lang(VERSION)

    out_items: list[dict[str, object]] = []
    for item in items:  # type: ignore[assignment]
        item_name = str(item["name"])
        if not is_survival_obtainable(item_name):
            continue

        stack_size = int(item.get("stackSize", 64))
        trade_count, trade_label, price_ars = infer_integer_offer(item)

        out_items.append(
            {
                "id": int(item["id"]),
                "key": item_name,
                "name_ru": pick_ru_name(item_name, str(item.get("displayName", "")), ru_lang),
                "name_en": str(item.get("displayName", "")) or fallback_display_name(item_name),
                "stack_size": stack_size,
                "category": classify(item_name),
                "obtainability": obtainability(item_name),
                "trade_count": trade_count,
                "trade_label": trade_label,
                "price_ars": price_ars,
            }
        )

    stabilize_economy(out_items)

    out_items.sort(key=lambda row: (row["category"], row["name_ru"]))

    payload = {
        "title": "Винд цены",
        "mc_version": VERSION,
        "currency": "ар",
        "currency_note": "1 ар = 1 алмазная руда",
        "pricing_note": "Все цены целые, без дробей. Цены руд стабилизированы под Fortune III.",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items_count": len(out_items),
        "items": out_items,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(f"Generated {len(out_items)} items for {VERSION} -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
