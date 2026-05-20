import React, { useState } from "react";
import {
  ActivityIndicator,
  Modal,
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
import { useLocalSearchParams, useRouter } from "expo-router";
import { resetPassword, logOut } from "@/helpers/AuthenticationHelper";
import { useLocalization } from "@/hooks/LocalizationContext";

type FormData = {
  currentPass: string;
  newPass: string;
  confirmPass: string;
};

const validatePassword = (value: string, t: (k: string) => string) => {
  if (!value) return undefined;
  if (value.length < 8) return t("changePass.validateMinLength");
  if (!/[0-9]/.test(value)) return t("changePass.validateNumber");
  if (!/[a-z]/.test(value)) return t("changePass.validateLower");
  if (!/[A-Z]/.test(value)) return t("changePass.validateUpper");
  if (!/[^a-zA-Z0-9]/.test(value)) return t("changePass.validateSpecial");
  return undefined;
};

const ChangePass = () => {
  const { data } = useLocalSearchParams() || {};
  const { has_password } = data ? (JSON.parse(data as string) as any) : {};

  const { theme } = useTheme();
  const { t } = useLocalization();
  const router = useRouter();
  const { control, handleSubmit, reset, watch } = useForm<FormData>();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSuccessModal, setShowSuccessModal] = useState(false);

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
    !validatePassword(newPass, t) &&
    newPass === confirmPass;

  const handleNewPassChange = (value: string) => {
    setNewPassError(validatePassword(value, t));
    if (confirmPass) {
      setConfirmPassError(
        value !== confirmPass ? t("changePass.errorMismatch") : undefined,
      );
    }
  };

  const handleConfirmPassChange = (value: string) => {
    setConfirmPassError(
      value !== newPass ? t("changePass.errorMismatch") : undefined,
    );
  };

  const onSubmit = async (data: FormData) => {
    const newPassErr = validatePassword(data.newPass, t);
    const confirmErr =
      data.newPass !== data.confirmPass
        ? t("changePass.errorMismatch")
        : undefined;

    setNewPassError(newPassErr);
    setConfirmPassError(confirmErr);

    if (newPassErr || confirmErr) return;

    setError("");

    if (has_password && data.newPass === data.currentPass) {
      return setError(t("changePass.errorSamePass"));
    }

    setLoading(true);
    const res = await resetPassword({
      old_password: has_password ? data.currentPass : undefined,
      new_password: data.newPass,
      confirm_new_password: data.confirmPass,
    });
    setLoading(false);

    if (res.status) {
      reset();
      setNewPassError(undefined);
      setConfirmPassError(undefined);
      setShowSuccessModal(true);
    } else {
      setError(t("changePass.errorFailed"));
    }
  };

  const handleSuccessConfirm = async () => {
    setShowSuccessModal(false);
    await logOut();
    router.replace("/Authentication");
  };

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader
        title={t(
          has_password ? "changePass.titleChange" : "changePass.titleSet",
        )}
      />

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
                label={t("changePass.currentPass")}
                placeholder={t("changePass.currentPassPlaceholder")}
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
            label={t("changePass.newPass")}
            placeholder={t("changePass.newPassPlaceholder")}
            secure
            required
            errorMessage={newPassError}
            onChangeText={handleNewPassChange}
          />

          <Input
            control={control}
            name="confirmPass"
            label={t("changePass.confirmPass")}
            placeholder={t("changePass.confirmPassPlaceholder")}
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
              {t("changePass.confirm")}
            </Text>
          )}
        </TouchableOpacity>
      </ScrollView>

      {/* Success Modal */}
      <Modal
        visible={showSuccessModal}
        transparent
        animationType="fade"
        statusBarTranslucent
      >
        <View style={styles.modalOverlay}>
          <View
            style={[
              styles.modalCard,
              {
                backgroundColor: theme.background.bg,
                borderColor: theme.border.default,
              },
            ]}
          >
            {/* Icon */}
            <View
              style={[
                styles.iconCircle,
                { backgroundColor: theme.base.success + "20" },
              ]}
            >
              <SimpleLineIcons
                name="check"
                size={28}
                color={theme.base.success}
              />
            </View>

            {/* Title */}
            <Text
              typography="titleLarge"
              color={theme.text.primary}
              style={{ textAlign: "center" }}
            >
              {t(
                has_password
                  ? "changePass.successChange"
                  : "changePass.successSet",
              )}
            </Text>

            {/* Body */}
            <Text
              typography="bodyMedium"
              color={theme.text.secondary}
              style={{ textAlign: "center" }}
            >
              {t("changePass.successLogoutNotice")}
            </Text>

            {/* CTA */}
            <TouchableOpacity
              style={[
                styles.modalButton,
                { backgroundColor: theme.base.primary },
              ]}
              onPress={handleSuccessConfirm}
              activeOpacity={0.8}
            >
              <Text typography="titleLarge" color={theme.text.onPrimary}>
                {t("changePass.successConfirmBtn")}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  modalCard: {
    width: "100%",
    borderRadius: 20,
    borderWidth: 0.5,
    padding: 24,
    alignItems: "center",
    gap: 16,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 4,
  },
  modalButton: {
    width: "100%",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 4,
  },
});
