import React from "react";
import { TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "./Text";
import { router } from "expo-router";

interface Props {
  title: string;
  onPressBack?: () => void;
}

const ScreenHeader = ({ title, onPressBack }: Props) => {
  return (
    <View
      style={{ flexDirection: "row", alignItems: "center", marginVertical: 12 }}
    >
      <TouchableOpacity
        onPress={() => (onPressBack != null ? onPressBack : router.dismiss())}
      >
        <Ionicons name="arrow-back" size={24} style={{ marginRight: 16 }} />
      </TouchableOpacity>

      <Text typography="titleMedium">{title}</Text>
    </View>
  );
};

export default ScreenHeader;
