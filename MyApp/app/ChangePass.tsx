import React, { useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { Input } from "@/components/ui/Input";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";

type FormData = {
  currentPass: string;
  confirmPass: string;
  newPass: string;
};

const ChangePass = () => {
  const { theme } = useTheme();
  const { control, handleSubmit, getValues, reset } = useForm<FormData>();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const onSubmit = async (data: FormData) => {
    setError("");
    setSuccess(false);

    if (data.currentPass !== data.confirmPass) {
      return setError("Xác nhận mật khẩu hiện tại không khớp.");
    }
    if (data.newPass.length < 6) {
      return setError("Mật khẩu mới phải có ít nhất 6 ký tự.");
    }
    if (data.newPass === data.currentPass) {
      return setError("Mật khẩu mới phải khác mật khẩu hiện tại.");
    }

    setLoading(true);
    // TODO: gọi API đổi mật khẩu
    // const res = await changePassword({ current_password: data.currentPass, new_password: data.newPass });
    await new Promise((r) => setTimeout(r, 1200));
    const res = { status: true };
    setLoading(false);

    if (res.status) {
      setSuccess(true);
      reset();
    } else {
      setError(
        "Đổi mật khẩu thất bại. Vui lòng kiểm tra lại mật khẩu hiện tại.",
      );
    }
  };

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title="Đổi mật khẩu" />

      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
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
            name="currentPass"
            label="Mật khẩu hiện tại"
            placeholder="Nhập mật khẩu hiện tại"
            secure
            required
          />
          <Input
            control={control}
            name="confirmPass"
            label="Xác nhận mật khẩu hiện tại"
            placeholder="Nhập lại mật khẩu hiện tại"
            secure
            required
          />

          <View
            style={[styles.divider, { backgroundColor: theme.border.default }]}
          />

          <Input
            control={control}
            name="newPass"
            label="Mật khẩu mới"
            placeholder="Nhập mật khẩu mới (ít nhất 6 ký tự)"
            secure
            required
          />
        </View>

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
              Đổi mật khẩu thành công!
            </Text>
          </View>
        )}

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
              Xác nhận
            </Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

export default ChangePass;

const styles = StyleSheet.create({
  safe: { flex: 1 },
  scroll: { padding: 16, gap: 12 },
  card: { borderRadius: 14, borderWidth: 0.5, padding: 16, gap: 12 },
  divider: { height: 0.5, opacity: 0.6 },
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
