# Винд цены (GitHub Pages)

Статический сайт с прайсом выживаемых предметов/блоков Minecraft **1.21.11**.  
Валюта: **ар** (`1 ар = 1 алмазная руда`).

## Что внутри

- `index.html` — страница.
- `styles.css` — тёмный Wind-стиль + SVG/анимации.
- `app.js` — поиск, фильтры, сортировка, режим цен.
- `data/items.json` — сгенерированный прайс (1388 позиций).
- `scripts/build_items.py` — регенерация прайса из актуальных данных.

## Публикация на GitHub Pages

1. Создай репозиторий на GitHub.
2. Залей содержимое папки `wind-ceny` в корень репозитория.
3. В GitHub зайди в `Settings` -> `Pages`.
4. В `Build and deployment` выбери:
   `Source: Deploy from a branch`, ветку `main`, папку `/ (root)`.
5. Сохрани. Через 1-2 минуты сайт появится по ссылке GitHub Pages.

## Обновить цены

```bash
python scripts/build_items.py
```

После генерации закоммить `data/items.json` и залей изменения.
