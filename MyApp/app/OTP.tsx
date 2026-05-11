import React, { useRef, useState } from "react";
import {
  ActivityIndicator,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { router } from "expo-router";

const OTP_LENGTH = 4;

const OTPScreen = () => {
  const { theme } = useTheme();
  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(""));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputs = useRef<(TextInput | null)[]>([]);

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
    if (code.length < OTP_LENGTH) return setError("Vui lòng nhập đủ 4 chữ số.");

    setError("");
    setLoading(true);
    // TODO: gọi API xác thực OTP
    await new Promise((r) => setTimeout(r, 1200));
    setLoading(false);
    // if (!res.status) setError("Mã OTP không đúng. Vui lòng thử lại.");

    router.push("./NewPass");
  };

  const handleResend = () => {
    setOtp(Array(OTP_LENGTH).fill(""));
    setError("");
    inputs.current[0]?.focus();
    // TODO: gọi API gửi lại OTP
  };

  const filled = otp.every((d) => d !== "");

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title="Xác thực OTP" />

      <View style={styles.content}>
        {/* Description */}
        <View style={styles.header}>
          <Text typography="titleLarge">Nhập mã xác thực</Text>
          <Text
            typography="bodyMedium"
            style={{ opacity: 0.5, textAlign: "center", marginTop: 6 }}
          >
            Mã OTP gồm 4 chữ số đã được gửi đến email của bạn
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
          <TouchableOpacity onPress={handleResend}>
            <Text typography="titleMedium" color={theme.base.primary}>
              Gửi lại
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
    gap: 14,
  },
  otpBox: {
    width: 64,
    height: 64,
    borderRadius: 14,
    borderWidth: 1.5,
    fontSize: 28,
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
});
