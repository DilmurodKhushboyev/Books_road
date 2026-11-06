// Do'kon xaritasi: 2 ta uzun qator (bo'lim), har birida old (1-5) va orqa (6-10) javonlar.
import { api } from "./api.js";
import { el, haptic, openSheet, showError, withLoader } from "./ui.js";

function shelfTile(shelf) {
  const arrow = shelf.side === "front" ? "⬆️" : "⬇️";
  return el("button", {
    class: `shelf${shelf.in_stock > 0 ? " filled" : ""}`,
    dataset: { shelfId: shelf.id },
    onclick: () => openShelf(shelf.id),
  }, `${arrow}${shelf.code}`, el("small", { text: `${shelf.in_stock} ta` }));
}

function island(section) {
  const front = section.shelves.filter((s) => s.side === "front");
  const back = section.shelves.filter((s) => s.side !== "front");
  const body = el("div", { class: "island-body" });
  const rows = Math.max(front.length, back.length);
  for (let i = 0; i < rows; i += 1) {
    body.append(front[i] ? shelfTile(front[i]) : el("div"), back[i] ? shelfTile(back[i]) : el("div"));
  }
  return el("div", { class: "island" }, el("div", { class: "island-name", text: section.name }), body);
}

export function renderMap(layout) {
  document.getElementById("store-map").replaceChildren(...layout.map(island));
}

function levelBlock(level, focus) {
  const items = level.items.length
    ? level.items.map((item) => el("div", { class: "level-item" },
        el("span", { text: item.author ? `${item.title} — ${item.author}` : item.title }),
        el("span", { class: `badge ${item.in_stock ? "ok" : "bad"}`, text: item.in_stock ? `${item.quantity} dona` : "Qolmagan" })))
    : [el("div", { class: "muted", text: "Bo'sh" })];
  const block = el("div", { class: "level", id: `level-${level.level}` },
    el("div", { class: "level-title", text: `${level.level}-qator${focus ? " 👈" : ""}` }), ...items);
  return block;
}

export async function openShelf(shelfId, focusLevel = null) {
  try {
    haptic();
    const shelf = await withLoader("Javon yuklanmoqda...", () => api(`/api/shelves/${shelfId}`));
    const content = el("div", {},
      el("h2", { class: "sheet-title", text: `🗄 ${shelf.code} javon · ${shelf.side_label}` }),
      el("div", { class: "muted", text: "1-qator — eng yuqori qator" }),
      ...shelf.levels.map((lvl) => levelBlock(lvl, lvl.level === focusLevel)));
    openSheet(content);
    if (focusLevel) document.getElementById(`level-${focusLevel}`)?.scrollIntoView({ block: "center" });
  } catch (err) {
    showError(err);
  }
}

export function highlightShelf(shelfId) {
  document.querySelectorAll(".shelf.highlight").forEach((n) => n.classList.remove("highlight"));
  const tile = document.querySelector(`.shelf[data-shelf-id="${Number(shelfId)}"]`);
  if (tile) {
    tile.classList.add("highlight");
    tile.scrollIntoView({ block: "center", behavior: "smooth" });
  }
}
