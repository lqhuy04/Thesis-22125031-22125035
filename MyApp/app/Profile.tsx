import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useState } from "react";
import { Modal, Pressable, TouchableOpacity, View } from "react-native";
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
  const [confirmLogout, setConfirmLogout] = useState(false);

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
      onPress: () => setConfirmLogout(true),
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

      <Modal
        visible={confirmLogout}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmLogout(false)}
      >
        <Pressable
          style={{
            flex: 1,
            backgroundColor: "rgba(0,0,0,0.45)",
            justifyContent: "center",
            alignItems: "center",
            padding: 24,
          }}
          onPress={() => setConfirmLogout(false)}
        >
          <Pressable
            style={{
              width: "100%",
              backgroundColor: theme.background.bg,
              borderRadius: 16,
              borderWidth: 0.5,
              borderColor: theme.border.default,
              padding: 20,
              gap: 8,
            }}
          >
            <Text typography="titleLarge">Đăng xuất</Text>
            <Text
              typography="bodyLarge"
              style={{ opacity: 0.6, marginBottom: 8 }}
            >
              Bạn có chắc muốn đăng xuất khỏi tài khoản không?
            </Text>

            <View style={{ flexDirection: "row", gap: 10 }}>
              <TouchableOpacity
                style={{
                  flex: 1,
                  paddingVertical: 12,
                  borderRadius: 12,
                  alignItems: "center",
                  borderWidth: 1,
                  borderColor: theme.border.default,
                  backgroundColor: theme.background.surface,
                }}
                onPress={() => setConfirmLogout(false)}
              >
                <Text typography="titleMedium">Huỷ</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={{
                  flex: 1,
                  paddingVertical: 12,
                  borderRadius: 12,
                  alignItems: "center",
                  backgroundColor: theme.base.error,
                }}
                onPress={async () => {
                  setConfirmLogout(false);
                  await removeSession();
                  router.replace("/Authentication");
                }}
              >
                <Text typography="titleMedium" color="#fff">
                  Đăng xuất
                </Text>
              </TouchableOpacity>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
};

export default Profile;
