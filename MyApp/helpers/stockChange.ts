type ChangePalette = {
  success: string;
  warning: string;
  error: string;
};

type NumberFormatOptions = Pick<
  Intl.NumberFormatOptions,
  "minimumFractionDigits" | "maximumFractionDigits"
>;

const DEFAULT_FORMAT_OPTIONS: NumberFormatOptions = {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
};

const normalizeZero = (value: number) => (value === 0 ? 0 : value);

export const getStockChangeColor = (
  value: number | null | undefined,
  palette: ChangePalette,
) => {
  if (value == null) return palette.warning;
  if (value > 0) return palette.success;
  if (value < 0) return palette.error;
  return palette.warning;
};

export const formatPriceChange = (
  value: number | null | undefined,
  options: NumberFormatOptions = DEFAULT_FORMAT_OPTIONS,
) => {
  if (value == null) return "--";
  const normalizedValue = normalizeZero(value);
  const prefix = normalizedValue > 0 ? "+" : "";
  return `${prefix}${normalizedValue.toLocaleString("vi-VN", options)}`;
};

export const formatPercentageChange = (
  value: number | null | undefined,
  options: NumberFormatOptions = DEFAULT_FORMAT_OPTIONS,
) => {
  if (value == null) return "--";
  const normalizedValue = normalizeZero(value);
  const arrow = normalizedValue > 0 ? "▲ " : normalizedValue < 0 ? "▼ " : "";
  const percentage = Math.abs(normalizedValue).toLocaleString("vi-VN", options);
  return `${arrow}${percentage}%`;
};
