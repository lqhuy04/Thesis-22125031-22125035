import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { router, useLocalSearchParams } from "expo-router";
import {
  verifyRegisterEmail,
  resendVerificationEmail,
  resendOTPForgetPass,
  verifyOTPForgetPass,
} from "@/helpers/AuthenticationHelper";

const OTP_LENGTH = 6;
const RESEND_COUNTDOWN = 60;

const OTPScreen = () => {
  const { email = "", flow = "signUp" } = useLocalSearchParams<{
    email: string;
    flow: string;
  }>();

  const { theme } = useTheme();
  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(""));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successModal, setSuccessModal] = useState(false);
  const [countdown, setCountdown] = useState(RESEND_COUNTDOWN);
  const inputs = useRef<(TextInput | null)[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startCountdown = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    setCountdown(RESEND_COUNTDOWN);
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, []);

  useEffect(() => {
    startCountdown();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [startCountdown]);

  const handleChange = (text: string, index: number) => {
    const digit = text.replace(/[^0-9]/g, "").slice(-1);
    const next = [...otp];
    next[index] = digit;
    setOtp(next);
    setError("");

    if (digit && index < OTP_LENGTH - 1) {
      inputs.current[index + 1]?.focus();
    }
  };

  const handleKeyPress = (key: string, index: number) => {
    if (key === "Backspace" && !otp[index] && index > 0) {
      const next = [...otp];
      next[index - 1] = "";
      setOtp(next);
      inputs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async () => {
    const code = otp.join("");
    if (code.length < OTP_LENGTH) return setError("Vui lòng nhập đủ 6 chữ số.");

    setError("");
    setLoading(true);

    const response =
      flow === "signUp"
        ? await verifyRegisterEmail({ email, otp: code })
        : await verifyOTPForgetPass({ email, otp: code });

    setLoading(false);

    if (response.status) {
      if (flow === "signUp") {
        setSuccessModal(true);
      } else {
        router.push({
          pathname: "/NewPass",
          params: { reset_password_token: response?.data },
        });
      }
    } else {
      setError("Mã OTP không đúng. Vui lòng thử lại.");
    }
  };

  const handleResend = () => {
    if (countdown > 0) return;
    setOtp(Array(OTP_LENGTH).fill(""));
    setError("");
    inputs.current[0]?.focus();
    startCountdown();

    if (flow === "signUp") {
      resendVerificationEmail({ email });
    } else {
      resendOTPForgetPass({ email });
    }
  };

  const filled = otp.every((d) => d !== "");
  const canResend = countdown === 0;

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title="Xác thực OTP" />

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
              🎉 Xác thực thành công
            </Text>
            <Text
              typography="bodyMedium"
              style={{ opacity: 0.6, textAlign: "center", marginTop: 8 }}
            >
              Vui lòng đăng nhập để tiếp tục.
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
        {/* Description */}
        <View style={styles.header}>
          <Text typography="titleLarge">Nhập mã xác thực</Text>
          <Text
            typography="bodyMedium"
            style={{ opacity: 0.5, textAlign: "center", marginTop: 6 }}
          >
            Mã OTP gồm 6 chữ số đã được gửi đến email của bạn
          </Text>
        </View>

        {/* OTP inputs */}
        <View style={styles.otpRow}>
          {otp.map((digit, index) => {
            const isFilled = digit !== "";
            return (
              <TextInput
                key={index}
                ref={(r) => {
                  inputs.current[index] = r;
                }}
                style={[
                  styles.otpBox,
                  {
                    borderColor: isFilled
                      ? theme.base.primary
                      : error
                        ? theme.base.error
                        : theme.border.default,
                    backgroundColor: theme.background.bg,
                    color: theme.text.primary,
                  },
                ]}
                value={digit}
                onChangeText={(t) => handleChange(t, index)}
                onKeyPress={({ nativeEvent }) =>
                  handleKeyPress(nativeEvent.key, index)
                }
                keyboardType="number-pad"
                maxLength={1}
                textAlign="center"
                selectTextOnFocus
              />
            );
          })}
        </View>

        {/* Error */}
        {!!error && (
          <Text
            typography="labelLarge"
            color={theme.base.error}
            style={{ textAlign: "center" }}
          >
            {error}
          </Text>
        )}

        {/* Resend */}
        <View style={styles.resendRow}>
          <Text typography="bodyMedium" style={{ opacity: 0.5 }}>
            Không nhận được mã?{" "}
          </Text>
          <TouchableOpacity onPress={handleResend} disabled={!canResend}>
            <Text
              typography="titleMedium"
              color={canResend ? theme.base.primary : theme.text.secondary}
            >
              {canResend ? "Gửi lại" : `Gửi lại (${countdown}s)`}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Verify button */}
        <TouchableOpacity
          style={[
            styles.button,
            {
              backgroundColor: filled
                ? theme.base.primary
                : theme.border.default,
            },
          ]}
          onPress={handleVerify}
          disabled={loading || !filled}
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
      </View>
    </View>
  );
};

export default OTPScreen;

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 32,
    gap: 24,
  },
  header: {
    alignItems: "center",
    gap: 2,
  },
  otpRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 10,
  },
  otpBox: {
    width: 48,
    height: 56,
    borderRadius: 12,
    borderWidth: 1.5,
    fontSize: 24,
    fontWeight: "600",
  },
  resendRow: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
  },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
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
