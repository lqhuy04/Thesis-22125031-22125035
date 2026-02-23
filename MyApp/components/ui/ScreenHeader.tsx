import React from "react";
import { TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "./Text";
import { router } from "expo-router";

interface Props {
  title: string;
  hiddenBack?: boolean;
  onPressBack?: () => void;
}

const ScreenHeader = ({hiddenBack = false, title, onPressBack }: Props) => {
  return (
    <View
      style={{ flexDirection: "row", alignItems: "center", marginVertical: 12 }}
    >
      {hiddenBack ? null : <TouchableOpacity
        onPress={() => (onPressBack != null ? onPressBack() : router.dismiss())}
      >
        <Ionicons name="arrow-back" size={24} style={{ marginRight: 16 }} />
      </TouchableOpacity>}

      <Text typography="titleLarge">{title}</Text>
    </View>
  );
};

export default ScreenHeader;
