// "Aqlli qidiruv" suhbati: nom bo'yicha qidiruv va rasm bo'yicha topish natijalari.
import { api } from "./api.js";
import { itemCard } from "./cards.js";
import { el, percent, showError, toast, withLoader } from "./ui.js";

const MIN_LEN = 2;
const MAX_BYTES = 10 * 1024 * 1024;
const WELCOME = "Salom! 👋 Kitob, atir yoki joynamoz nomini yozing — qaysi bo'lim, javon va qatorda ekanini topaman. 📷 tugmasi bilan rasm ham yuborishingiz mumkin.";
let canEdit = false;
let busy = false;

const log = () => document.getElementById("chat-log");

function now() {
  return new Date().toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" });
}

// Faqat chat ochiq bo'lsa suramiz (aks holda bosh sahifa o'z-o'zidan pastga tushib qoladi)
function scrollDown() {
  if (!document.getElementById("view-chat").classList.contains("active")) return;
  requestAnimationFrame(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }));
}

function userBubble(content) {
  log().append(el("div", { class: "msg-user" }, content, el("span", { class: "msg-time", text: now() })));
  scrollDown();
}

function botBubble(...children) {
  const bubble = el("div", { class: "msg-bubble" }, ...children);
  log().append(el("div", { class: "msg-bot" }, el("span", { class: "mini-orb" }), bubble));
  scrollDown();
  return bubble;
}

function typingBubble() {
  return botBubble(el("div", { class: "typing" }, el("span"), el("span"), el("span")));
}

export function resetChat() {
  log().replaceChildren();
  botBubble(el("p", { text: WELCOME }));
}

export async function ask(query) {
  const text = (query || "").trim();
  if (text.length < MIN_LEN) {
    toast("Kamida 2 ta harf yozing.", true);
    return;
  }
  if (busy) return;
  busy = true;
  userBubble(text);
  const bubble = typingBubble();
  try {
    const data = await api(`/api/search?q=${encodeURIComponent(text)}`);
    const cards = data.results.map((view) => itemCard(view, { canEdit }));
    bubble.replaceChildren(cards.length
      ? el("p", { text: `«${text}» bo'yicha ${cards.length} ta natija:` })
      : el("p", { text: `😔 «${text}» topilmadi. Boshqacha yozib ko'ring yoki rasm yuboring.` }), ...cards);
  } catch (err) {
    bubble.replaceChildren(el("p", { text: err.message || "Xatolik yuz berdi." }));
    showError(err);
  } finally {
    busy = false;
    scrollDown();
  }
}

function photoAnswer(result) {
  if (!result.recognized) {
    return [el("p", { text: "🤷 Rasmdagi narsani aniqlay olmadim. Muqovani yaqinroqdan, tiniq suring." })];
  }
  const q = result.query;
  const seen = el("p", { text: `👁 Ko'rdim: ${q.title}${q.author ? ` — ${q.author}` : ""} (ishonch ${percent(q.confidence)})` });
  if (!result.results.length) return [seen, el("p", { text: "😔 Bazada bunga o'xshash narsa topilmadi." })];
  const note = result.confident ? null : el("span", { class: "badge warn", text: "⚠️ Aniq emas — eng o'xshash variantlar" });
  const cards = result.results.map((view) => itemCard(view, {
    canEdit, extraBadge: el("span", { class: "badge warn", text: `o'xshashlik ${percent(view.score)}` }),
  }));
  return [seen, note, ...cards].filter(Boolean);
}

export async function findByPhoto(file) {
  if (!file) return;
  if (file.size > MAX_BYTES) {
    toast("Rasm 10 MB dan katta.", true);
    return;
  }
  const preview = el("img", { alt: "" });
  preview.src = URL.createObjectURL(file);
  userBubble(preview);
  const form = new FormData();
  form.append("photo", file);
  try {
    const result = await withLoader("Rasmni ko'ryapman...", () => api("/api/find-by-photo", { method: "POST", form }));
    botBubble(...photoAnswer(result));
  } catch (err) {
    botBubble(el("p", { text: err.message || "Xatolik yuz berdi." }));
    showError(err);
  }
}

export function initChat(me) {
  canEdit = me.can_edit;
  resetChat();
  const input = document.getElementById("chat-input");
  document.getElementById("chat-ask").addEventListener("submit", (event) => {
    event.preventDefault();
    const value = input.value;
    input.value = "";
    ask(value);
  });
  document.getElementById("chat-new").addEventListener("click", resetChat);
}
