// API "eshigi": barcha so'rovlar shu yerdan, Telegram initData header bilan.
const tg = window.Telegram?.WebApp;

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function authHeaders() {
  return { "X-Telegram-Init-Data": tg?.initData || "" };
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = authHeaders();
  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, { method, headers, body: payload });
  } catch {
    throw new ApiError("Internet aloqasi yo'q. Qayta urinib ko'ring.", 0, "network");
  }
  return res;
}

export async function api(path, options) {
  const res = await request(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(data.message || "Kutilmagan xatolik yuz berdi.", res.status, data.error);
  }
  return data;
}

const thumbCache = new Map();

// Rasm ham avtorizatsiya talab qiladi -> blob URL orqali ko'rsatamiz
export async function thumbUrl(itemId) {
  if (thumbCache.has(itemId)) return thumbCache.get(itemId);
  const res = await request(`/api/items/${encodeURIComponent(itemId)}/thumb`);
  const url = res.ok ? URL.createObjectURL(await res.blob()) : null;
  thumbCache.set(itemId, url);
  return url;
}
