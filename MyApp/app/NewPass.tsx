import React, { useState } from "react";
import {
  ActivityIndicator,
  Modal,
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
import { router, useLocalSearchParams } from "expo-router";
import { resetForgetPassword } from "@/helpers/AuthenticationHelper";

type FormData = {
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

const ResetPassword = () => {
  const { reset_password_token = "" } = useLocalSearchParams<{
    reset_password_token: string;
  }>();

  const { theme } = useTheme();
  const { control, handleSubmit, watch, reset } = useForm<FormData>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successModal, setSuccessModal] = useState(false);
  const [newPassError, setNewPassError] = useState<string | undefined>();
  const [confirmPassError, setConfirmPassError] = useState<
    string | undefined
  >();

  const newPass = watch("newPass");
  const confirmPass = watch("confirmPass");

  const isFormValid =
    !!newPass &&
    !!confirmPass &&
    !validatePassword(newPass) &&
    newPass === confirmPass;

  const handleNewPassChange = (value: string) => {
    setNewPassError(validatePassword(value));
    if (confirmPass) {
      setConfirmPassError(
        value !== confirmPass ? "Xác nhận mật khẩu không khớp." : undefined,
      );
    }
  };

  const handleConfirmPassChange = (value: string) => {
    setConfirmPassError(
      value !== newPass ? "Xác nhận mật khẩu không khớp." : undefined,
    );
  };

  const onSubmit = async (data: FormData) => {
    const passErr = validatePassword(data.newPass);
    const confirmErr =
      data.newPass !== data.confirmPass
        ? "Xác nhận mật khẩu không khớp."
        : undefined;

    setNewPassError(passErr);
    setConfirmPassError(confirmErr);

    if (passErr || confirmErr) return;

    setError("");
    setLoading(true);

    const response = await resetForgetPassword({
      reset_password_token,
      new_password: data.newPass,
      confirm_new_password: data.confirmPass,
    });

    setLoading(false);

    if (!response.status)
      return setError("Đặt lại mật khẩu thất bại, vui lòng thử lại.");

    reset();
    setSuccessModal(true);
  };

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title="Đặt lại mật khẩu" />

      {/* Loading Modal */}
      <Modal
        visible={loading}
        transparent
        animationType="fade"
        statusBarTranslucent
      >
        <View style={styles.overlay}>
          <ActivityIndicator size="large" color={theme.base.primary} />
        </View>
      </Modal>

      {/* Success Modal */}
      <Modal
        visible={successModal}
        transparent
        animationType="fade"
        statusBarTranslucent
      >
        <View style={styles.overlay}>
          <View
            style={[styles.modalCard, { backgroundColor: theme.background.bg }]}
          >
            <Text typography="titleLarge" style={{ textAlign: "center" }}>
              🎉 Đổi mật khẩu thành công
            </Text>
            <Text
              typography="bodyMedium"
              style={{ opacity: 0.6, textAlign: "center", marginTop: 8 }}
            >
              Vui lòng đăng nhập lại để tiếp tục.
            </Text>
            <TouchableOpacity
              style={[
                styles.modalButton,
                { backgroundColor: theme.base.primary },
              ]}
              onPress={() => {
                setSuccessModal(false);
                router.dismissAll();
              }}
              activeOpacity={0.8}
            >
              <Text typography="titleMedium" color={theme.text.onPrimary}>
                Đồng ý
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

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
            placeholder="Nhập mật khẩu mới"
            required
            secure
            errorMessage={newPassError}
            onChangeText={handleNewPassChange}
          />
          <Input
            control={control}
            name="confirmPass"
            label="Xác nhận mật khẩu mới"
            placeholder="Nhập lại mật khẩu mới"
            required
            secure
            errorMessage={confirmPassError}
            onChangeText={handleConfirmPassChange}
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
          <Text typography="titleLarge" color={theme.text.onPrimary}>
            Xác nhận
          </Text>
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
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  modalCard: {
    width: "100%",
    borderRadius: 20,
    padding: 24,
    alignItems: "center",
    gap: 4,
  },
  modalButton: {
    marginTop: 16,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 40,
    alignItems: "center",
  },
});
