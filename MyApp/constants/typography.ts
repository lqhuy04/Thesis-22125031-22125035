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
  },
  headlineMedium: {
    fontSize: 28,
    lineHeight: 36,
    fontFamily: fontFamily.medium,
  },
  headlineSmall: {
    fontSize: 24,
    lineHeight: 32,
    fontFamily: fontFamily.medium,
  },
  titleLarge: {
    fontSize: 20,
    lineHeight: 24,
    fontFamily: fontFamily.medium,
  },
  titleMedium: {
    fontSize: 16,
    lineHeight: 20,
    letterSpacing: 0.15,
    fontFamily: fontFamily.medium,
  },
  titleSmall: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
    fontFamily: fontFamily.medium,
  },
  labelLarge: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
    fontFamily: fontFamily.medium,
  },
  labelMedium: {
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.5,
    fontFamily: fontFamily.medium,
  },
  labelSmall: {
    fontSize: 11,
    lineHeight: 16,
    letterSpacing: 0.5,
    fontFamily: fontFamily.medium,
  },

  bodyLarge: {
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.5,
    fontFamily: fontFamily.regular,
  },
  bodyMedium: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.25,
    fontFamily: fontFamily.regular,
  },
  bodySmall: {
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.4,
    fontFamily: fontFamily.regular,
  },
};
