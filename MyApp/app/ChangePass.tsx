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
    setSuccess(false);

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
      setSuccess(true);
      reset();
      setNewPassError(undefined);
      setConfirmPassError(undefined);
    } else {
      setError(t("changePass.errorFailed"));
    }
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
              {t(
                has_password
                  ? "changePass.successChange"
                  : "changePass.successSet",
              )}
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
