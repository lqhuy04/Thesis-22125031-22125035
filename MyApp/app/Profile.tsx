import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useState } from "react";
import { TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "@/components/ui/Text";
import { router } from "expo-router";
import { getSession, removeSession, Session } from "@/helpers/api/TokenStorage";
import { SafeAreaView } from "react-native-safe-area-context";
import AntDesign from "@expo/vector-icons/AntDesign";
import FontAwesome6 from "@expo/vector-icons/FontAwesome6";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";

// ─── Types ───────────────────────────────────────────────────────────────────
interface MenuItemProps {
  label: string;
  icon: React.ReactNode;
  onPress: () => void;
}

interface MenuSectionProps {
  title: string;
  items: MenuItemProps[];
}

// ─── Sub-components ──────────────────────────────────────────────────────────

const Divider = ({ borderColor }: { borderColor: string }) => (
  <View
    style={{
      height: 1,
      backgroundColor: borderColor + "80",
      marginVertical: 12,
    }}
  />
);

const MenuItem = ({ label, icon, onPress }: MenuItemProps) => {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={{ flexDirection: "row", alignItems: "center" }}
    >
      <View
        style={{
          width: 30,
          marginRight: 8,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {icon}
      </View>

      <View style={{ flex: 1 }}>
        <Text typography="bodyLarge">{label}</Text>
      </View>

      <MaterialCommunityIcons name="chevron-right" size={24} color="black" />
    </TouchableOpacity>
  );
};

const MenuSection = ({ title, items }: MenuSectionProps) => {
  const { theme } = useTheme();

  return (
    <>
      <Text
        typography="titleMedium"
        style={{ marginHorizontal: 12, marginTop: 24, marginBottom: 8 }}
      >
        {title}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginHorizontal: 12,
        }}
      >
        {items.map((item, index) => (
          <React.Fragment key={item.label}>
            {index > 0 && <Divider borderColor={theme.border.default} />}
            <MenuItem {...item} />
          </React.Fragment>
        ))}
      </View>
    </>
  );
};

// ─── Main Screen ─────────────────────────────────────────────────────────────

const Profile = () => {
  const { theme } = useTheme();
  const [profile, setProfile] = useState<Session | null>(null);

  useEffect(() => {
    getSession().then(setProfile);
  }, []);

  const managementItems: MenuItemProps[] = [
    {
      label: "Quản lý tài sản",
      icon: (
        <MaterialIcons
          name="attach-money"
          size={20}
          color={theme.base.primary}
        />
      ),
      onPress: () => router.push("/WatchListStock"),
    },
    {
      label: "Khẩu vị rủi ro",
      icon: (
        <Ionicons
          name="bar-chart-outline"
          size={20}
          color={theme.base.primary}
        />
      ),
      onPress: () => router.push("/RiskAppetite"),
    },
    {
      label: "Danh sách theo dõi",
      icon: <AntDesign name="stock" size={20} color={theme.base.primary} />,
      onPress: () => router.push("/Favorite"),
    },
  ];

  const systemItems: MenuItemProps[] = [
    {
      label: "Chế độ tối",
      icon: (
        <MaterialCommunityIcons
          name="theme-light-dark"
          size={20}
          color={theme.base.primary}
        />
      ),
      onPress: () => router.push("/WatchListStock"),
    },
    {
      label: "Ngôn ngữ",
      icon: (
        <Ionicons
          name="language-outline"
          size={20}
          color={theme.base.primary}
        />
      ),
      onPress: () => router.push("/WatchListStock"),
    },
  ];

  const accountItems: MenuItemProps[] = [
    {
      label: "Đổi mật khẩu",
      icon: (
        <MaterialIcons name="password" size={20} color={theme.base.primary} />
      ),
      onPress: () => router.push("/WatchListStock"),
    },
    {
      label: "Đăng xuất",
      icon: (
        <MaterialIcons name="logout" size={20} color={theme.base.primary} />
      ),
      onPress: async () => {
        await removeSession();
        router.replace("/Authentication");
      },
    },
  ];

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: theme.background.surface }}
    >
      {/* Profile card */}
      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginHorizontal: 12,
          marginTop: 12,
          flexDirection: "row",
          alignItems: "center",
        }}
      >
        <View
          style={{
            backgroundColor: theme.base.primary + "12",
            width: 48,
            height: 48,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <FontAwesome6
            name="user"
            size={20}
            color={theme.base.primary + "80"}
          />
        </View>

        <View style={{ flex: 1, marginLeft: 8 }}>
          <Text typography="titleMedium">{profile?.email}</Text>
          <Text typography="bodyLarge">{profile?.user_id}</Text>
        </View>
      </View>

      {/* Menu sections */}
      <MenuSection title="Quản lý" items={managementItems} />
      <MenuSection title="Hệ thống" items={systemItems} />
      <MenuSection title="Tài khoản" items={accountItems} />
    </SafeAreaView>
  );
};

export default Profile;
