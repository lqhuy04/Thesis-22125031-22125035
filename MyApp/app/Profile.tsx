import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "@/components/ui/Text";
import { router } from "expo-router";

const Profile = () => {
  const { theme } = useTheme();

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.bg,
      }}
    >
      <View style={{ padding: 12 }}>
        <TouchableOpacity
          onPress={() => router.push("/Setting")}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginVertical: 12,
          }}
        >
          <Ionicons
            name="settings-outline"
            size={20}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleSmall">Cài đặt</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/RiskProfile")}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginVertical: 12,
          }}
        >
          <Ionicons
            name="settings-outline"
            size={20}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleSmall">Khẩu vị rủi ro</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

export default Profile;
