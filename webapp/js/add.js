// Javonga qo'shish (xodimlar): javon+qator tanlash -> rasm -> AI ro'yxati -> tahrir -> tasdiqlash.
import { api } from "./api.js";
import { el, percent, showError, toast, withLoader } from "./ui.js";

const MAX_BYTES = 10 * 1024 * 1024;
const DATA_IMAGE_PREFIX = "data:image/jpeg;base64,";
let shelves = [];
let busy = false;

function fillShelves(layout) {
  shelves = layout.flatMap((section) => section.shelves.map((shelf) => ({ ...shelf, section: section.code })));
  const select = document.getElementById("add-shelf");
  select.replaceChildren(...shelves.map((s) =>
    el("option", { value: s.id, text: `${s.code} (${s.side_label})` })));
  fillLevels();
}

function fillLevels() {
  const shelfId = Number(document.getElementById("add-shelf").value);
  const shelf = shelves.find((s) => s.id === shelfId);
  const count = shelf ? shelf.levels_count : 0;
  const select = document.getElementById("add-level");
  select.replaceChildren(...Array.from({ length: count }, (_, i) =>
    el("option", { value: i + 1, text: `${i + 1}-qator` })));
}

function reviewRow(item) {
  const include = el("input", { type: "checkbox", checked: item.include, dataset: { field: "include" } });
  const thumb = item.thumb && item.thumb.startsWith(DATA_IMAGE_PREFIX)
    ? el("img", { class: "item-thumb", src: item.thumb, alt: "" }) : null;
  const row = el("div", { class: `review-item${item.include ? "" : " off"}`, dataset: { index: item.index } },
    include, thumb,
    el("div", { class: "item-body" },
      el("input", { class: "edit-input", value: item.title, maxlength: 255, dataset: { field: "title" }, "aria-label": "Nomi" }),
      el("input", { class: "edit-input", value: item.author, maxlength: 255, placeholder: "Muallif / brend", dataset: { field: "author" } }),
      el("input", { class: "edit-input", type: "number", min: 1, max: 9999, value: item.quantity, dataset: { field: "quantity" }, "aria-label": "Soni" }),
      el("span", { class: "badge kind", text: item.kind_label }),
      item.low_confidence ? el("span", { class: "badge warn", text: `⚠️ ishonch ${percent(item.confidence)} — tekshiring` }) : null));
  include.addEventListener("change", () => row.classList.toggle("off", !include.checked));
  return row;
}

function collectEdits(container) {
  return [...container.querySelectorAll(".review-item")].map((row) => {
    const get = (field) => row.querySelector(`[data-field="${field}"]`);
    const quantity = Math.max(1, Math.min(9999, parseInt(get("quantity").value, 10) || 1));
    return {
      index: Number(row.dataset.index),
      include: get("include").checked,
      title: get("title").value.trim() || undefined,
      author: get("author").value.trim(),
      quantity,
    };
  });
}

async function finish(batchId, action, container) {
  if (busy) return;
  busy = true;
  container.querySelectorAll(".review-actions .btn").forEach((b) => { b.disabled = true; });
  try {
    if (action === "confirm") {
      const res = await withLoader("Saqlanmoqda...", () =>
        api(`/api/recognitions/${batchId}/confirm`, { method: "POST", body: { edits: collectEdits(container) } }));
      toast(`✅ Saqlandi: ${res.saved} ta`);
      window.dispatchEvent(new CustomEvent("br:layout-changed"));
    } else {
      await api(`/api/recognitions/${batchId}/cancel`, { method: "POST" });
      toast("Bekor qilindi");
    }
    container.replaceChildren();
  } catch (err) {
    showError(err);
    container.querySelectorAll(".review-actions .btn").forEach((b) => { b.disabled = false; });
  } finally {
    busy = false;
  }
}

function renderReview(batch) {
  const container = document.getElementById("add-review");
  if (!batch.items.length) {
    container.replaceChildren(el("div", { class: "card empty-note", text: "🤷 Rasmda hech narsa aniqlanmadi. Yaqinroqdan qayta suring." }));
    return;
  }
  container.replaceChildren(
    el("div", { class: "card" },
      el("h2", { class: "sheet-title", text: `🧾 AI ${batch.items.length} ta narsa topdi` }),
      el("div", { class: "muted", text: `O'rtacha ishonch ${percent(batch.avg_confidence)}. ⚠️ belgililarni tekshiring, nomini tuzating.` })),
    el("div", { class: "list" }, ...batch.items.map(reviewRow)),
    el("div", { class: "review-actions" },
      el("button", { class: "btn ghost", text: "❌ Bekor", onclick: () => finish(batch.batch_id, "cancel", container) }),
      el("button", { class: "btn primary", text: "💾 Tasdiqlash", onclick: () => finish(batch.batch_id, "confirm", container) })));
}

async function onPhoto(file) {
  if (!file) return;
  if (file.size > MAX_BYTES) {
    toast("Rasm 10 MB dan katta.", true);
    return;
  }
  const form = new FormData();
  form.append("shelf_id", document.getElementById("add-shelf").value);
  form.append("level", document.getElementById("add-level").value);
  form.append("photo", file);
  try {
    const batch = await withLoader("🤖 AI javonni o'qiyapti... (10-30 soniya)", () =>
      api("/api/recognitions", { method: "POST", form }));
    renderReview(batch);
  } catch (err) {
    showError(err);
  }
}

export function initAdd(me, layout) {
  if (!me.can_edit) return;
  document.getElementById("add-level-hint").textContent = me.level_hint;
  fillShelves(layout);
  document.getElementById("add-shelf").addEventListener("change", fillLevels);
  const input = document.getElementById("add-photo-input");
  input.addEventListener("change", () => {
    onPhoto(input.files[0]);
    input.value = "";
  });
}
