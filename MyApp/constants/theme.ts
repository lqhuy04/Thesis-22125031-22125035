// theme.ts

/* =========================
   Light theme
   ========================= */

export const lightTheme = {
  mode: "light",

  base: {
    primary: "#613DE4",
    primaryHover: "#4E31B6",
    attention: "#FACC15",
    warning: "#F59E0B",
    error: "#EF4444",
    success: "#3BB266",
    info: "#F5F7FC",
  },

  background: {
    bg: "#FBFCFE",
    surface: "#F5F7FC",
    primarySurface: "#613de430",
  },

  text: {
    onPrimary: "#FFFFFF",
    primary: "#111112",
    secondary: "#D4D4D4",
  },

  border: {
    default: "#CDD5E9",
  },
};

/* =========================
   Dark theme
   ========================= */

export const darkTheme = {
  mode: "dark",

  base: {
    primary: "#613DE4",
    primaryHover: "#4E31B6",
    attention: "#FACC15",
    warning: "#F59E0B",
    error: "#EF4444",
    success: "#3BB266",
    info: "#1D2939",
  },

  background: {
    bg: "#1D2939",
    surface: "#101828",
    primarySurface: "#613de430",
  },

  text: {
    onPrimary: "#FFFFFF",
    primary: "#FFFFFF",
    secondary: "#9CA3AF",
  },

  border: {
    default: "#475467",
  },
};

/* =========================
   Theme type
   ========================= */

export type Theme = typeof lightTheme;
