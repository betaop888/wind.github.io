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
};

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

const formatPrice = (value) => `${Number(value)} ${state.currency}`;

const saleFormatText = (item) => {
  if (item.trade_label === "стак") return `стак (${item.trade_count} шт)`;
  if (item.trade_label === "шт") return "1 шт";
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
    if (state.sort === "priceAsc") return a.price_ars - b.price_ars;
    if (state.sort === "priceDesc") return b.price_ars - a.price_ars;
    if (state.sort === "nameDesc") return b.name_ru.localeCompare(a.name_ru, "ru");
    return a.name_ru.localeCompare(b.name_ru, "ru");
  });

  state.filtered = filtered;
}

function renderRows() {
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
        <td class="price">${formatPrice(item.price_ars)}</td>
      </tr>`;
    })
    .join("");
}

function renderMeta() {
  const total = state.items.length;
  const matched = state.filtered.length;
  const rendered = Math.min(state.visibleLimit, matched);

  refs.resultMeta.textContent = `Показано ${rendered} из ${matched} (всего ${total})`;

  const generated = state.generatedAt
    ? new Date(state.generatedAt).toLocaleString("ru-RU")
    : "неизвестно";
  refs.metaInfo.textContent = `MC ${state.version} · обновлено ${generated}`;

  refs.showMoreBtn.hidden = rendered >= matched;
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

  refs.showMoreBtn.addEventListener("click", () => {
    state.visibleLimit += state.step;
    render();
  });
}

async function bootstrap() {
  refs.resultMeta.textContent = "Загрузка данных...";
  try {
    const response = await fetch("./data/items.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();

    state.version = payload.mc_version || "";
    state.generatedAt = payload.generated_at || "";
    state.currency = payload.currency || "ар";

    state.items = (payload.items || []).map((item) => ({
      ...item,
      search_text: normalizeText(`${item.name_ru} ${item.name_en} ${item.key}`),
    }));

    refs.totalItems.textContent = String(state.items.length);
    refs.pricingNote.textContent =
      payload.pricing_note || "Все цены целые. Дробных ар нет.";

    initCategorySelect();
    bindEvents();
    render();
  } catch (error) {
    refs.resultMeta.textContent = "Ошибка загрузки данных";
    refs.metaInfo.textContent = String(error);
    refs.itemsBody.innerHTML =
      '<tr><td class="empty" colspan="5">Не удалось загрузить файл data/items.json</td></tr>';
    refs.showMoreBtn.hidden = true;
  }
}

bootstrap();
