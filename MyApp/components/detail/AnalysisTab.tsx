import React from "react";
import { View, TouchableOpacity } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";

interface AnalysisTabProps {
  tab: "fun" | "tech" | "ovr";
  setTab: (tab: "fun" | "tech" | "ovr") => void;
}

const AnalysisTab = ({ tab, setTab }: AnalysisTabProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <View
      style={{
        marginBottom: 24,
        backgroundColor: theme.background.surface,
        padding: 4,
        borderRadius: 4,
        alignItems: "center",
        flexDirection: "row",
      }}
    >
      <TouchableOpacity
        onPress={() => setTab("fun")}
        style={{
          flex: 1,
          justifyContent: "center",
          paddingVertical: 8,
          borderTopLeftRadius: 4,
          borderBottomLeftRadius: 4,
          backgroundColor: tab === "fun" ? theme.base.primary : undefined,
          borderWidth: 1,
          borderColor:
            tab === "fun" ? theme.base.primary : theme.border.default,
        }}
      >
        <Text
          typography="titleMedium"
          color={tab === "fun" ? theme.text.onPrimary : theme.text.primary}
          style={{ textAlign: "center" }}
        >
          PTCB
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        onPress={() => setTab("tech")}
        style={{
          flex: 1,
          justifyContent: "center",
          paddingVertical: 8,
          borderTopRightRadius: 4,
          borderBottomRightRadius: 4,
          backgroundColor: tab === "tech" ? theme.base.primary : undefined,
          borderWidth: 1,
          borderColor:
            tab === "tech" ? theme.base.primary : theme.border.default,
        }}
      >
        <Text
          typography="titleMedium"
          color={tab === "tech" ? theme.text.onPrimary : theme.text.primary}
          style={{ textAlign: "center" }}
        >
          PTKT
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        onPress={() => setTab("ovr")}
        style={{
          flex: 1,
          justifyContent: "center",
          paddingVertical: 8,
          borderTopRightRadius: 4,
          borderBottomRightRadius: 4,
          backgroundColor: tab === "ovr" ? theme.base.primary : undefined,
          borderWidth: 1,
          borderColor:
            tab === "ovr" ? theme.base.primary : theme.border.default,
        }}
      >
        <Text
          typography="titleMedium"
          color={tab === "ovr" ? theme.text.onPrimary : theme.text.primary}
          style={{ textAlign: "center" }}
        >
          Summary
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default AnalysisTab;
