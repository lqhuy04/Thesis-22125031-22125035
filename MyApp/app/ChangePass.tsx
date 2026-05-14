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
import { useLocalSearchParams } from "expo-router";
import { resetPassword } from "@/helpers/AuthenticationHelper";

type FormData = {
  currentPass: string;
  newPass: string;
  confirmPass: string;
};

const validatePassword = (value: string): string | undefined => {
  if (!value) return undefined;
  if (value.length < 8) return "Mật khẩu phải có ít nhất 8 ký tự.";
  if (!/[0-9]/.test(value)) return "Mật khẩu phải chứa ít nhất 1 chữ số.";
  if (!/[a-z]/.test(value)) return "Mật khẩu phải chứa ít nhất 1 chữ thường.";
  if (!/[A-Z]/.test(value)) return "Mật khẩu phải chứa ít nhất 1 chữ in hoa.";
  if (!/[^a-zA-Z0-9]/.test(value))
    return "Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt.";
  return undefined;
};

const ChangePass = () => {
  const { data } = useLocalSearchParams() || {};
  const { has_password } = data ? (JSON.parse(data as string) as any) : {};

  const { theme } = useTheme();
  const { control, handleSubmit, reset, watch } = useForm<FormData>();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const [newPassError, setNewPassError] = useState<string | undefined>();
  const [confirmPassError, setConfirmPassError] = useState<
    string | undefined
  >();

  const newPass = watch("newPass");
  const confirmPass = watch("confirmPass");

  const isFormValid =
    (!has_password || !!watch("currentPass")) &&
    !!newPass &&
    !!confirmPass &&
    !validatePassword(newPass) &&
    newPass === confirmPass;

  const handleNewPassChange = (value: string) => {
    setNewPassError(validatePassword(value));
    if (confirmPass) {
      setConfirmPassError(
        value !== confirmPass ? "Mật khẩu xác nhận không khớp." : undefined,
      );
    }
  };

  const handleConfirmPassChange = (value: string) => {
    setConfirmPassError(
      value !== newPass ? "Mật khẩu xác nhận không khớp." : undefined,
    );
  };

  const onSubmit = async (data: FormData) => {
    const newPassErr = validatePassword(data.newPass);
    const confirmErr =
      data.newPass !== data.confirmPass
        ? "Mật khẩu xác nhận không khớp."
        : undefined;

    setNewPassError(newPassErr);
    setConfirmPassError(confirmErr);

    if (newPassErr || confirmErr) return;

    setError("");
    setSuccess(false);

    if (has_password && data.newPass === data.currentPass) {
      return setError("Mật khẩu mới phải khác mật khẩu hiện tại.");
    }

    setLoading(true);
    const res = await resetPassword({
      old_password: has_password ? data.currentPass : undefined,
      new_password: data.newPass,
      confirm_new_password: data.confirmPass,
    });
    setLoading(false);

    if (res.status) {
      setSuccess(true);
      reset();
      setNewPassError(undefined);
      setConfirmPassError(undefined);
    } else {
      setError(
        "Đổi mật khẩu thất bại. Vui lòng kiểm tra lại mật khẩu hiện tại.",
      );
    }
  };

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title={has_password ? "Đổi mật khẩu" : "Đặt mật khẩu"} />

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
          {has_password ? (
            <>
              <Input
                control={control}
                name="currentPass"
                label="Mật khẩu hiện tại"
                placeholder="Nhập mật khẩu hiện tại"
                secure
                required
              />

              <View
                style={[
                  styles.divider,
                  { backgroundColor: theme.border.default },
                ]}
              />
            </>
          ) : null}

          <Input
            control={control}
            name="newPass"
            label="Mật khẩu mới"
            placeholder="Nhập mật khẩu mới"
            secure
            required
            errorMessage={newPassError}
            onChangeText={handleNewPassChange}
          />

          <Input
            control={control}
            name="confirmPass"
            label="Xác nhận mật khẩu mới"
            placeholder="Nhập lại mật khẩu mới để xác nhận"
            secure
            required
            errorMessage={confirmPassError}
            onChangeText={handleConfirmPassChange}
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
              {has_password ? "Đổi" : "Đặt"} mật khẩu thành công!
            </Text>
          </View>
        )}

        <TouchableOpacity
          style={[
            styles.button,
            {
              backgroundColor: isFormValid
                ? theme.base.primary
                : theme.border.default,
            },
          ]}
          onPress={handleSubmit(onSubmit)}
          disabled={loading || !isFormValid}
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
