// Text.tsx

import React from "react";
import {
  Text as RNText,
  TextProps as RNTextProps,
  TextStyle,
} from "react-native";
import { typography, TypographyVariant } from "../../constants/typography";

type Props = RNTextProps & {
  typography?: TypographyVariant;
  color?: string;
  style?: TextStyle;
};

export const Text: React.FC<Props> = ({
  typography: variant = "bodyMedium",
  color,
  style,
  children,
  ...rest
}) => {
  return (
    <RNText
      {...rest}
      style={[typography[variant], color ? { color } : null, style]}
    >
      {children}
    </RNText>
  );
};
