"use strict";

const state = {
  items: [],
  filtered: [],
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
  activityMap: document.querySelector("#activityMap"),
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

      return `<tr>
        <td>
          <div class="item">
            <strong>${escapeHtml(item.name_ru)}</strong>
            <small>${escapeHtml(item.key)} · ${escapeHtml(item.name_en)}</small>
          </div>
        </td>
        <td><span class="badge">${escapeHtml(item.category)}</span></td>
        <td><span class="badge ${typeClass}">${escapeHtml(item.obtainability)}</span></td>
        <td>${escapeHtml(saleFormatText(item))}</td>
        <td class="price ${isUnknown ? "unknown" : ""}">${escapeHtml(formatPrice(item))}</td>
      </tr>`;
    })
    .join("");
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
          `${item.name_ru} ${item.name_en} ${item.key} ${item.price_note || ""}`,
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
