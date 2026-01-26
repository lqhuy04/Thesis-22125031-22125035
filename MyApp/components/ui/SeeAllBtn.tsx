import { useLocalization } from "@/hooks/LocalizationContext";
import React from "react";
import { TouchableOpacity } from "react-native";
import { Text } from "./Text";
import { useTheme } from "@/hooks/ThemeContext";

const SeeAllBtn = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <TouchableOpacity
      style={{
        marginTop: 16,
        paddingVertical: 8,
        width: "100%",
        borderRadius: 4,
        borderWidth: 1,
        borderColor: theme.base.primary,
        alignItems: "center",
      }}
    >
      <Text typography="titleMedium" color={theme.text.primary}>
        {t("detail.newsSectionViewAll")}
      </Text>
    </TouchableOpacity>
  );
};

export default SeeAllBtn;
