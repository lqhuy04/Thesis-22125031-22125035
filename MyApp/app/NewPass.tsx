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

type FormData = {
  newPass: string;
  confirmPass: string;
};

const ResetPassword = () => {
  const { theme } = useTheme();
  const { control, handleSubmit, reset } = useForm<FormData>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const onSubmit = async (data: FormData) => {
    setError("");

    if (data.newPass.length < 6)
      return setError("Mật khẩu phải có ít nhất 6 ký tự.");
    if (data.newPass !== data.confirmPass)
      return setError("Xác nhận mật khẩu không khớp.");

    setLoading(true);
    // TODO: gọi API đặt lại mật khẩu
    await new Promise((r) => setTimeout(r, 1200));
    setLoading(false);

    // if (!res.status) return setError("Đặt lại mật khẩu thất bại, vui lòng thử lại.");

    setSuccess(true);
    reset();
  };

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title="Đặt lại mật khẩu" />

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
            <SimpleLineIcons name="lock" size={28} color={theme.base.primary} />
          </View>
          <Text typography="titleLarge" style={{ textAlign: "center" }}>
            Mật khẩu mới
          </Text>
          <Text
            typography="bodyMedium"
            style={{ opacity: 0.5, textAlign: "center", marginTop: 4 }}
          >
            Đặt mật khẩu mới cho tài khoản của bạn.
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
            name="newPass"
            label="Mật khẩu mới"
            placeholder="Nhập mật khẩu mới (ít nhất 6 ký tự)"
            required
            secure
          />
          <Input
            control={control}
            name="confirmPass"
            label="Xác nhận mật khẩu mới"
            placeholder="Nhập lại mật khẩu mới"
            required
            secure
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

        {/* Success */}
        {success && (
          <View
            style={[
              styles.banner,
              {
                backgroundColor: theme.base.success + "15",
                borderColor: theme.base.success + "40",
              },
            ]}
          >
            <SimpleLineIcons
              name="check"
              size={13}
              color={theme.base.success}
            />
            <Text
              typography="labelLarge"
              color={theme.base.success}
              style={{ flex: 1 }}
            >
              Đặt lại mật khẩu thành công!
            </Text>
          </View>
        )}

        {/* Button */}
        <TouchableOpacity
          style={[styles.button, { backgroundColor: theme.base.primary }]}
          onPress={
            success
              ? () => router.replace("/Authentication")
              : handleSubmit(onSubmit)
          }
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color={theme.text.onPrimary} />
          ) : (
            <Text typography="titleLarge" color={theme.text.onPrimary}>
              {success ? "Về trang đăng nhập" : "Xác nhận"}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default ResetPassword;

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
    gap: 4,
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
