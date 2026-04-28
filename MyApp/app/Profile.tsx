import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "@/components/ui/Text";
import { router } from "expo-router";
import { removeToken } from "@/helpers/api/TokenStorage";
import { SafeAreaView } from "react-native-safe-area-context";
import AntDesign from "@expo/vector-icons/AntDesign";

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
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginVertical: 12,
          }}
        >
          <AntDesign
            name="stock"
            size={24}
            color="black"
            style={{ marginRight: 8 }}
          />
          <Text typography="titleLarge">Cổ phiếu của tôi</Text>
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
            size={24}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleLarge">Khẩu vị rủi ro</Text>
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
            size={24}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleLarge">Cài đặt</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={async () => {
            await removeToken();
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
            size={24}
            style={{ marginRight: 8 }}
          />
          <Text typography="titleLarge">Đăng xuất</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

export default Profile;
