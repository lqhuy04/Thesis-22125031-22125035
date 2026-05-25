// components/SessionExpiredModal.tsx
import React, { useEffect, useState } from "react";
import { Modal, View, StyleSheet, TouchableOpacity } from "react-native";
import { router } from "expo-router";
import { removeSession } from "@/helpers/api/TokenStorage";
import { authEvents, AUTH_EXPIRED_EVENT } from "@/helpers/api/authEvents";
import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";

export const SessionExpiredModal = () => {
  const { theme } = useTheme();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handler = () => setVisible(true);
    authEvents.on(AUTH_EXPIRED_EVENT, handler);
    return () => {
      authEvents.off(AUTH_EXPIRED_EVENT, handler);
    };
  }, []);

  const handleConfirm = async () => {
    setVisible(false);
    await removeSession();
    router.replace("/Authentication");
  };

  return (
    <Modal transparent visible={visible} animationType="fade">
      <View style={styles.overlay}>
        <View style={[styles.card, { backgroundColor: theme.background.bg }]}>
          <Text
            typography="titleLarge"
            color={theme.text.primary}
            style={{ marginBottom: 8 }}
          >
            Phiên đăng nhập hết hạn
          </Text>
          <Text
            typography="bodyLarge"
            color={theme.text.primary + "80"}
            style={{ marginBottom: 24 }}
          >
            Vui lòng đăng nhập lại để tiếp tục sử dụng.
          </Text>
          <TouchableOpacity
            onPress={handleConfirm}
            style={[styles.button, { backgroundColor: theme.base.primary }]}
          >
            <Text typography="bodyLarge" color={theme.text.onPrimary}>
              Đăng nhập lại
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "#00000066",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  card: {
    width: "100%",
    borderRadius: 16,
    padding: 24,
  },
  button: {
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
});
