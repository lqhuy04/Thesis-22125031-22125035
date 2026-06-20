// typography.ts

import { TextStyle } from "react-native";
import { fontFamily } from "./fonts";

export type TypographyVariant =
  | "headlineLarge"
  | "headlineMedium"
  | "headlineSmall"
  | "titleLarge"
  | "titleMedium"
  | "titleSmall"
  | "labelLarge"
  | "labelMedium"
  | "labelSmall"
  | "bodyLarge"
  | "bodyMedium"
  | "bodySmall";

export const typography: Record<TypographyVariant, TextStyle> = {
  headlineLarge: {
    fontSize: 32,
    lineHeight: 40,
    fontFamily: fontFamily.semiBold,
    fontWeight: "600",
  },
  headlineMedium: {
    fontSize: 28,
    lineHeight: 36,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },
  headlineSmall: {
    fontSize: 24,
    lineHeight: 32,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },
  titleLarge: {
    fontSize: 20,
    lineHeight: 24,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },
  titleMedium: {
    fontSize: 16,
    lineHeight: 20,
    letterSpacing: 0.15,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },
  titleSmall: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },
  labelLarge: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },
  labelMedium: {
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.5,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },
  labelSmall: {
    fontSize: 11,
    lineHeight: 16,
    letterSpacing: 0.5,
    fontFamily: fontFamily.medium,
    fontWeight: "500",
  },

  bodyLarge: {
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.5,
    fontFamily: fontFamily.regular,
    fontWeight: "400",
  },
  bodyMedium: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.25,
    fontFamily: fontFamily.regular,
    fontWeight: "400",
  },
  bodySmall: {
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.4,
    fontFamily: fontFamily.regular,
    fontWeight: "400",
  },
};
