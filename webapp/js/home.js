// Bosh sahifa: avatar, salomlashish, rol belgisi, tezkor kartochkalar.
import { icon } from "./icons.js";
import { el } from "./ui.js";

const tg = window.Telegram?.WebApp;
const SAFE_PHOTO_PREFIX = "https://";

function renderAvatar(user) {
  const box = document.getElementById("avatar");
  const photo = user?.photo_url;
  if (typeof photo === "string" && photo.startsWith(SAFE_PHOTO_PREFIX)) {
    const img = el("img", { alt: "" });
    img.src = photo;
    img.addEventListener("error", () => box.replaceChildren((user.first_name || "B").charAt(0)));
    box.replaceChildren(img);
  } else {
    box.textContent = (user?.first_name || "B").charAt(0).toUpperCase();
  }
}

function quickCard(iconName, title, subtitle, onClick) {
  return el("button", { class: "quick", type: "button", onclick: onClick },
    el("div", { class: "quick-icon" }, icon(iconName, 20)),
    el("h3", { text: title }),
    el("p", { text: subtitle }));
}

function totalItems(layout) {
  return layout.reduce((sum, section) => sum + section.shelves.reduce((acc, s) => acc + s.in_stock, 0), 0);
}

export function initHome(me, layout, actions) {
  const user = tg?.initDataUnsafe?.user;
  renderAvatar(user);
  document.getElementById("hello").textContent = `Salom, ${user?.first_name || "do'stim"} 👋`;
  if (me.can_edit) {
    const pill = document.getElementById("role-pill");
    pill.querySelector("span").textContent = me.is_owner ? "Do'kon egasi" : "Xodim";
    pill.classList.remove("hidden");
  }
  const shelves = layout.reduce((sum, section) => sum + section.shelves.length, 0);
  const cards = [
    quickCard("search", "Nom bilan qidirish", "Kitob, atir, joynamoz...", actions.chat),
    quickCard("camera", "Rasm bilan topish", "Muqovani suring — AI topadi", actions.photo),
    quickCard("map", "Do'kon xaritasi", `${layout.length} bo'lim, ${shelves} javon`, actions.map),
    me.can_edit
      ? quickCard("plus", "Javonga qo'shish", "Javon rasmidan kiritish", actions.add)
      : quickCard("help", "Qanday ishlaydi", "3 qadamda topish", actions.help),
  ];
  document.getElementById("quick-grid").replaceChildren(...cards);
  return totalItems(layout);
}
