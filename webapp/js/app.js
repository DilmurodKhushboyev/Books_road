// Ilova kirish nuqtasi: Telegram sozlamalari, profil, tablar va modullarni ulash.
import { api } from "./api.js";
import { initAdd } from "./add.js";
import { highlightShelf, openShelf, renderMap } from "./map.js";
import { initPhotoFind } from "./photo_find.js";
import { initSearch } from "./search.js";
import { closeSheet, el, haptic, showError, withLoader } from "./ui.js";

const tg = window.Telegram?.WebApp;
let me = null;

function applyTheme() {
  if (tg?.colorScheme) document.documentElement.dataset.theme = tg.colorScheme;
}

function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === name));
  closeSheet();
  window.scrollTo({ top: 0 });
}

async function loadLayout() {
  const data = await api("/api/layout");
  renderMap(data.sections, me.can_edit);
  return data.sections;
}

function bindEvents() {
  document.getElementById("tabbar").addEventListener("click", (event) => {
    const tab = event.target.closest(".tab");
    if (!tab) return;
    haptic();
    showView(tab.dataset.view);
  });
  document.getElementById("sheet-backdrop").addEventListener("click", closeSheet);
  window.addEventListener("br:show-shelf", (event) => {
    showView("map");
    highlightShelf(event.detail.shelfId);
    openShelf(event.detail.shelfId, event.detail.level);
  });
  window.addEventListener("br:layout-changed", () => loadLayout().catch(showError));
}

async function start() {
  tg?.ready();
  tg?.expand();
  applyTheme();
  tg?.onEvent?.("themeChanged", applyTheme);
  bindEvents();
  if (!tg?.initData) {
    document.getElementById("views").replaceChildren(
      el("div", { class: "glass empty", text: "Bu sahifa Telegram bot ichida ochilishi kerak. Botdagi «🗺 Do'kon xaritasi» tugmasini bosing." }));
    return;
  }
  try {
    me = await withLoader("Yuklanmoqda...", () => api("/api/me"));
    document.getElementById("role-badge").textContent = me.is_owner ? "Egasi" : me.can_edit ? "Xodim" : "";
    document.getElementById("tab-add").classList.toggle("hidden", !me.can_edit);
    initSearch(me);
    initPhotoFind(me);
    const layout = await loadLayout();
    initAdd(me, layout);
  } catch (err) {
    showError(err);
  }
}

start();
