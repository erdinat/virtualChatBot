/**
 * localStorage güvenli sarmalayıcı.
 *
 * Tarayıcı private browsing modunda, quota aşıldığında veya storage devre dışı
 * bırakıldığında localStorage erişimi exception fırlatır. Render path'inde
 * patlamayı önlemek için bu yardımcıları kullanın.
 */

export function safeGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function safeSet(key: string, value: string): boolean {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

export function safeRemove(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

/**
 * localStorage'dan sayı okur. Anahtar yoksa, parse edilemezse veya
 * storage erişimi başarısız olursa fallback döner.
 */
export function safeGetInt(key: string, fallback = 0): number {
  const raw = safeGet(key);
  if (raw === null) return fallback;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? n : fallback;
}
