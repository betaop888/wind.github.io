"use strict";

const state = {
  items: [],
  filtered: [],
  currency: "ар",
  version: "",
  generatedAt: "",
  query: "",
  category: "all",
  obtainability: "all",
  sort: "priceAsc",
  mode: "item",
};

const refs = {
  searchInput: document.querySelector("#searchInput"),
  clearBtn: document.querySelector("#clearBtn"),
  categorySelect: document.querySelector("#categorySelect"),
  obtainabilitySelect: document.querySelector("#obtainabilitySelect"),
  sortSelect: document.querySelector("#sortSelect"),
  modeButtons: document.querySelectorAll(".mode-btn"),
  categoryChips: document.querySelector("#categoryChips"),
  itemsBody: document.querySelector("#itemsBody"),
  resultMeta: document.querySelector("#resultMeta"),
  metaInfo: document.querySelector("#metaInfo"),
  totalItems: document.querySelector("#totalItems"),
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

const formatPrice = (value) => {
  if (value === null || value === undefined) return "—";
  const num = Number(value);
  if (!Number.isFinite(num)) return "—";
  let text;
  if (Number.isInteger(num)) {
    text = String(num);
  } else if (num < 1) {
    text = num.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  } else if (num < 10) {
    text = num.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
  } else if (num < 100) {
    text = num.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
  } else {
    text = num.toFixed(1).replace(/\.0$/, "");
  }
  return `${text} ${state.currency}`;
};

const activePrice = (item) =>
  state.mode === "stack"
    ? item.price_stack ?? item.price_item
    : item.price_item ?? item.price_stack;

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
    if (state.sort === "priceAsc") return activePrice(a) - activePrice(b);
    if (state.sort === "priceDesc") return activePrice(b) - activePrice(a);
    if (state.sort === "nameDesc") return b.name_ru.localeCompare(a.name_ru, "ru");
    return a.name_ru.localeCompare(b.name_ru, "ru");
  });

  state.filtered = filtered;
}

function renderRows() {
  if (!state.filtered.length) {
    refs.itemsBody.innerHTML =
      '<tr><td class="empty" colspan="7">Ничего не найдено. Сбросьте фильтры или измените запрос.</td></tr>';
    return;
  }

  refs.itemsBody.innerHTML = state.filtered
    .map((item) => {
      const typeClass =
        item.obtainability === "Фармится"
          ? "type-farm"
          : item.obtainability === "Ограниченный"
            ? "type-limited"
            : "";
      const stackText = item.stack_size > 1 ? item.stack_size : "1";
      return `<tr>
        <td>
          <div class="item-name">
            <strong>${escapeHtml(item.name_ru)}</strong>
            <small>${escapeHtml(item.key)} · ${escapeHtml(item.name_en)}</small>
          </div>
        </td>
        <td><span class="badge">${escapeHtml(item.category)}</span></td>
        <td><span class="badge ${typeClass}">${escapeHtml(item.obtainability)}</span></td>
        <td class="muted">${stackText}</td>
        <td class="price">${formatPrice(item.price_item)}</td>
        <td class="price">${item.stack_size > 1 ? formatPrice(item.price_stack) : "—"}</td>
        <td class="price-main">${formatPrice(activePrice(item))}</td>
      </tr>`;
    })
    .join("");
}

function renderMeta() {
  const total = state.items.length;
  const visible = state.filtered.length;
  const modeText = state.mode === "stack" ? "цена за стак" : "цена за 1 шт";

  refs.resultMeta.innerHTML = `<strong>Показано ${visible}</strong> из ${total} позиций`;

  const generatedLabel = state.generatedAt
    ? new Date(state.generatedAt).toLocaleString("ru-RU")
    : "неизвестно";
  refs.metaInfo.textContent = `MC ${state.version} · ${modeText} · обновлено ${generatedLabel}`;
}

function syncModeButtons() {
  refs.modeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === state.mode);
  });
}

function renderCategoryChips() {
  const counts = new Map();
  for (const item of state.items) {
    counts.set(item.category, (counts.get(item.category) || 0) + 1);
  }

  const sortedCategories = Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  const chipsHtml = [
    `<button class="chip ${state.category === "all" ? "active" : ""}" data-category="all" type="button">Все (${state.items.length})</button>`,
    ...sortedCategories.map(
      ([category, count]) =>
        `<button class="chip ${state.category === category ? "active" : ""}" data-category="${escapeHtml(category)}" type="button">${escapeHtml(category)} (${count})</button>`,
    ),
  ].join("");

  refs.categoryChips.innerHTML = chipsHtml;
  refs.categoryChips.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.category = chip.dataset.category || "all";
      refs.categorySelect.value = state.category;
      render();
    });
  });
}

function initCategorySelect() {
  const categories = [...new Set(state.items.map((item) => item.category))].sort((a, b) =>
    a.localeCompare(b, "ru"),
  );

  const options = ['<option value="all">Все категории</option>']
    .concat(categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`))
    .join("");

  refs.categorySelect.innerHTML = options;
}

function render() {
  computeFiltered();
  syncModeButtons();
  renderCategoryChips();
  renderRows();
  renderMeta();
}

function bindEvents() {
  refs.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    render();
  });

  refs.clearBtn.addEventListener("click", () => {
    state.query = "";
    refs.searchInput.value = "";
    render();
  });

  refs.categorySelect.addEventListener("change", (event) => {
    state.category = event.target.value;
    render();
  });

  refs.obtainabilitySelect.addEventListener("change", (event) => {
    state.obtainability = event.target.value;
    render();
  });

  refs.sortSelect.addEventListener("change", (event) => {
    state.sort = event.target.value;
    render();
  });

  refs.modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.mode = button.dataset.mode || "item";
      render();
    });
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

    state.currency = payload.currency || "ар";
    state.version = payload.mc_version || "";
    state.generatedAt = payload.generated_at || "";
    state.items = (payload.items || []).map((item) => ({
      ...item,
      search_text: normalizeText(`${item.name_ru} ${item.name_en} ${item.key}`),
    }));

    refs.totalItems.textContent = String(state.items.length);
    initCategorySelect();
    bindEvents();
    render();
  } catch (error) {
    refs.resultMeta.textContent = "Ошибка загрузки данных.";
    refs.metaInfo.textContent = String(error);
    refs.itemsBody.innerHTML =
      '<tr><td class="empty" colspan="7">Не удалось прочитать `data/items.json`.</td></tr>';
  }
}

bootstrap();
