import { useTheme } from "@/hooks/ThemeContext";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated,
  Modal,
  Pressable,
  Switch,
  TouchableOpacity,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "@/components/ui/Text";
import { router, useFocusEffect } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import FontAwesome6 from "@expo/vector-icons/FontAwesome6";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import {
  getProfile,
  logOut,
  UserProfile,
} from "@/helpers/AuthenticationHelper";
import { Language, useLocalization } from "@/hooks/LocalizationContext";
import { resetOnboarding } from "@/helpers/onboarding";

// ─── Skeleton ────────────────────────────────────────────────────────────────

const SkeletonBox = ({
  width,
  height,
  borderRadius = 6,
  style,
}: {
  width: number | string;
  height: number;
  borderRadius?: number;
  style?: object;
}) => {
  const { theme } = useTheme();
  const opacity = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 1, duration: 700, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.4, duration: 700, useNativeDriver: true }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={[{ width, height, borderRadius, backgroundColor: theme.border.default, opacity }, style]}
    />
  );
};

// ─── Types ───────────────────────────────────────────────────────────────────
interface MenuItemProps {
  label: string;
  icon: React.ReactNode;
  onPress: () => void;
  trailing?: React.ReactNode; // thêm prop này
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

const MenuItem = ({ label, icon, onPress, trailing }: MenuItemProps) => {
  const { theme } = useTheme();
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
        <Text color={theme.text.primary} typography="bodyLarge">
          {label}
        </Text>
      </View>

      {/* Thay chevron cứng bằng trailing slot */}
      {trailing ?? (
        <MaterialCommunityIcons
          name="chevron-right"
          size={24}
          color={theme.text.primary}
        />
      )}
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
        color={theme.text.primary}
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
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [confirmLogout, setConfirmLogout] = useState(false);

  const { toggleTheme, isDark, resetTheme } = useTheme();
  const { language, setLanguage, t } = useLocalization();
  const [showLangSheet, setShowLangSheet] = useState(false);

  useFocusEffect(
    useCallback(() => {
      getProfile()
        .then((result) => {
          if (result.status && result.data) {
            setProfile(result.data);
          }
        })
        .catch((error) => {
          console.error("Failed to fetch profile:", error);
        });
    }, []),
  );

  const managementItems: MenuItemProps[] = [
    {
      label: t("profile.riskAppetite"),
      icon: (
        <Ionicons
          name="bar-chart-outline"
          size={20}
          color={theme.base.primary}
        />
      ),
      onPress: () => router.push("/RiskAppetite"),
    },
  ];

  const systemItems: MenuItemProps[] = [
    {
      label: t("profile.darkMode"),
      icon: (
        <MaterialCommunityIcons
          name="theme-light-dark"
          size={20}
          color={theme.base.primary}
        />
      ),
      onPress: toggleTheme, // tap cả row cũng toggle được
      trailing: (
        <Switch
          trackColor={{
            false: theme.background.primarySurface,
            true: theme.background.primarySurface,
          }}
          thumbColor={isDark ? theme.base.primary : theme.text.onPrimary}
          onValueChange={toggleTheme}
          value={isDark}
          style={{ transform: [{ scale: 0.8 }] }}
        />
      ),
    },
    {
      label: t("profile.language"),
      icon: (
        <Ionicons
          name="language-outline"
          size={20}
          color={theme.base.primary}
        />
      ),
      onPress: () => setShowLangSheet(true),
      trailing: (
        // hiển thị label ngôn ngữ hiện tại + chevron
        <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
          <Text
            typography="bodyMedium"
            style={{ opacity: 0.8 }}
            color={theme.text.primary}
          >
            {language === "vi" ? "Tiếng Việt" : "English"}
          </Text>
          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color={theme.text.primary}
          />
        </View>
      ),
    },
  ];

  const accountItems: MenuItemProps[] = [
    {
      label: profile?.has_password
        ? t("profile.changePass")
        : t("profile.createPass"),
      icon: (
        <MaterialIcons name="password" size={20} color={theme.base.primary} />
      ),
      onPress: () =>
        router.push({
          pathname: "/ChangePass",
          params: {
            data: JSON.stringify({ has_password: profile?.has_password }),
          },
        }),
    },
    {
      label: t("profile.logOut"),
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
            backgroundColor: theme.background.primarySurface,
            width: 48,
            height: 48,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <FontAwesome6 name="user" size={20} color={theme.base.primary} />
        </View>

        <View style={{ flex: 1, marginLeft: 8 }}>
          {profile ? (
            <>
              <Text
                typography="titleMedium"
                color={theme.text.primary}
                style={{ marginBottom: 4 }}
              >
                {profile.email}
              </Text>
              <Text typography="bodyMedium" color={theme.text.primary}>
                {profile.user_id}
              </Text>
            </>
          ) : (
            <>
              <SkeletonBox width="75%" height={18} style={{ marginBottom: 8 }} />
              <SkeletonBox width="55%" height={14} />
            </>
          )}
        </View>
      </View>

      {/* Menu sections */}
      <MenuSection title={t("profile.management")} items={managementItems} />
      <MenuSection title={t("profile.system")} items={systemItems} />
      <MenuSection title={t("profile.account")} items={accountItems} />

      {/* Language Bottom Sheet */}
      <Modal
        visible={showLangSheet}
        transparent
        animationType="slide"
        onRequestClose={() => setShowLangSheet(false)}
      >
        <Pressable
          style={{
            flex: 1,
            backgroundColor: "rgba(0,0,0,0.45)",
            justifyContent: "flex-end",
          }}
          onPress={() => setShowLangSheet(false)}
        >
          <Pressable
            style={{
              backgroundColor: theme.background.bg,
              borderTopLeftRadius: 20,
              borderTopRightRadius: 20,
              padding: 20,
              gap: 8,
            }}
          >
            <Text
              typography="titleLarge"
              style={{ marginBottom: 8, alignSelf: "center" }}
              color={theme.text.primary}
            >
              {t("profile.language")}
            </Text>

            {[
              { value: "vi", label: "Tiếng Việt" },
              { value: "en", label: "English" },
            ].map((opt) => (
              <TouchableOpacity
                key={opt.value}
                onPress={() => {
                  setLanguage(opt.value as Language);
                  setShowLangSheet(false);
                }}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  paddingVertical: 14,
                  paddingHorizontal: 12,
                  borderRadius: 12,
                  backgroundColor:
                    language === opt.value
                      ? theme.base.primary + "18"
                      : "transparent",
                }}
              >
                <Text typography="bodyLarge" color={theme.text.primary}>
                  {opt.label}
                </Text>
                {language === opt.value && (
                  <MaterialIcons
                    name="check"
                    size={20}
                    color={theme.base.primary}
                  />
                )}
              </TouchableOpacity>
            ))}

            {/* Safe area bottom padding */}
            <View style={{ height: 16 }} />
          </Pressable>
        </Pressable>
      </Modal>

      {/* Logout Modal */}

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
            <Text typography="titleLarge" color={theme.text.primary}>
              {t("profile.logOut")}
            </Text>
            <Text
              typography="bodyLarge"
              style={{ opacity: 0.6, marginBottom: 8 }}
              color={theme.text.primary}
            >
              {t("profile.logoutConfirm")}
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
                <Text typography="titleMedium" color={theme.text.primary}>
                  {t("profile.cancel")}
                </Text>
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
                  await logOut();
                  // Đưa Onboarding, theme, lang về mặc định
                  await resetOnboarding();
                  await resetTheme();
                  await setLanguage("vi");
                  setConfirmLogout(false);
                  router.replace("/Authentication");
                }}
              >
                <Text typography="titleMedium" color={theme.text.onPrimary}>
                  {t("profile.logOut")}
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
