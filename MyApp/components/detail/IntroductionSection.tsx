import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  LayoutAnimation,
  Platform,
  Pressable,
  UIManager,
  View,
} from "react-native";
import { Text } from "../ui/Text";
import {
  CompanyLeader,
  CompanyProfile,
  getCompanyLeaders,
  getCompanyProfile,
} from "@/helpers/CompanyProfileHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import Entypo from "@expo/vector-icons/Entypo";

if (
  Platform.OS === "android" &&
  UIManager.setLayoutAnimationEnabledExperimental
) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface IntroductionSectionProps {
  stockSymbol: string;
}

// ── Skeleton ────────────────────────────────────────────────────────────────
const SkeletonBox = ({
  width,
  height,
  borderRadius = 6,
  style,
}: {
  width: number | string;
  height: number;
  borderRadius?: number;
  style?: object;
}) => {
  const { theme } = useTheme();
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: 900,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, [shimmer]);

  const opacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [0.35, 0.7],
  });

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius,
          backgroundColor: theme.text.primary + "30",
          opacity,
        },
        style,
      ]}
    />
  );
};

const SkeletonSection = () => (
  <View style={{ paddingVertical: 14, gap: 0 }}>
    {/* Section header row */}
    <View
      style={{
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 14,
      }}
    >
      <SkeletonBox width={140} height={16} />
      <SkeletonBox width={16} height={16} borderRadius={4} />
    </View>
    {/* Info rows */}
    {[100, 120, 90, 110].map((w, i) => (
      <View
        key={i}
        style={{
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <SkeletonBox width={w} height={13} />
        <SkeletonBox width={80} height={13} />
      </View>
    ))}
  </View>
);

const IntroductionSkeleton = () => {
  const { theme } = useTheme();
  return (
    <View>
      <View style={{ marginHorizontal: 12, marginTop: 12 }}>
        <SkeletonBox width={160} height={16} />
      </View>
      <View
        style={{
          marginTop: 12,
          marginHorizontal: 12,
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          paddingHorizontal: 12,
          paddingVertical: 4,
        }}
      >
        <SkeletonSection />
        <SkeletonSection />
        <SkeletonSection />
      </View>
    </View>
  );
};

// ── Accordion ────────────────────────────────────────────────────────────────
interface AccordionProps {
  title: string;
  defaultOpen?: boolean;
  borderColor: string;
  titleColor: string;
  children: React.ReactNode;
}

const Accordion = ({
  title,
  defaultOpen = false,
  borderColor,
  titleColor,
  children,
}: AccordionProps) => {
  const [open, setOpen] = useState(defaultOpen);
  const rotateAnim = useRef(new Animated.Value(defaultOpen ? 1 : 0)).current;
  const { theme } = useTheme();

  const toggle = () => {
    LayoutAnimation.configureNext({
      duration: 260,
      create: { type: "easeInEaseOut", property: "opacity" },
      update: { type: "spring", springDamping: 0.78 },
      delete: { type: "easeInEaseOut", property: "opacity" },
    });
    Animated.timing(rotateAnim, {
      toValue: open ? 0 : 1,
      duration: 240,
      useNativeDriver: true,
    }).start();
    setOpen((prev) => !prev);
  };

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "180deg"],
  });

  return (
    <View>
      <Pressable
        onPress={toggle}
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          paddingVertical: 14,
        }}
      >
        <Text typography="titleMedium" color={titleColor}>
          {title}
        </Text>
        <Animated.View style={{ transform: [{ rotate }] }}>
          <View
            style={{
              width: 20,
              height: 20,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Entypo
              name="chevron-small-down"
              size={24}
              color={theme.base.primary}
            />
          </View>
        </Animated.View>
      </Pressable>
      {open && <View style={{ paddingBottom: 16 }}>{children}</View>}
    </View>
  );
};

// ── Info row ─────────────────────────────────────────────────────────────────
const InfoRow = ({
  label,
  value,
  labelColor,
  valueColor,
}: {
  label: string;
  value?: string | number | null;
  labelColor: string;
  valueColor: string;
}) => (
  <View
    style={{
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      marginTop: 8,
    }}
  >
    <Text typography="bodyLarge" color={labelColor}>
      {label}
    </Text>
    <Text
      typography="bodyMedium"
      color={valueColor}
      style={{ maxWidth: "55%", textAlign: "right" }}
    >
      {value ?? "--"}
    </Text>
  </View>
);

// ── Main component ────────────────────────────────────────────────────────────
const IntroductionSection = ({ stockSymbol }: IntroductionSectionProps) => {
  const { theme } = useTheme();
  const [companyProfileData, setCompanyProfileData] =
    useState<CompanyProfile | null>(null);
  const [leaders, setLeaders] = useState<CompanyLeader[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getCompanyProfile(stockSymbol).then((res) => {
        if (res.status) setCompanyProfileData(res.data);
      }),
      getCompanyLeaders(stockSymbol).then((res) => {
        if (res.status) setLeaders(res.data);
      }),
    ]).finally(() => setLoading(false));
  }, [stockSymbol]);

  if (loading) return <IntroductionSkeleton />;
  if (!companyProfileData) return null;

  const labelColor = theme.text.primary;
  const valueColor = theme.text.primary + "88";
  const borderColor = theme.border.default;

  return (
    <View>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginHorizontal: 12, marginTop: 24 }}
      >
        Hồ sơ doanh nghiệp
      </Text>

      <View
        style={{
          marginTop: 12,
          marginHorizontal: 12,
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          paddingHorizontal: 12,
          paddingTop: 4,
          paddingBottom: 4,
        }}
      >
        <Accordion
          title="Giới thiệu chung"
          defaultOpen
          borderColor={borderColor}
          titleColor={labelColor}
        >
          <Text typography="bodyMedium" color={valueColor}>
            {companyProfileData.description}
          </Text>
          <View style={{ height: 10 }} />
          <Text typography="bodyMedium" color={valueColor}>
            • Địa chỉ: {companyProfileData.address}
          </Text>
          <Text typography="bodyMedium" color={valueColor}>
            • Email: {companyProfileData.email}
          </Text>
          <Text typography="bodyMedium" color={valueColor}>
            • Điện thoại: {companyProfileData.phone}
          </Text>
          <Text typography="bodyMedium" color={valueColor}>
            • Website: {companyProfileData.website}
          </Text>
          <Text typography="bodyMedium" color={valueColor}>
            • Fax: {companyProfileData.fax}
          </Text>
        </Accordion>

        <Accordion
          title="Thông tin cơ bản"
          borderColor={borderColor}
          titleColor={labelColor}
        >
          <InfoRow
            label="Mã"
            value={companyProfileData.symbol}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="Tên ngành ICB"
            value={companyProfileData.industry_name}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="Mã ngành ICB"
            value={companyProfileData.icb_code}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="Năm thành lập"
            value={companyProfileData.founded_date}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="Vốn điều lệ"
            value={`${companyProfileData.listed_volume} tỷ`}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="Số lượng nhân viên"
            value={companyProfileData.employee_count}
            labelColor={labelColor}
            valueColor={valueColor}
          />
        </Accordion>

        <Accordion
          title="Thông tin niêm yết"
          borderColor={borderColor}
          titleColor={labelColor}
        >
          <InfoRow
            label="Ngày niêm yết"
            value={companyProfileData.listing_date}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="Nơi niêm yết"
            value={companyProfileData.exchange}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="Giá chào sàn (1000 VND)"
            value={companyProfileData.ipo_price}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="KL đang niêm yết"
            value={`${companyProfileData.market_cap_billion} tỷ`}
            labelColor={labelColor}
            valueColor={valueColor}
          />
          <InfoRow
            label="SLCP lưu hành"
            value={companyProfileData.shares_outstanding}
            labelColor={labelColor}
            valueColor={valueColor}
          />
        </Accordion>

        {leaders.length > 0 && (
          <Accordion
            title="Ban lãnh đạo"
            borderColor={borderColor}
            titleColor={labelColor}
          >
            {leaders.map((leader, index) => (
              <View
                key={index}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginTop: 8,
                  paddingVertical: 6,
                  borderBottomWidth: index < leaders.length - 1 ? 1 : 0,
                  borderBottomColor: borderColor,
                }}
              >
                <Text
                  typography="titleMedium"
                  color={labelColor}
                  style={{ flex: 1 }}
                >
                  {leader.full_name}
                </Text>
                <Text
                  typography="bodyMedium"
                  color={valueColor}
                  style={{ maxWidth: "45%", textAlign: "right" }}
                >
                  {leader.position}
                </Text>
              </View>
            ))}
          </Accordion>
        )}
      </View>
    </View>
  );
};

export default IntroductionSection;
