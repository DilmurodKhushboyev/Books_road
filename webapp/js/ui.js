// Kichik UI yordamchilari. Matn faqat textContent orqali qo'yiladi (XSS himoyasi).
const tg = window.Telegram?.WebApp;

export function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "dataset") Object.assign(node.dataset, value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

let toastTimer;
export function toast(message, isError = false) {
  const node = document.getElementById("toast");
  node.textContent = message;
  node.classList.toggle("error", isError);
  node.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.add("hidden"), 3200);
  haptic(isError ? "error" : "success");
}

export function haptic(type = "light") {
  try {
    if (type === "light") tg?.HapticFeedback?.impactOccurred("light");
    else tg?.HapticFeedback?.notificationOccurred(type);
  } catch (err) {
    console.debug("haptic", err);
  }
}

export async function withLoader(text, fn) {
  const loader = document.getElementById("loader");
  document.getElementById("loader-text").textContent = text;
  loader.classList.remove("hidden");
  try {
    return await fn();
  } finally {
    loader.classList.add("hidden");
  }
}

export function showError(err) {
  console.warn(err);
  toast(err?.message || "Kutilmagan xatolik yuz berdi.", true);
}

export function openSheet(content) {
  const box = document.getElementById("sheet-content");
  box.replaceChildren(content);
  document.getElementById("sheet").classList.remove("hidden");
  document.getElementById("sheet-backdrop").classList.remove("hidden");
}

export function closeSheet() {
  document.getElementById("sheet").classList.add("hidden");
  document.getElementById("sheet-backdrop").classList.add("hidden");
}

export function percent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}
