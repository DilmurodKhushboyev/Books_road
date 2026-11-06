// Mahsulot kartochkasi — qidiruv va rasm bo'yicha topish natijalari uchun umumiy.
import { api, thumbUrl } from "./api.js";
import { el, haptic, showError, toast } from "./ui.js";

function showOnMap(place) {
  window.dispatchEvent(new CustomEvent("br:show-shelf", { detail: { shelfId: place.shelf_id, level: place.level } }));
}

async function changeStock(placementId, action, onChanged) {
  try {
    haptic();
    const view = await api(`/api/placements/${placementId}/stock`, { method: "POST", body: { action } });
    toast("Yangilandi ✅");
    onChanged?.(view);
  } catch (err) {
    showError(err);
  }
}

function placeRow(place, canEdit, onChanged) {
  const status = place.in_stock
    ? el("span", { class: "badge ok", text: `✅ Bor: ${place.quantity} dona` })
    : el("span", { class: "badge bad", text: "❌ Qolmagan" });
  const actions = el("div", { class: "place-actions" },
    el("button", { class: "btn small ghost", text: "🗺 Xaritada", onclick: () => showOnMap(place) }));
  if (canEdit) {
    const id = place.placement_id;
    actions.append(
      el("button", { class: "btn small ghost", text: "➖", onclick: () => changeStock(id, "dec", onChanged) }),
      el("button", { class: "btn small ghost", text: "➕", onclick: () => changeStock(id, "inc", onChanged) }),
      el("button", { class: "btn small ghost", text: "❌ Qolmadi", onclick: () => changeStock(id, "out", onChanged) }),
    );
  }
  return el("div", { class: "place" }, el("div", { text: `📍 ${place.location}` }), status, actions);
}

export function itemCard(view, { canEdit = false, extraBadge = null } = {}) {
  const thumb = el("img", { class: "item-thumb", alt: "" });
  thumbUrl(view.item_id).then((url) => { if (url) thumb.src = url; else thumb.classList.add("hidden"); });
  const body = el("div", { class: "item-body" });
  const card = el("div", { class: "glass item" }, thumb, body);

  const render = (current) => {
    const places = current.placements.length
      ? current.placements.map((p) => placeRow(p, canEdit, render))
      : [el("div", { class: "muted", text: "📍 Javonga joylashtirilmagan" })];
    const children = [
      el("div", { class: "item-title", text: current.title }),
      current.author ? el("div", { class: "item-author", text: current.author }) : null,
      el("span", { class: "badge ok", text: current.kind_label }),
      extraBadge,
      ...places,
    ];
    // replaceChildren null'ni "null" matniga aylantiradi — bo'shlarini olib tashlaymiz
    body.replaceChildren(...children.filter(Boolean));
  };
  render(view);
  return card;
}

export function emptyState(text) {
  return el("div", { class: "glass empty", text });
}
