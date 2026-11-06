// Nom bo'yicha qidiruv.
import { api } from "./api.js";
import { emptyState, itemCard } from "./cards.js";
import { el, showError } from "./ui.js";

const MIN_LEN = 2;
let canEdit = false;

async function runSearch(query) {
  const box = document.getElementById("search-results");
  if (query.trim().length < MIN_LEN) {
    box.replaceChildren(emptyState("Kamida 2 ta harf yozing."));
    return;
  }
  box.replaceChildren(el("div", { class: "empty", text: "⏳ Qidirilmoqda..." }));
  try {
    const data = await api(`/api/search?q=${encodeURIComponent(query.trim())}`);
    box.replaceChildren(...(data.results.length
      ? data.results.map((view) => itemCard(view, { canEdit }))
      : [emptyState(`😔 «${query}» topilmadi. Boshqacha yozib ko'ring yoki rasm bilan qidiring.`)]));
  } catch (err) {
    box.replaceChildren();
    showError(err);
  }
}

export function initSearch(me) {
  canEdit = me.can_edit;
  const form = document.getElementById("search-form");
  const input = document.getElementById("search-input");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    input.blur();
    runSearch(input.value);
  });
  document.getElementById("search-results").replaceChildren(
    emptyState("📚 Kitob, atir, joynamoz... nomini yozing — qaysi javonda ekanini ko'rsataman."));
}
