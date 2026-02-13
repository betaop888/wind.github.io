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
    "lapis_lazuli": 1 / 64,
    "redstone": 1 / 64,
    "quartz": 2 / 64,
    "ancient_debris": 8.0,
    "netherite_scrap": 5.0,
    "netherite_ingot": 20.0,
    "netherite_block": 180.0,
    "totem_of_undying": 2.0,
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
    "totem_of_undying": (1, 2),
    "golden_apple": (1, 4),
    "ghast_tear": (1, 2),
    "disc_fragment_5": (1, 4),
    "ominous_trial_key": (1, 14),
    "netherite_ingot": (1, 20),
    "beacon": (1, 56),
    "iron_ingot": (64, 1),
    "bread": (64, 1),
    "lapis_lazuli": (64, 1),
    "redstone": (64, 1),
    "coal": (64, 1),
    "charcoal": (64, 1),
}

ANTI_DUMP_MINIMUMS = {
    # key: (trade_count, minimum price in ars)
    "netherite_ingot": (1, 20),
    "beacon": (1, 50),
    "totem_of_undying": (1, 2),
    "elytra": (1, 120),
    "dragon_head": (1, 90),
    "shulker_shell": (1, 10),
}

ECONOMY_POLICY = {
    "code_title": "Экономический кодекс сервера WIND",
    "approval": {
        "date": "2026-02-14",
        "officials": [
            {"role": "Губернатор", "name": "F0fner"},
            {"role": "Вице-Губернатор", "name": "Tw1sTix"},
            {"role": "Верховный Судья", "name": "Bluetooth"},
            {"role": "Министр Экономики", "name": "Frozzor"},
        ],
    },
    "system_type": "регулируемая рыночная экономика",
    "code_purpose": [
        "Регулирование торговых, финансовых и предпринимательских отношений.",
        "Порядок ведения бизнеса, налогообложения и лицензирования.",
        "Правила оборота валюты АР и защита рынка от злоупотреблений.",
    ],
    "system_goals": [
        "Единое и стабильное экономическое пространство.",
        "Сохранение ценности валюты АР.",
        "Защита прав предпринимателей и потребителей.",
        "Прозрачная налоговая система и добросовестная конкуренция.",
        "Предотвращение инфляции и обрушения рынка.",
        "Стимулирование малого и крупного бизнеса.",
    ],
    "principles": [
        "Свобода предпринимательства при соблюдении ЭКС.",
        "Прозрачность: регистрация, проверяемость, недопустимость сокрытия доходов.",
        "Справедливая налоговая нагрузка пропорционально обороту.",
        "Защита рынка: анти-демпинг, анти-монополизация, защита редких ресурсов.",
        "Единство экономического пространства: правила действуют на спавне, вне спавна и в аду.",
    ],
    "money_in": [
        "Госзакупки",
        "Зарплаты госработ",
        "Малый и крупный бизнес",
        "Копание аров вручную",
    ],
    "money_out": [
        "Налоги",
        "Аренда земли",
        "Лицензии",
        "Штрафы",
        "Госпошлины (на доработке)",
        "Налог при продаже бизнеса",
    ],
    "participants": [
        "Граждане сервера",
        "Зарегистрированные бизнесы",
        "Объединения (кланы, общины)",
        "Министерство экономики",
    ],
    "entrepreneur_rights": [
        "Свободный выбор направления деятельности.",
        "Установка цен при отсутствии минимального порога.",
        "Приобретение территории и регистрация бизнеса.",
        "Заключение договоров и продажа бизнеса.",
        "Обжалование решений органов экономического контроля.",
    ],
    "consumer_rights": [
        "Качественный товар и достоверная информация о нём.",
        "Соблюдение минимальных ценовых порогов.",
        "Подача жалоб и судебная защита при нарушениях.",
    ],
    "entrepreneur_duties": [
        "Регистрация бизнеса и получение лицензии.",
        "Своевременная уплата налогов и сборов.",
        "Соблюдение минимальных ценовых порогов.",
        "Предоставление достоверных данных о бизнесе.",
        "Уважение прав потребителей.",
    ],
    "consumer_duties": [
        "Соблюдать правила торговли.",
        "Оплачивать сделки в полном объёме.",
        "Не участвовать в нелегальной торговле.",
    ],
    "land_types": [
        "Государственная: спавн (оверворлд, ад), земля приобретается в собственность.",
        "Коммерческая: вне спавна, облагается налогом.",
    ],
    "spawn_rent_formula": "Стоимость = площадь участка в блоках",
    "spawn_land_price_per_block_ars": 1,
    "monthly_business_rent_ars": 32,
    "size_coefficients": [
        "до 100 блоков: без надбавки",
        "101-200 блоков: +20%",
        "200+ блоков: +35%",
    ],
    "business_types": [
        "Торговый (магазины, ТЦ)",
        "Сервисный (казино, строительные компании и т.д.)",
        "Премиальный (редкие товары: элитры, маяки и т.д.)",
    ],
    "turnover_tax": {
        "formula": "Налог = (стоимость территории / 2) + процент по типу бизнеса",
        "trading": "10%",
        "service": "15%",
        "premium": "20%",
    },
    "business_sale_tax_percent": 7,
    "business_sale_tax_note": "Налог 7% при продаже бизнеса действует на спавне/в хабе ада.",
    "mandatory_payments": [
        "Покупка территории (для бизнеса на спавне)",
        "Лицензионный сбор",
        "Налог с оборота",
        "Налог при продаже бизнеса (7%)",
    ],
    "article_summary": [
        {
            "article": "Статья 1",
            "title": "Основные положения",
            "summary": "Назначение Кодекса, цели системы и модель регулируемой рыночной экономики.",
        },
        {
            "article": "Статья 2",
            "title": "Принципы деятельности",
            "summary": "Свобода предпринимательства, прозрачность, справедливая налоговая нагрузка, защита рынка.",
        },
        {
            "article": "Статья 3",
            "title": "Валюта и оборот",
            "summary": "Официальная валюта АР, источники ввода и механизмы вывода средств.",
        },
        {
            "article": "Статья 4",
            "title": "Участники экономики",
            "summary": "Права и обязанности предпринимателей и потребителей, роль министерства.",
        },
        {
            "article": "Статья 5-6",
            "title": "Территории и типы бизнеса",
            "summary": "Спавн/вне спавна, торговый/сервисный/премиальный типы бизнеса.",
        },
        {
            "article": "Статья 7-9",
            "title": "Анти-демпинг и контроль",
            "summary": "Минимальные цены на отдельные товары и государственный контроль устойчивости рынка.",
        },
        {
            "article": "Статья 10-16",
            "title": "Финансовые нормативы",
            "summary": "Стоимость территории, налоги, лицензии, обязательные платежи и порядок применения.",
        },
    ],
    "sanctions": [
        {
            "code": "ЭКС 2.1",
            "violation": "Ведение бизнеса без регистрации",
            "first": "50 АР",
            "repeat": "100 АР",
            "systematic": "Временная остановка бизнеса до 14 дней",
        },
        {
            "code": "ЭКС 2.2",
            "violation": "Ведение бизнеса без действующей лицензии",
            "first": "50 АР",
            "repeat": "100 АР + приостановка деятельности",
            "systematic": "До получения лицензии",
        },
        {
            "code": "ЭКС 2.3",
            "violation": "Деятельность вне заявленного типа",
            "first": "75 АР",
            "repeat": "Аннулирование лицензии",
            "systematic": "Аннулирование лицензии",
        },
        {
            "code": "ЭКС 3.1",
            "violation": "Уклонение от 7% налога при продаже бизнеса",
            "first": "100 АР + обязательная уплата 7%",
            "repeat": "Усиление санкции решением суда/министерства",
            "systematic": "Усиленный контроль",
        },
        {
            "code": "ЭКС 3.2",
            "violation": "Несвоевременная уплата налога",
            "first": "10% от суммы задолженности",
            "repeat": "Повышенный штраф",
            "systematic": "Ограничение экономической деятельности",
        },
        {
            "code": "ЭКС 4.1",
            "violation": "Демпинг (ниже минимальной цены)",
            "first": "50 АР",
            "repeat": "100 АР",
            "systematic": "Временное закрытие бизнеса до 14 дней",
        },
        {
            "code": "ЭКС 4.2",
            "violation": "Скрытый демпинг через личные сделки",
            "first": "100 АР",
            "repeat": "Аннулирование лицензии",
            "systematic": "Аннулирование лицензии",
        },
        {
            "code": "ЭКС 5.1",
            "violation": "Продажа запрещённых товаров",
            "first": "100 АР + изъятие товара",
            "repeat": "Аннулирование лицензии",
            "systematic": "Аннулирование лицензии",
        },
        {
            "code": "ЭКС 6.1",
            "violation": "Самовольная коммерческая застройка на спавне",
            "first": "100 АР + демонтаж",
            "repeat": "Усиленные санкции",
            "systematic": "Ограничение деятельности",
        },
        {
            "code": "ЭКС 6.2",
            "violation": "Использование участка не по назначению",
            "first": "50 АР",
            "repeat": "Временное ограничение деятельности",
            "systematic": "Усиленное ограничение",
        },
        {
            "code": "ЭКС 7.1",
            "violation": "Экономическое мошенничество",
            "first": "От 150 АР",
            "repeat": "Аннулирование лицензии",
            "systematic": "Запрет предпринимательства до 30 дней",
        },
        {
            "code": "ЭКС 7.2",
            "violation": "Монополизация рынка через демпинг",
            "first": "150 АР",
            "repeat": "Временное ограничение деятельности",
            "systematic": "Ограничение деятельности",
        },
    ],
    "anti_dumping": {
        "rule": "Цена ниже минимума — штраф или временное закрытие бизнеса.",
        "minimum_prices": [
            {"key": key, "trade_count": offer[0], "min_price_ars": offer[1]}
            for key, offer in ANTI_DUMP_MINIMUMS.items()
        ],
    },
    "licenses_spawn": {
        "period": "1 месяц",
        "trading_ars": 32,
        "service_ars": 48,
        "premium_ars": 64,
    },
    "licenses_outside_spawn_2weeks": {
        "period": "2 недели",
        "trading_ars": 64,
        "service_ars": 72,
        "premium_ars": 96,
    },
}

CUSTOM_ITEMS = [
    {
        "id": 200001,
        "key": "alcoholic_drinks",
        "name_ru": "Алкогольные напитки",
        "name_en": "Alcoholic Drinks",
        "stack_size": 1,
        "category": "Кастомные предметы",
        "obtainability": "Ограниченный",
        "trade_count": 1,
        "trade_label": "шт",
        "price_ars": None,
        "price_note": "неопределенно",
    },
    {
        "id": 200002,
        "key": "cigarettes",
        "name_ru": "Сигареты",
        "name_en": "Cigarettes",
        "stack_size": 1,
        "category": "Кастомные предметы",
        "obtainability": "Ограниченный",
        "trade_count": 1,
        "trade_label": "шт",
        "price_ars": None,
        "price_note": "неопределенно",
    },
    {
        "id": 200003,
        "key": "crab_claw",
        "name_ru": "Клешня краба",
        "name_en": "Crab Claw",
        "stack_size": 1,
        "category": "Кастомные предметы",
        "obtainability": "Ограниченный",
        "trade_count": 1,
        "trade_label": "шт",
        "price_ars": None,
        "price_note": "неопределенно",
    },
]

ROMAN_LEVELS = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
}

ENCHANTED_BOOK_VARIANTS = [
    # Armor
    {"key": "protection", "name_ru": "Защита", "name_en": "Protection", "max_level": 4, "tier": 2},
    {
        "key": "fire_protection",
        "name_ru": "Огнеупорность",
        "name_en": "Fire Protection",
        "max_level": 4,
        "tier": 2,
    },
    {
        "key": "blast_protection",
        "name_ru": "Взрывоустойчивость",
        "name_en": "Blast Protection",
        "max_level": 4,
        "tier": 2,
    },
    {
        "key": "projectile_protection",
        "name_ru": "Защита от снарядов",
        "name_en": "Projectile Protection",
        "max_level": 4,
        "tier": 2,
    },
    {
        "key": "feather_falling",
        "name_ru": "Невесомость",
        "name_en": "Feather Falling",
        "max_level": 4,
        "tier": 2,
    },
    {"key": "thorns", "name_ru": "Шипы", "name_en": "Thorns", "max_level": 3, "tier": 3},
    {"key": "respiration", "name_ru": "Подводник", "name_en": "Respiration", "max_level": 3, "tier": 2},
    {"key": "aqua_affinity", "name_ru": "Подводная спешка", "name_en": "Aqua Affinity", "max_level": 1, "tier": 2},
    {
        "key": "depth_strider",
        "name_ru": "Подводная ходьба",
        "name_en": "Depth Strider",
        "max_level": 3,
        "tier": 2,
    },
    {
        "key": "frost_walker",
        "name_ru": "Ледоход",
        "name_en": "Frost Walker",
        "max_level": 2,
        "tier": 3,
        "treasure": True,
    },
    {
        "key": "binding_curse",
        "name_ru": "Проклятие несъёмности",
        "name_en": "Curse of Binding",
        "max_level": 1,
        "tier": 2,
        "treasure": True,
    },
    {
        "key": "soul_speed",
        "name_ru": "Скорость души",
        "name_en": "Soul Speed",
        "max_level": 3,
        "tier": 3,
        "treasure": True,
    },
    {
        "key": "swift_sneak",
        "name_ru": "Проворство",
        "name_en": "Swift Sneak",
        "max_level": 3,
        "tier": 4,
        "treasure": True,
    },
    # Weapons
    {"key": "sharpness", "name_ru": "Острота", "name_en": "Sharpness", "max_level": 5, "tier": 3},
    {"key": "smite", "name_ru": "Небесная кара", "name_en": "Smite", "max_level": 5, "tier": 2},
    {
        "key": "bane_of_arthropods",
        "name_ru": "Бич членистоногих",
        "name_en": "Bane of Arthropods",
        "max_level": 5,
        "tier": 2,
    },
    {"key": "knockback", "name_ru": "Отдача", "name_en": "Knockback", "max_level": 2, "tier": 2},
    {"key": "fire_aspect", "name_ru": "Заговор огня", "name_en": "Fire Aspect", "max_level": 2, "tier": 3},
    {"key": "looting", "name_ru": "Добыча", "name_en": "Looting", "max_level": 3, "tier": 3},
    {
        "key": "sweeping_edge",
        "name_ru": "Разящий клинок",
        "name_en": "Sweeping Edge",
        "max_level": 3,
        "tier": 2,
    },
    # Tools
    {"key": "efficiency", "name_ru": "Эффективность", "name_en": "Efficiency", "max_level": 5, "tier": 2},
    {"key": "silk_touch", "name_ru": "Шёлковое касание", "name_en": "Silk Touch", "max_level": 1, "tier": 4},
    {"key": "unbreaking", "name_ru": "Прочность", "name_en": "Unbreaking", "max_level": 3, "tier": 2},
    {"key": "fortune", "name_ru": "Удача", "name_en": "Fortune", "max_level": 3, "tier": 4},
    # Bow
    {"key": "power", "name_ru": "Сила", "name_en": "Power", "max_level": 5, "tier": 2},
    {"key": "punch", "name_ru": "Отбрасывание", "name_en": "Punch", "max_level": 2, "tier": 2},
    {"key": "flame", "name_ru": "Горящая стрела", "name_en": "Flame", "max_level": 1, "tier": 3},
    {"key": "infinity", "name_ru": "Бесконечность", "name_en": "Infinity", "max_level": 1, "tier": 4},
    # Fishing rod
    {"key": "luck_of_the_sea", "name_ru": "Удача моря", "name_en": "Luck of the Sea", "max_level": 3, "tier": 3},
    {"key": "lure", "name_ru": "Приманка", "name_en": "Lure", "max_level": 3, "tier": 2},
    # Trident
    {"key": "loyalty", "name_ru": "Верность", "name_en": "Loyalty", "max_level": 3, "tier": 3},
    {"key": "impaling", "name_ru": "Пронзатель", "name_en": "Impaling", "max_level": 5, "tier": 2},
    {"key": "riptide", "name_ru": "Тягун", "name_en": "Riptide", "max_level": 3, "tier": 3},
    {"key": "channeling", "name_ru": "Громовержец", "name_en": "Channeling", "max_level": 1, "tier": 4},
    # Crossbow
    {"key": "multishot", "name_ru": "Тройной выстрел", "name_en": "Multishot", "max_level": 1, "tier": 3},
    {"key": "piercing", "name_ru": "Пробивание", "name_en": "Piercing", "max_level": 4, "tier": 2},
    {"key": "quick_charge", "name_ru": "Быстрая перезарядка", "name_en": "Quick Charge", "max_level": 3, "tier": 2},
    # Mace (1.21)
    {"key": "density", "name_ru": "Плотность", "name_en": "Density", "max_level": 5, "tier": 3},
    {"key": "breach", "name_ru": "Пробой", "name_en": "Breach", "max_level": 4, "tier": 3},
    {"key": "wind_burst", "name_ru": "Порыв ветра", "name_en": "Wind Burst", "max_level": 3, "tier": 4},
    # Universal / curses
    {"key": "mending", "name_ru": "Починка", "name_en": "Mending", "max_level": 1, "tier": 5, "treasure": True},
    {
        "key": "vanishing_curse",
        "name_ru": "Проклятие утраты",
        "name_en": "Curse of Vanishing",
        "max_level": 1,
        "tier": 2,
        "treasure": True,
    },
]

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

UNDEFINED_PRICE_KEYS = {
    "ghast_tear",
    "end_crystal",
    "dragon_egg",
    "enchanted_golden_apple",
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


def enchanted_book_price(level: int, tier: int, treasure: bool) -> int:
    level_factor = 2.5 + (level * 1.5)
    tier_factor = 1.0 + (max(1, tier) - 1) * 0.22
    treasure_factor = 1.25 if treasure else 1.0
    return round_price(level_factor * tier_factor * treasure_factor)


def build_enchanted_book_items(start_id: int = 210000) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    next_id = start_id

    for enchant in ENCHANTED_BOOK_VARIANTS:
        enchant_key = str(enchant["key"])
        name_ru = str(enchant["name_ru"])
        name_en = str(enchant["name_en"])
        max_level = int(enchant["max_level"])
        tier = int(enchant.get("tier", 2))
        treasure = bool(enchant.get("treasure", False))

        for level in range(1, max_level + 1):
            roman_level = ROMAN_LEVELS.get(level, str(level))
            result.append(
                {
                    "id": next_id,
                    "key": f"enchanted_book_{enchant_key}_{level}",
                    "icon_key": "enchanted_book",
                    "name_ru": f"Зачарованная книга: {name_ru} {roman_level}",
                    "name_en": f"Enchanted Book: {name_en} {roman_level}",
                    "stack_size": 1,
                    "category": "Зачарованные книги",
                    "obtainability": "Ограниченный" if treasure else "Обычный",
                    "trade_count": 1,
                    "trade_label": "шт",
                    "price_ars": enchanted_book_price(level, tier, treasure),
                }
            )
            next_id += 1

    return result


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


def enforce_antidumping(rows: list[dict[str, object]]) -> None:
    by_key: dict[str, dict[str, object]] = {str(row["key"]): row for row in rows}

    for key, (trade_count, min_price_ars) in ANTI_DUMP_MINIMUMS.items():
        row = by_key.get(key)
        if not row:
            continue
        if row["price_ars"] is None:
            continue
        row["trade_count"] = trade_count
        row["trade_label"] = "шт" if trade_count == 1 else "стак" if trade_count == 64 else f"{trade_count} шт"
        row["price_ars"] = max(int(row["price_ars"]), int(min_price_ars))


def apply_undefined_prices(rows: list[dict[str, object]]) -> None:
    by_key: dict[str, dict[str, object]] = {str(row["key"]): row for row in rows}
    for key in UNDEFINED_PRICE_KEYS:
        row = by_key.get(key)
        if not row:
            continue
        row["trade_count"] = 1
        row["trade_label"] = "шт"
        row["price_ars"] = None
        row["price_note"] = "неопределенно"


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
    enforce_antidumping(out_items)
    apply_undefined_prices(out_items)

    existing_keys = {str(row["key"]) for row in out_items}
    for custom_item in CUSTOM_ITEMS:
        custom_key = str(custom_item["key"])
        if custom_key in existing_keys:
            continue
        out_items.append(dict(custom_item))
        existing_keys.add(custom_key)

    for book_item in build_enchanted_book_items():
        book_key = str(book_item["key"])
        if book_key in existing_keys:
            continue
        out_items.append(book_item)
        existing_keys.add(book_key)

    out_items.sort(key=lambda row: (row["category"], row["name_ru"]))

    payload = {
        "title": "Винд цены",
        "mc_version": VERSION,
        "currency": "ар",
        "currency_note": "1 ар = 1 алмазная руда",
        "pricing_note": "Все цены целые, без дробей. Анти-демпинг для ключевых товаров включен. Отдельные редкие позиции могут иметь статус «неопределенно».",
        "economy_policy": ECONOMY_POLICY,
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
