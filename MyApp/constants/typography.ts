// typography.ts

import { TextStyle } from "react-native";

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
  },
  headlineMedium: {
    fontSize: 28,
    lineHeight: 36,
  },
  headlineSmall: {
    fontSize: 24,
    lineHeight: 32,
  },

  titleLarge: {
    fontSize: 20,
    lineHeight: 24,
  },
  titleMedium: {
    fontSize: 16,
    lineHeight: 20,
    letterSpacing: 0.15,
  },
  titleSmall: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
  },

  labelLarge: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
  },
  labelMedium: {
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.5,
  },
  labelSmall: {
    fontSize: 11,
    lineHeight: 16,
    letterSpacing: 0.5,
  },

  bodyLarge: {
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.5,
  },
  bodyMedium: {
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.25,
  },
  bodySmall: {
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.4,
  },
};
