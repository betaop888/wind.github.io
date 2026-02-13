"use strict";

const state = {
  items: [],
  filtered: [],
  policy: null,
  query: "",
  category: "all",
  obtainability: "all",
  sort: "priceAsc",
  visibleLimit: 220,
  step: 220,
  version: "",
  generatedAt: "",
  currency: "ар",
};

const TEXTURE_ROOT =
  "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.21/assets/minecraft/textures";

const DEFAULT_POLICY = {
  money_in: ["Госзакупки", "Зарплаты госработ", "Малый и крупный бизнес", "Копание аров вручную"],
  money_out: ["Налоги", "Аренда земли", "Лицензии", "Штрафы", "Госпошлины (на доработке)"],
  size_coefficients: [
    "до 100 блоков: без надбавки",
    "101-200 блоков: +20%",
    "200+ блоков: +35%",
  ],
  turnover_tax: {
    trading: "10%",
    service: "15%",
    premium: "20%",
  },
  licenses_spawn: {
    trading_ars: 32,
    service_ars: 48,
    premium_ars: 64,
  },
  licenses_outside_spawn_2weeks: {
    trading_ars: 64,
    service_ars: 72,
    premium_ars: 96,
  },
  anti_dumping: {
    rule: "Цена ниже минимума — штраф или временное закрытие бизнеса.",
    minimum_prices: [
      { key: "netherite_ingot", trade_count: 1, min_price_ars: 20 },
      { key: "beacon", trade_count: 1, min_price_ars: 50 },
      { key: "totem_of_undying", trade_count: 1, min_price_ars: 2 },
      { key: "elytra", trade_count: 1, min_price_ars: 120 },
      { key: "dragon_head", trade_count: 1, min_price_ars: 90 },
      { key: "shulker_shell", trade_count: 1, min_price_ars: 10 },
    ],
  },
};

const refs = {
  searchInput: document.querySelector("#searchInput"),
  clearBtn: document.querySelector("#clearBtn"),
  categorySelect: document.querySelector("#categorySelect"),
  obtainabilitySelect: document.querySelector("#obtainabilitySelect"),
  sortSelect: document.querySelector("#sortSelect"),
  pricingNote: document.querySelector("#pricingNote"),
  itemsBody: document.querySelector("#itemsBody"),
  resultMeta: document.querySelector("#resultMeta"),
  metaInfo: document.querySelector("#metaInfo"),
  totalItems: document.querySelector("#totalItems"),
  showMoreBtn: document.querySelector("#showMoreBtn"),
  unknownCount: document.querySelector("#unknownCount"),
  avgPrice: document.querySelector("#avgPrice"),
  quickButtons: document.querySelectorAll(".quick-btn"),
  activityMap: document.querySelector("#activityMap"),
  moneyInList: document.querySelector("#moneyInList"),
  moneyOutList: document.querySelector("#moneyOutList"),
  sizeCoefficientsList: document.querySelector("#sizeCoefficientsList"),
  turnoverTaxList: document.querySelector("#turnoverTaxList"),
  licenseSpawnList: document.querySelector("#licenseSpawnList"),
  licenseOutsideList: document.querySelector("#licenseOutsideList"),
  antiRuleText: document.querySelector("#antiRuleText"),
  antiDumpTableBody: document.querySelector("#antiDumpTableBody"),
};

const hasCoreRefs =
  !!refs.itemsBody &&
  !!refs.resultMeta &&
  !!refs.metaInfo &&
  !!refs.totalItems &&
  !!refs.searchInput &&
  !!refs.clearBtn &&
  !!refs.categorySelect &&
  !!refs.obtainabilitySelect &&
  !!refs.sortSelect &&
  !!refs.pricingNote;

const normalizeText = (value) =>
  String(value || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "");

const escapeHtml = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const textureUrl = (type, key) => `${TEXTURE_ROOT}/${type}/${encodeURIComponent(key)}.png`;

const itemIconText = (nameRu) => {
  const cleaned = String(nameRu || "").replace(/[^\p{L}\p{N}]/gu, "");
  const short = cleaned.slice(0, 2) || "??";
  return short.toUpperCase();
};

const tradeCountLabel = (count) => `${Number(count) || 1} шт`;

const getNumericPrice = (item) =>
  typeof item.price_ars === "number" && Number.isFinite(item.price_ars)
    ? item.price_ars
    : null;

const formatPrice = (item) => {
  const numeric = getNumericPrice(item);
  if (numeric === null) return item.price_note || "неопределенно";
  return `${numeric} ${state.currency}`;
};

const saleFormatText = (item) => {
  if (item.trade_label === "стак") return `стак (${item.trade_count} шт)`;
  return `${item.trade_count} шт`;
};

function attachIconFallbacks() {
  const icons = document.querySelectorAll(".item-icon");
  if (!icons.length) return;

  const onLoad = (event) => {
    const img = event.currentTarget;
    const media = img.closest(".item-media");
    if (media) media.classList.remove("fallback");
  };

  const onError = (event) => {
    const img = event.currentTarget;
    const media = img.closest(".item-media");
    const altSrc = img.dataset.altSrc;
    const stage = img.dataset.stage || "item";

    if (stage === "item" && altSrc) {
      img.dataset.stage = "block";
      img.src = altSrc;
      return;
    }

    img.classList.add("missing");
    if (media) media.classList.add("fallback");
    img.removeEventListener("load", onLoad);
    img.removeEventListener("error", onError);
  };

  icons.forEach((img) => {
    img.addEventListener("load", onLoad);
    img.addEventListener("error", onError);
  });
}

function renderList(node, values) {
  if (!node || !Array.isArray(values) || !values.length) return;
  node.innerHTML = values.map((value) => `<li>${escapeHtml(value)}</li>`).join("");
}

function renderPolicy() {
  const policy = state.policy || DEFAULT_POLICY;
  if (!policy) return;

  renderList(refs.moneyInList, policy.money_in || policy.moneyIn);
  renderList(refs.moneyOutList, policy.money_out || policy.moneyOut);
  renderList(
    refs.sizeCoefficientsList,
    policy.size_coefficients || policy.sizeCoefficients || [],
  );

  if (refs.turnoverTaxList && policy.turnover_tax) {
    const tax = policy.turnover_tax;
    const rows = [
      `Торговый: +${String(tax.trading || tax.trade || "10%")}`,
      `Сервисный: +${String(tax.service || "15%")}`,
      `Премиальный: +${String(tax.premium || "20%")}`,
    ];
    refs.turnoverTaxList.innerHTML = rows.map((row) => `<li>${escapeHtml(row)}</li>`).join("");
  }

  if (refs.licenseSpawnList && policy.licenses_spawn) {
    const ls = policy.licenses_spawn;
    refs.licenseSpawnList.innerHTML = [
      `Торговый: ${ls.trading_ars ?? ls.trading ?? 32} ар`,
      `Сервисный: ${ls.service_ars ?? ls.service ?? 48} ар`,
      `Премиальный: ${ls.premium_ars ?? ls.premium ?? 64} ар`,
    ]
      .map((line) => `<li>${escapeHtml(line)}</li>`)
      .join("");
  }

  if (refs.licenseOutsideList && policy.licenses_outside_spawn_2weeks) {
    const lo = policy.licenses_outside_spawn_2weeks;
    refs.licenseOutsideList.innerHTML = [
      `Торговый: ${lo.trading_ars ?? lo.trading ?? 64} ар`,
      `Сервисный: ${lo.service_ars ?? lo.service ?? 72} ар`,
      `Премиальный: ${lo.premium_ars ?? lo.premium ?? 96} ар`,
    ]
      .map((line) => `<li>${escapeHtml(line)}</li>`)
      .join("");
  }

  if (refs.antiRuleText && policy.anti_dumping?.rule) {
    refs.antiRuleText.textContent = policy.anti_dumping.rule;
  }

  if (refs.antiDumpTableBody) {
    const mins = policy.anti_dumping?.minimum_prices || [];
    const byKey = new Map(state.items.map((item) => [item.key, item]));

    if (!mins.length) {
      refs.antiDumpTableBody.innerHTML = "<tr><td colspan='3'>Минимумы не заданы.</td></tr>";
      return;
    }

    refs.antiDumpTableBody.innerHTML = mins
      .map((rule) => {
        const item = byKey.get(rule.key);
        const title = item ? item.name_ru : rule.key;
        const currentPrice =
          item && typeof item.price_ars === "number" ? `${item.price_ars} ${state.currency}` : "н/д";
        const minPrice = `${rule.min_price_ars} ${state.currency}`;
        const unit = tradeCountLabel(rule.trade_count);
        return `<tr>
          <td>${escapeHtml(title)}</td>
          <td>${escapeHtml(`${minPrice} (сейчас ${currentPrice})`)}</td>
          <td>${escapeHtml(unit)}</td>
        </tr>`;
      })
      .join("");
  }
}

function computeFiltered() {
  const queryNorm = normalizeText(state.query);

  const filtered = state.items.filter((item) => {
    if (state.category !== "all" && item.category !== state.category) return false;
    if (state.obtainability !== "all" && item.obtainability !== state.obtainability)
      return false;
    if (queryNorm && !item.search_text.includes(queryNorm)) return false;
    return true;
  });

  filtered.sort((a, b) => {
    if (state.sort === "priceAsc" || state.sort === "priceDesc") {
      const aPrice = getNumericPrice(a);
      const bPrice = getNumericPrice(b);

      if (aPrice === null && bPrice === null) {
        return a.name_ru.localeCompare(b.name_ru, "ru");
      }
      if (aPrice === null) return 1;
      if (bPrice === null) return -1;

      if (state.sort === "priceAsc") return aPrice - bPrice;
      return bPrice - aPrice;
    }

    if (state.sort === "nameDesc") return b.name_ru.localeCompare(a.name_ru, "ru");
    return a.name_ru.localeCompare(b.name_ru, "ru");
  });

  state.filtered = filtered;
}

function renderRows() {
  if (!refs.itemsBody) return;
  const rows = state.filtered.slice(0, state.visibleLimit);

  if (!rows.length) {
    refs.itemsBody.innerHTML =
      '<tr><td class="empty" colspan="5">Ничего не найдено. Измени фильтры или поисковый запрос.</td></tr>';
    return;
  }

  refs.itemsBody.innerHTML = rows
    .map((item) => {
      const typeClass =
        item.obtainability === "Фармится"
          ? "farm"
          : item.obtainability === "Ограниченный"
            ? "limit"
            : "";

      const isUnknown = getNumericPrice(item) === null;
      const fallback = escapeHtml(itemIconText(item.name_ru));
      const primaryIcon = escapeHtml(textureUrl("item", item.key));
      const secondaryIcon = escapeHtml(textureUrl("block", item.key));
      const altText = escapeHtml(item.name_ru);

      return `<tr>
        <td>
          <div class="item-row">
            <div class="item-media" data-fallback="${fallback}">
              <img
                class="item-icon"
                loading="lazy"
                decoding="async"
                src="${primaryIcon}"
                data-alt-src="${secondaryIcon}"
                data-stage="item"
                alt="${altText}"
              />
            </div>
            <div class="item">
              <strong>${escapeHtml(item.name_ru)}</strong>
              <small>${escapeHtml(item.key)} · ${escapeHtml(item.name_en)}</small>
            </div>
          </div>
        </td>
        <td><span class="badge">${escapeHtml(item.category)}</span></td>
        <td><span class="badge ${typeClass}">${escapeHtml(item.obtainability)}</span></td>
        <td>${escapeHtml(saleFormatText(item))}</td>
        <td class="price ${isUnknown ? "unknown" : ""}">${escapeHtml(formatPrice(item))}</td>
      </tr>`;
    })
    .join("");

  attachIconFallbacks();
}

function renderMeta() {
  if (!refs.resultMeta || !refs.metaInfo) return;

  const total = state.items.length;
  const matched = state.filtered.length;
  const rendered = Math.min(state.visibleLimit, matched);

  refs.resultMeta.textContent = `Показано ${rendered} из ${matched} (всего ${total})`;

  const unknown = state.items.filter((item) => getNumericPrice(item) === null).length;
  const known = state.items.filter((item) => getNumericPrice(item) !== null);
  const avg =
    known.length > 0
      ? Math.round(
          (known.reduce((acc, item) => acc + Number(getNumericPrice(item) || 0), 0) /
            known.length) *
            100,
        ) / 100
      : 0;

  const generated = state.generatedAt
    ? new Date(state.generatedAt).toLocaleString("ru-RU")
    : "неизвестно";

  refs.metaInfo.textContent = `MC ${state.version} · обновлено ${generated}`;

  if (refs.totalItems) refs.totalItems.textContent = String(total);
  if (refs.unknownCount) refs.unknownCount.textContent = String(unknown);
  if (refs.avgPrice) refs.avgPrice.textContent = `${avg} ${state.currency}`;

  if (refs.showMoreBtn) {
    refs.showMoreBtn.hidden = rendered >= matched;
  }
}

function render() {
  computeFiltered();
  renderRows();
  renderMeta();
}

function resetAndRender() {
  state.visibleLimit = state.step;
  render();
}

function initCategorySelect() {
  if (!refs.categorySelect) return;

  const categories = [...new Set(state.items.map((item) => item.category))].sort((a, b) =>
    a.localeCompare(b, "ru"),
  );

  refs.categorySelect.innerHTML = [
    '<option value="all">Все категории</option>',
    ...categories.map(
      (category) =>
        `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`,
    ),
  ].join("");
}

function bindEvents() {
  if (!hasCoreRefs) return;

  refs.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    resetAndRender();
  });

  refs.clearBtn.addEventListener("click", () => {
    state.query = "";
    refs.searchInput.value = "";
    resetAndRender();
  });

  refs.categorySelect.addEventListener("change", (event) => {
    state.category = event.target.value;
    resetAndRender();
  });

  refs.obtainabilitySelect.addEventListener("change", (event) => {
    state.obtainability = event.target.value;
    resetAndRender();
  });

  refs.sortSelect.addEventListener("change", (event) => {
    state.sort = event.target.value;
    resetAndRender();
  });

  if (refs.showMoreBtn) {
    refs.showMoreBtn.addEventListener("click", () => {
      state.visibleLimit += state.step;
      render();
    });
  }

  if (refs.quickButtons && refs.quickButtons.length) {
    refs.quickButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const quickQuery = button.getAttribute("data-query");
        const quickSort = button.getAttribute("data-sort");

        if (quickQuery) {
          state.query = quickQuery;
          refs.searchInput.value = quickQuery;
          resetAndRender();
          return;
        }

        if (quickSort) {
          state.sort = quickSort;
          refs.sortSelect.value = quickSort;
          resetAndRender();
        }
      });
    });
  }
}

function resolveDataUrl() {
  const scriptWithSrc = document.querySelector('script[src*="app.js"]');
  if (scriptWithSrc && scriptWithSrc.src) {
    return new URL("./data/items.json", scriptWithSrc.src).toString();
  }
  return "./data/items.json";
}

function renderActivityMap() {
  if (!refs.activityMap) return;

  const totalCells = 34 * 8;
  const hotCount = 26;
  const cells = [];

  for (let i = 0; i < totalCells; i += 1) {
    const edgeHot = i >= totalCells - hotCount;
    const rhythmHot = i % 41 === 0 || i % 67 === 0;
    const isHot = edgeHot || rhythmHot;
    cells.push(`<span class="activity-cell ${isHot ? "hot" : ""}"></span>`);
  }

  refs.activityMap.innerHTML = cells.join("");
}

async function bootstrap() {
  if (!refs.resultMeta || !refs.metaInfo || !refs.itemsBody) return;

  refs.resultMeta.textContent = "Загрузка данных...";

  try {
    if (!hasCoreRefs) {
      throw new Error("DOM mismatch: обновите страницу (Ctrl+F5) или очистите кеш.");
    }

    const response = await fetch(resolveDataUrl(), { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();

    state.version = payload.mc_version || "";
    state.generatedAt = payload.generated_at || "";
    state.currency = payload.currency || "ар";
    state.policy = payload.economy_policy || null;

    state.items = (payload.items || []).map((item) => {
      const numericPrice =
        typeof item.price_ars === "number" && Number.isFinite(item.price_ars)
          ? Number(item.price_ars)
          : null;

      return {
        ...item,
        trade_count: Number(item.trade_count) || 1,
        price_ars: numericPrice,
        search_text: normalizeText(
          `${item.name_ru} ${item.name_en} ${item.key} ${item.price_note || ""} ${
            item.category || ""
          } ${item.obtainability || ""}`,
        ),
      };
    });

    if (refs.pricingNote) {
      refs.pricingNote.textContent =
        payload.pricing_note || "Все цены целые. Дробных ар нет.";
    }

    initCategorySelect();
    bindEvents();
    renderActivityMap();
    renderPolicy();
    render();
  } catch (error) {
    refs.resultMeta.textContent = "Ошибка загрузки данных";
    refs.metaInfo.textContent = String(error);
    refs.itemsBody.innerHTML =
      '<tr><td class="empty" colspan="5">Не удалось загрузить файл data/items.json</td></tr>';
    if (refs.showMoreBtn) refs.showMoreBtn.hidden = true;
  }
}

bootstrap();
