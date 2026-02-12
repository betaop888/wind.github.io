#!/usr/bin/env python3
"""Generate survival item price list for Wind Prices site."""

from __future__ import annotations

import json
import math
import urllib.request
from dataclasses import dataclass
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
        "iron",
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
        "wind_charge",
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


@dataclass(frozen=True)
class MaterialPrice:
    token: str
    multiplier: float


MATERIAL_MULTIPLIERS = (
    MaterialPrice("wooden_", 0.55),
    MaterialPrice("stone_", 0.7),
    MaterialPrice("iron_", 1.9),
    MaterialPrice("golden_", 1.7),
    MaterialPrice("diamond_", 4.3),
    MaterialPrice("netherite_", 14.0),
    MaterialPrice("chainmail_", 2.6),
)


OVERRIDES = {
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
    "diamond": 0.9,
    "diamond_block": 8.1,
    "raw_iron": 0.18,
    "iron_ingot": 0.22,
    "iron_block": 1.95,
    "raw_copper": 0.1,
    "copper_ingot": 0.14,
    "copper_block": 1.2,
    "raw_gold": 0.22,
    "gold_ingot": 0.28,
    "gold_block": 2.45,
    "emerald": 0.52,
    "emerald_block": 4.6,
    "coal": 0.05,
    "charcoal": 0.05,
    "lapis_lazuli": 0.14,
    "redstone": 0.08,
    "quartz": 0.16,
    "ancient_debris": 12.0,
    "netherite_scrap": 22.0,
    "netherite_ingot": 90.0,
    "netherite_block": 810.0,
    "totem_of_undying": 8.0,
    "elytra": 220.0,
    "shulker_shell": 15.0,
    "nether_star": 85.0,
    "beacon": 220.0,
    "enchanted_golden_apple": 260.0,
    "trident": 48.0,
    "dragon_egg": 640.0,
    "dragon_head": 120.0,
    "heart_of_the_sea": 40.0,
    "nautilus_shell": 3.0,
    "echo_shard": 9.0,
    "disc_fragment_5": 5.0,
    "recovery_compass": 36.0,
    "bottle_o_enchanting": 2.0,
    "enchanted_book": 6.0,
    "wind_charge": 2.5,
    "ominous_trial_key": 14.0,
    "wither_skeleton_skull": 7.5,
    "ghast_tear": 2.0,
    "blaze_rod": 0.45,
    "ender_pearl": 0.55,
    "gunpowder": 0.18,
    "slime_ball": 0.35,
    "golden_apple": 4.2,
    "golden_carrot": 0.9,
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
    if contains_token(name, KEYWORD_SETS["combat"]) or contains_token(
        name, KEYWORD_SETS["tool"]
    ):
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


def normalize(price: float) -> float:
    if price < 1:
        return round(price, 4)
    if price < 10:
        return round(price, 3)
    if price < 100:
        return round(price, 2)
    return round(price, 1)


def fallback_display_name(item_name: str) -> str:
    return item_name.replace("_", " ").title()


def pick_ru_name(item_name: str, en_display_name: str, ru_lang: dict[str, str]) -> str:
    keys = (f"item.minecraft.{item_name}", f"block.minecraft.{item_name}")
    for key in keys:
        if key in ru_lang:
            return str(ru_lang[key])
    return en_display_name if en_display_name else fallback_display_name(item_name)


def infer_price(item: dict[str, object]) -> float:
    name = str(item["name"])
    stack_size = int(item.get("stackSize", 64))

    if name in OVERRIDES:
        return OVERRIDES[name]

    if stack_size >= 64:
        price = 0.02
    elif stack_size == 16:
        price = 0.08
    else:
        price = 1.2

    if contains_token(name, KEYWORD_SETS["farmable"]):
        price *= 0.72
    if contains_token(name, KEYWORD_SETS["redstone"]):
        price *= 1.35
    if contains_token(name, KEYWORD_SETS["food"]):
        price *= 0.92
    if contains_token(name, KEYWORD_SETS["rare"]):
        price *= 6.0

    if "ore" in name:
        price *= 2.1
    if "deepslate_" in name:
        price *= 1.12
    if "waxed_" in name or "oxidized_" in name:
        price *= 1.2
    if any(x in name for x in ("stairs", "fence", "trapdoor")):
        price *= 1.2
    if "slab" in name:
        price *= 0.9
    if "wall" in name:
        price *= 1.1
    if "concrete_powder" in name:
        price *= 0.95
    if "smithing_template" in name:
        price *= 8.0
    if any(x in name for x in ("banner_pattern", "pottery_sherd", "music_disc")):
        price *= 4.2
    if any(x in name for x in ("potion", "lingering_potion", "splash_potion")):
        price *= 2.4

    for entry in MATERIAL_MULTIPLIERS:
        if entry.token in name:
            price *= entry.multiplier
            break

    if name in LIMITED_ITEMS:
        price *= 1.9

    min_price = 0.003 if stack_size >= 64 else 0.012 if stack_size == 16 else 0.35
    max_price = 1200.0
    return min(max(price, min_price), max_price)


def main() -> None:
    items = fetch_json(ITEMS_URL)
    ru_lang = load_ru_lang(VERSION)

    out_items: list[dict[str, object]] = []
    for item in items:  # type: ignore[assignment]
        item_name = str(item["name"])
        if not is_survival_obtainable(item_name):
            continue

        stack_size = int(item.get("stackSize", 64))
        raw_price_item = infer_price(item)
        price_item = normalize(raw_price_item)
        stack_price = normalize(raw_price_item * stack_size) if stack_size > 1 else None
        out_items.append(
            {
                "id": int(item["id"]),
                "key": item_name,
                "name_ru": pick_ru_name(item_name, str(item.get("displayName", "")), ru_lang),
                "name_en": str(item.get("displayName", "")) or fallback_display_name(item_name),
                "stack_size": stack_size,
                "category": classify(item_name),
                "obtainability": obtainability(item_name),
                "price_item": price_item,
                "price_stack": stack_price,
            }
        )

    out_items.sort(key=lambda row: (row["category"], row["name_ru"]))
    payload = {
        "title": "Винд цены",
        "mc_version": VERSION,
        "currency": "ар",
        "currency_note": "1 ар = 1 алмазная руда",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items_count": len(out_items),
        "items": out_items,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(
        f"Generated {len(out_items)} survival items for {VERSION} -> {OUTPUT_PATH}",
    )


if __name__ == "__main__":
    main()
