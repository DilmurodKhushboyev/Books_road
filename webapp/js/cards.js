// Mahsulot kartochkasi — chat javoblarida ishlatiladi (qidiruv va rasm bo'yicha topish).
import { api, thumbUrl } from "./api.js";
import { icon } from "./icons.js";
import { el, haptic, showError, toast } from "./ui.js";

function showOnMap(place) {
  window.dispatchEvent(new CustomEvent("br:show-shelf", { detail: { shelfId: place.shelf_id, level: place.level } }));
}

async function changeStock(placementId, action, onChanged) {
  try {
    haptic();
    const view = await api(`/api/placements/${placementId}/stock`, { method: "POST", body: { action } });
    toast("Yangilandi ✅");
    onChanged(view);
  } catch (err) {
    showError(err);
  }
}

function placeBlock(place, canEdit, onChanged) {
  const status = place.in_stock
    ? el("span", { class: "badge ok", text: `Bor · ${place.quantity} dona` })
    : el("span", { class: "badge bad", text: "Qolmagan" });
  const actions = el("div", { class: "place-actions" },
    el("button", { class: "btn small ghost", onclick: () => showOnMap(place) }, icon("pin", 15), "Xaritada"));
  if (canEdit) {
    const id = place.placement_id;
    actions.append(
      el("button", { class: "btn small ghost", text: "−", "aria-label": "Bittaga kamaytirish", onclick: () => changeStock(id, "dec", onChanged) }),
      el("button", { class: "btn small ghost", text: "+", "aria-label": "Bittaga ko'paytirish", onclick: () => changeStock(id, "inc", onChanged) }),
      el("button", { class: "btn small ghost", text: "Qolmadi", onclick: () => changeStock(id, "out", onChanged) }),
    );
  }
  return el("div", { class: "place" },
    el("div", {}, `📍 ${place.location}`),
    el("div", { class: "place-row" }, status, actions));
}

export function itemCard(view, { canEdit = false, extraBadge = null } = {}) {
  const thumb = el("img", { class: "item-thumb", alt: "" });
  thumbUrl(view.item_id).then((url) => { if (url) thumb.src = url; else thumb.classList.add("hidden"); });
  const body = el("div", { class: "item-body" });
  const placesBox = el("div", { class: "item-places" });

  const render = (current) => {
    const head = [
      el("div", { class: "item-title", text: current.title }),
      current.author ? el("div", { class: "item-author", text: current.author }) : null,
      el("div", { class: "item-tags" }, el("span", { class: "badge kind", text: current.kind_label }), extraBadge),
    ];
    // replaceChildren null'ni "null" matniga aylantiradi — bo'shlarini olib tashlaymiz
    body.replaceChildren(...head.filter(Boolean));
    placesBox.replaceChildren(...(current.placements.length
      ? current.placements.map((p) => placeBlock(p, canEdit, render))
      : [el("div", { class: "muted", text: "📍 Javonga joylashtirilmagan" })]));
  };
  render(view);
  return el("div", { class: "item" }, el("div", { class: "item-head" }, thumb, body), placesBox);
}
