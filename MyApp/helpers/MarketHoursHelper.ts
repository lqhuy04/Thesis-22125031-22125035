import type { Language } from "@/hooks/LocalizationContext";

/**
 * Lịch giao dịch HOSE/HNX (giờ Việt Nam, chỉ Thứ 2 - Thứ 6):
 *   Mở cửa        : 09:00
 *   Nghỉ trưa     : 11:30 - 13:00
 *   Đóng cửa      : 14:45 (VNINDEX/VN30/VN100) | 15:00 (HNXINDEX/HNXUPCOMINDEX)
 */

export type MarketStatus = "open" | "lunch" | "closed";

export interface MarketState {
  status: MarketStatus;
  /** Thời điểm mở cửa (hoặc mở lại phiên) kế tiếp. null khi đang giao dịch. */
  nextOpen: Date | null;
  /** Thời điểm đóng cửa cuối ngày. Chỉ có giá trị khi đang giao dịch. */
  closeAt: Date | null;
}

const OPEN = 9 * 60; // 09:00
const MORNING_END = 11 * 60 + 30; // 11:30
const AFTERNOON_START = 13 * 60; // 13:00

const HNX_INDEXES = ["HNXINDEX", "HNXUPCOMINDEX"];

const minutesOfDay = (d: Date): number => d.getHours() * 60 + d.getMinutes();

const isWeekday = (d: Date): boolean => {
  const day = d.getDay();
  return day >= 1 && day <= 5;
};

/** Phút đóng cửa trong ngày tuỳ theo chỉ số. */
const getCloseMinutes = (indexId?: string): number => {
  const id = (indexId ?? "").toUpperCase();
  return HNX_INDEXES.includes(id) ? 15 * 60 : 14 * 60 + 45;
};

const atTime = (base: Date, hour: number, minute: number): Date => {
  const d = new Date(base);
  d.setHours(hour, minute, 0, 0);
  return d;
};

const computeNextOpen = (now: Date, status: MarketStatus): Date | null => {
  if (status === "open") return null;

  // Đang nghỉ trưa -> mở lại phiên chiều lúc 13:00 cùng ngày.
  if (status === "lunch") return atTime(now, 13, 0);

  // Đóng cửa: nếu hôm nay là ngày giao dịch và còn trước 09:00 -> mở cửa hôm nay.
  if (isWeekday(now) && minutesOfDay(now) < OPEN) return atTime(now, 9, 0);

  // Ngược lại tìm ngày giao dịch kế tiếp lúc 09:00.
  const d = atTime(now, 9, 0);
  do {
    d.setDate(d.getDate() + 1);
  } while (!isWeekday(d));
  return d;
};

const computeCloseAt = (
  now: Date,
  status: MarketStatus,
  closeMinutes: number,
): Date | null => {
  if (status !== "open") return null;
  return atTime(now, Math.floor(closeMinutes / 60), closeMinutes % 60);
};

/** Xác định trạng thái thị trường tại thời điểm `now` cho một chỉ số. */
export const getMarketState = (
  indexId?: string,
  now: Date = new Date(),
): MarketState => {
  const cur = minutesOfDay(now);
  const closeMinutes = getCloseMinutes(indexId);

  let status: MarketStatus = "closed";
  if (isWeekday(now)) {
    if (
      (cur >= OPEN && cur < MORNING_END) ||
      (cur >= AFTERNOON_START && cur < closeMinutes)
    ) {
      status = "open";
    } else if (cur >= MORNING_END && cur < AFTERNOON_START) {
      status = "lunch";
    }
  }

  return {
    status,
    nextOpen: computeNextOpen(now, status),
    closeAt: computeCloseAt(now, status, closeMinutes),
  };
};

const pad = (n: number): string => (n < 10 ? `0${n}` : `${n}`);

const WEEKDAYS: Record<Language, string[]> = {
  // index theo Date.getDay(): 0 = Chủ nhật ... 6 = Thứ 7
  vi: ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"],
  en: [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ],
};

/** Định dạng "09:00 Thứ 6 05/06/2026" / "09:00 Friday 05/06/2026". */
export const formatNextOpen = (date: Date, language: Language): string => {
  const time = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  const weekday = WEEKDAYS[language][date.getDay()];
  const dateStr = `${pad(date.getDate())}/${pad(
    date.getMonth() + 1
  )}/${date.getFullYear()}`;
  return `${time} ${weekday} ${dateStr}`;
};
