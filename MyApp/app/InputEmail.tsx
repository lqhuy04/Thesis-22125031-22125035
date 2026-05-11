import React, { useState } from "react";
import {
  ActivityIndicator,
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Input } from "@/components/ui/Input";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import { router } from "expo-router";

const ForgotPasswordEmail = () => {
  const { theme } = useTheme();
  const { control, handleSubmit } = useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (data: any) => {
    if (!data.email) return setError("Vui lòng nhập email.");

    setError("");
    setLoading(true);
    // TODO: gọi API gửi OTP về email
    await new Promise((r) => setTimeout(r, 1200));
    setLoading(false);

    // if (!res.status) return setError("Email không tồn tại trong hệ thống.");
    router.push("/OTP"); // chuyển sang trang OTP
  };

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title="Quên mật khẩu" />

      <View style={styles.content}>
        {/* Icon + mô tả */}
        <View style={styles.header}>
          <View
            style={[
              styles.iconWrap,
              {
                backgroundColor: theme.base.primary + "12",
                borderColor: theme.base.primary + "30",
              },
            ]}
          >
            <SimpleLineIcons
              name="envelope"
              size={28}
              color={theme.base.primary}
            />
          </View>
          <Text typography="titleLarge" style={{ textAlign: "center" }}>
            Xác nhận email
          </Text>
          <Text
            typography="bodyMedium"
            style={{ opacity: 0.5, textAlign: "center", marginTop: 4 }}
          >
            Nhập email đã đăng ký, chúng tôi sẽ gửi mã OTP để đặt lại mật khẩu.
          </Text>
        </View>

        {/* Card */}
        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.background.bg,
              borderColor: theme.border.default,
            },
          ]}
        >
          <Input
            control={control}
            name="email"
            label="Email"
            placeholder="username@gmail.com"
            required
          />
        </View>

        {/* Error */}
        {!!error && (
          <View
            style={[
              styles.banner,
              {
                backgroundColor: theme.base.error + "15",
                borderColor: theme.base.error + "40",
              },
            ]}
          >
            <SimpleLineIcons
              name="exclamation"
              size={13}
              color={theme.base.error}
            />
            <Text
              typography="labelLarge"
              color={theme.base.error}
              style={{ flex: 1 }}
            >
              {error}
            </Text>
          </View>
        )}

        {/* Button */}
        <TouchableOpacity
          style={[styles.button, { backgroundColor: theme.base.primary }]}
          onPress={handleSubmit(onSubmit)}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color={theme.text.onPrimary} />
          ) : (
            <Text typography="titleLarge" color={theme.text.onPrimary}>
              Gửi mã xác thực
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default ForgotPasswordEmail;

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { flex: 1, paddingHorizontal: 24, paddingTop: 32, gap: 16 },
  header: { alignItems: "center", gap: 8 },
  iconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  card: {
    borderRadius: 16,
    borderWidth: 0.5,
    padding: 16,
  },
  banner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
  },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 4,
  },
});
