// Kirish nuqtasi: Telegram (to'liq ekran), profil, navigatsiya va modullarni ulash.
import { initAdd } from "./add.js";
import { api } from "./api.js";
import { ask, findByPhoto, initChat } from "./chat.js";
import { initHome } from "./home.js";
import { hydrateIcons, icon } from "./icons.js";
import { highlightShelf, openShelf, renderMap } from "./map.js";
import { closeSheet, el, haptic, showError, withLoader } from "./ui.js";

const tg = window.Telegram?.WebApp;
const MOBILE_PLATFORMS = ["android", "ios"];
let me = null;

function applyTheme() {
  if (tg?.colorScheme) document.documentElement.dataset.theme = tg.colorScheme;
  const bg = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
  try {
    tg?.setHeaderColor?.(bg);
    tg?.setBackgroundColor?.(bg);
    tg?.setBottomBarColor?.(bg);
  } catch (err) {
    console.debug("theme colors", err);
  }
}

// Telegram'ning yuqori panelini yashirib, ilovani butun ekranga yoyish (Bot API 8.0+, mobil)
function goFullscreen() {
  if (!tg) return;
  tg.expand();
  try {
    if (tg.isVersionAtLeast?.("7.7")) tg.disableVerticalSwipes();
    if (tg.isVersionAtLeast?.("8.0") && MOBILE_PLATFORMS.includes(tg.platform) && !tg.isFullscreen) {
      tg.requestFullscreen();
    }
  } catch (err) {
    console.debug("fullscreen", err);
  }
}

export function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  closeSheet();
  window.scrollTo({ top: 0 });
}

function pickPhoto() {
  haptic();
  document.getElementById("find-photo-input").click();
}

function bindNavigation() {
  document.getElementById("nav").addEventListener("click", (event) => {
    const button = event.target.closest(".nav-btn");
    if (!button) return;
    haptic();
    showView(button.dataset.view);
  });
  document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => showView(b.dataset.go)));
  document.getElementById("nav-photo").addEventListener("click", pickPhoto);
  document.getElementById("chat-photo").addEventListener("click", pickPhoto);
  document.getElementById("sheet-backdrop").addEventListener("click", closeSheet);

  const photoInput = document.getElementById("find-photo-input");
  photoInput.addEventListener("change", () => {
    const file = photoInput.files[0];
    photoInput.value = "";
    if (!file) return;
    showView("chat");
    findByPhoto(file);
  });
  document.getElementById("home-ask").addEventListener("submit", (event) => {
    event.preventDefault();
    const input = document.getElementById("home-input");
    const query = input.value;
    input.value = "";
    input.blur();
    showView("chat");
    ask(query);
  });
  window.addEventListener("br:show-shelf", (event) => {
    showView("map");
    highlightShelf(event.detail.shelfId);
    openShelf(event.detail.shelfId, event.detail.level);
  });
  window.addEventListener("br:layout-changed", () => loadLayout().catch(showError));
}

async function loadLayout() {
  const data = await api("/api/layout");
  renderMap(data.sections);
  return data.sections;
}

function setupStaffNav() {
  const last = document.getElementById("nav-last");
  last.dataset.view = "add";
  last.setAttribute("aria-label", "Javonga qo'shish");
  last.replaceChildren(icon("plus"));
}

async function start() {
  hydrateIcons();
  bindNavigation();
  tg?.ready();
  goFullscreen();
  applyTheme();
  tg?.onEvent?.("themeChanged", applyTheme);
  if (!tg?.initData) {
    document.getElementById("app").replaceChildren(el("div", { class: "card empty-note",
      text: "Bu sahifa Telegram bot ichida ochilishi kerak. Botdagi «🗺 Do'kon xaritasi» tugmasini bosing." }));
    return;
  }
  try {
    me = await withLoader("Yuklanmoqda...", () => api("/api/me"));
    if (me.can_edit) setupStaffNav();
    initChat(me);
    const layout = await loadLayout();
    initHome(me, layout, {
      chat: () => showView("chat"), photo: pickPhoto, map: () => showView("map"),
      add: () => showView("add"), help: () => showView("help"),
    });
    initAdd(me, layout);
  } catch (err) {
    showError(err);
  }
}

start();
