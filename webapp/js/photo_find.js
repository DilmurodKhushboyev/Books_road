// Rasm bo'yicha topish (AI).
import { api } from "./api.js";
import { emptyState, itemCard } from "./cards.js";
import { el, percent, showError, toast, withLoader } from "./ui.js";

const MAX_BYTES = 10 * 1024 * 1024;
let canEdit = false;

function queryInfo(result) {
  const q = result.query;
  const text = `👁 AI ko'rdi: ${q.title}${q.author ? ` — ${q.author}` : ""} (ishonch ${percent(q.confidence)})`;
  const card = el("div", { class: "glass card" }, el("div", { text }));
  if (result.results.length && !result.confident) {
    card.append(el("span", { class: "badge warn", text: "⚠️ Aniq emas — eng o'xshash variantlar" }));
  }
  return card;
}

async function onFile(file) {
  const box = document.getElementById("photo-results");
  if (!file) return;
  if (file.size > MAX_BYTES) {
    toast("Rasm 10 MB dan katta.", true);
    return;
  }
  const form = new FormData();
  form.append("photo", file);
  try {
    const result = await withLoader("🤖 AI rasmni tahlil qilyapti...", () =>
      api("/api/find-by-photo", { method: "POST", form }));
    if (!result.recognized) {
      box.replaceChildren(emptyState("🤷 Rasmdagi narsani aniqlay olmadim. Yaqinroqdan, tiniq suring."));
      return;
    }
    const cards = result.results.map((view) => itemCard(view, {
      canEdit,
      extraBadge: el("span", { class: "badge warn", text: `o'xshashlik ${percent(view.score)}` }),
    }));
    box.replaceChildren(queryInfo(result), ...(cards.length ? cards : [emptyState("😔 Bazada o'xshash narsa topilmadi.")]));
  } catch (err) {
    showError(err);
  }
}

export function initPhotoFind(me) {
  canEdit = me.can_edit;
  const input = document.getElementById("find-photo-input");
  input.addEventListener("change", () => {
    onFile(input.files[0]);
    input.value = "";
  });
}
