import React, { useEffect, useRef, useState } from "react";
import { Animated, Alert, TouchableOpacity, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { router } from "expo-router";
import { getRiskAppetite, saveRiskAppetite } from "@/helpers/ProfileHelpers";

type PeriodKey = "short_term" | "mid_term" | "long_term";

const SkeletonBox = ({
  width,
  height,
  borderRadius = 8,
  style,
}: {
  width: number | string;
  height: number;
  borderRadius?: number;
  style?: object;
}) => {
  const { theme } = useTheme();
  const opacity = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.4,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius,
          backgroundColor: theme.border.default,
          opacity,
        },
        style,
      ]}
    />
  );
};

const RiskAppetiteSkeleton = () => {
  const insets = useSafeAreaInsets();
  const { theme } = useTheme();

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
        paddingBottom: insets.bottom + 12,
      }}
    >
      <ScreenHeader title="" />

      <View style={{ flex: 1, paddingHorizontal: 20, paddingTop: 28 }}>
        <SkeletonBox width="70%" height={28} borderRadius={6} />
        <SkeletonBox
          width="90%"
          height={16}
          borderRadius={4}
          style={{ marginTop: 12 }}
        />
        <SkeletonBox
          width="60%"
          height={16}
          borderRadius={4}
          style={{ marginTop: 6, marginBottom: 28 }}
        />

        {[0, 1, 2].map((i) => (
          <View
            key={i}
            style={{
              flexDirection: "row",
              alignItems: "center",
              borderWidth: 1.5,
              borderColor: theme.border.default,
              borderRadius: 12,
              padding: 16,
              marginBottom: 12,
            }}
          >
            <SkeletonBox
              width={22}
              height={22}
              borderRadius={11}
              style={{ marginRight: 14 }}
            />
            <View style={{ flex: 1, gap: 6 }}>
              <SkeletonBox width="45%" height={18} borderRadius={4} />
              <SkeletonBox width="30%" height={13} borderRadius={4} />
            </View>
          </View>
        ))}
      </View>

      <SkeletonBox
        width="auto"
        height={48}
        borderRadius={8}
        style={{ marginHorizontal: 20 }}
      />
    </View>
  );
};

const RiskAppetite = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const insets = useSafeAreaInsets();

  const [period, setPeriod] = useState<PeriodKey | "">("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const PERIOD_OPTIONS: { key: PeriodKey; label: string; desc: string }[] = [
    {
      key: "short_term",
      label: t("riskAppetiteScreen.shortTerm"),
      desc: t("riskAppetiteScreen.shortTermDesc"),
    },
    {
      key: "mid_term",
      label: t("riskAppetiteScreen.midTerm"),
      desc: t("riskAppetiteScreen.midTermDesc"),
    },
    {
      key: "long_term",
      label: t("riskAppetiteScreen.longTerm"),
      desc: t("riskAppetiteScreen.longTermDesc"),
    },
  ];

  useEffect(() => {
    setLoading(true);
    getRiskAppetite().then((res) => {
      if (res.status && res.data?.period) {
        setPeriod(res.data.period as PeriodKey);
      }
      setLoading(false);
    });
  }, []);

  const onSave = () => {
    if (!period) return;
    setSaving(true);
    saveRiskAppetite({ period }).then((res) => {
      setSaving(false);
      if (res.status) {
        router.back();
      } else {
        Alert.alert("Lỗi", "Đã có lỗi xảy ra, vui lòng thử lại sau.");
      }
    });
  };

  if (loading) return <RiskAppetiteSkeleton />;

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
        paddingBottom: insets.bottom + 12,
      }}
    >
      <ScreenHeader title={t("riskAppetiteScreen.title")} />

      <View style={{ flex: 1, paddingHorizontal: 20, paddingTop: 28 }}>
        <Text typography="headlineSmall" color={theme.text.primary}>
          {t("riskAppetiteScreen.question")}
        </Text>

        <Text
          typography="bodyMedium"
          color={theme.text.primary + "88"}
          style={{ marginTop: 6, marginBottom: 28 }}
        >
          {t("riskAppetiteScreen.description")}
        </Text>

        {PERIOD_OPTIONS.map((option) => {
          const selected = period === option.key;
          return (
            <TouchableOpacity
              key={option.key}
              activeOpacity={0.75}
              onPress={() => setPeriod(option.key)}
              style={{
                flexDirection: "row",
                alignItems: "center",
                borderWidth: 1.5,
                borderColor: selected
                  ? theme.base.primary
                  : theme.border.default,
                borderRadius: 12,
                padding: 16,
                marginBottom: 12,
                backgroundColor: selected
                  ? theme.base.primary + "18"
                  : theme.background.surface,
              }}
            >
              <View
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 11,
                  borderWidth: 2,
                  borderColor: selected
                    ? theme.base.primary
                    : theme.border.default,
                  alignItems: "center",
                  justifyContent: "center",
                  marginRight: 14,
                }}
              >
                {selected && (
                  <View
                    style={{
                      width: 11,
                      height: 11,
                      borderRadius: 6,
                      backgroundColor: theme.base.primary,
                    }}
                  />
                )}
              </View>

              <View style={{ flex: 1 }}>
                <Text
                  typography="titleMedium"
                  color={selected ? theme.base.primary : theme.text.primary}
                >
                  {option.label}
                </Text>
                <Text
                  typography="bodySmall"
                  color={theme.text.primary + "88"}
                  style={{ marginTop: 2 }}
                >
                  {option.desc}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      <TouchableOpacity
        activeOpacity={period ? 0.8 : 1}
        onPress={period && !saving ? onSave : undefined}
        style={{
          backgroundColor: period ? theme.base.primary : theme.background.bg,
          paddingVertical: 14,
          marginHorizontal: 20,
          borderRadius: 8,
          alignItems: "center",
          opacity: saving ? 0.7 : 1,
        }}
      >
        <Text
          typography="titleMedium"
          color={period ? theme.text.onPrimary : theme.text.primary + "88"}
        >
          {saving
            ? t("riskAppetiteScreen.saving")
            : t("riskAppetiteScreen.save")}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default RiskAppetite;
