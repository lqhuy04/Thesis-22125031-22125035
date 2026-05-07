import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "@/components/ui/Text";
import { router } from "expo-router";
import { removeSession } from "@/helpers/api/TokenStorage";
import { SafeAreaView } from "react-native-safe-area-context";
import AntDesign from "@expo/vector-icons/AntDesign";

const Profile = () => {
  const { theme } = useTheme();

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
      }}
    >
      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
        }}
      ></View>

      <View style={{ padding: 12 }}>
        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginVertical: 12,
          }}
        >
          <AntDesign
            name="stock"
            size={20}
            color="black"
            style={{ marginRight: 8 }}
          />
          <Text typography="titleMedium">Cổ phiếu của tôi</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("/RiskAppetite")}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginVertical: 12,
          }}
        >
          <Ionicons
            name="bar-chart-outline"
            size={20}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleMedium">Khẩu vị rủi ro</Text>
        </TouchableOpacity>

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
          <Text typography="titleMedium">Cài đặt</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={async () => {
            await removeSession();
            router.replace("/Authentication");
          }}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginVertical: 12,
          }}
        >
          <Ionicons
            name="log-out-outline"
            size={20}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleMedium">Đăng xuất</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

export default Profile;
