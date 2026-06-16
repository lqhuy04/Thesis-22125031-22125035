import { markOnboardingDone } from "@/helpers/onboarding";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import React, { useRef, useState } from "react";
import {
  FlatList,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

type Slide = {
  key: string;
  titleKey: string;
  descKey: string;
  icon: keyof typeof Ionicons.glyphMap;
};

const SLIDES: Slide[] = [
  {
    key: "1",
    titleKey: "onboarding.slide1Title",
    descKey: "onboarding.slide1Desc",
    icon: "trending-up",
  },
  {
    key: "2",
    titleKey: "onboarding.slide2Title",
    descKey: "onboarding.slide2Desc",
    icon: "analytics",
  },
  {
    key: "3",
    titleKey: "onboarding.slide3Title",
    descKey: "onboarding.slide3Desc",
    icon: "sparkles",
  },
];

export default function Onboarding() {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const listRef = useRef<FlatList<Slide>>(null);
  const [index, setIndex] = useState(0);

  const isLast = index === SLIDES.length - 1;

  const finish = async () => {
    await markOnboardingDone();
    router.replace("/Authentication");
  };

  const handleNext = () => {
    if (isLast) {
      finish();
      return;
    }
    listRef.current?.scrollToIndex({ index: index + 1, animated: true });
  };

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const next = Math.round(e.nativeEvent.contentOffset.x / width);
    if (next !== index) setIndex(next);
  };

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: theme.background.bg, paddingTop: insets.top },
      ]}
    >
      {/* Skip */}
      <Pressable
        style={[styles.skipBtn, { opacity: isLast ? 0 : 1 }]}
        disabled={isLast}
        onPress={finish}
        hitSlop={12}
      >
        <Text style={[styles.skipText, { color: theme.text.secondary }]}>
          {t("ui.skip")}
        </Text>
      </Pressable>

      <FlatList
        ref={listRef}
        data={SLIDES}
        keyExtractor={(item) => item.key}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={onScroll}
        scrollEventThrottle={16}
        renderItem={({ item }) => (
          <View style={[styles.slide, { width }]}>
            <View
              style={[
                styles.imageWrap,
                { backgroundColor: theme.background.primarySurface },
              ]}
            >
              <Ionicons name={item.icon} size={96} color={theme.base.primary} />
            </View>
            <Text style={[styles.title, { color: theme.text.primary }]}>
              {t(item.titleKey)}
            </Text>
            <Text style={[styles.description, { color: theme.text.secondary }]}>
              {t(item.descKey)}
            </Text>
          </View>
        )}
      />

      {/* Dots */}
      <View style={styles.dots}>
        {SLIDES.map((_, i) => (
          <View
            key={i}
            style={[
              styles.dot,
              {
                backgroundColor:
                  i === index ? theme.base.primary : theme.border.default,
                width: i === index ? 22 : 8,
              },
            ]}
          />
        ))}
      </View>

      {/* CTA */}
      <View style={[styles.footer, { paddingBottom: insets.bottom + 16 }]}>
        <Pressable
          style={[styles.cta, { backgroundColor: theme.base.primary }]}
          onPress={handleNext}
        >
          <Text style={[styles.ctaText, { color: theme.text.onPrimary }]}>
            {isLast ? t("ui.start") : t("ui.continue")}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  skipBtn: {
    alignSelf: "flex-end",
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  skipText: { fontSize: 15, fontFamily: "Roboto-Medium" },
  slide: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
  },
  imageWrap: {
    width: 220,
    height: 220,
    borderRadius: 110,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 48,
  },
  title: {
    fontSize: 24,
    fontFamily: "Roboto-SemiBold",
    textAlign: "center",
    marginBottom: 12,
  },
  description: {
    fontSize: 15,
    fontFamily: "Roboto-Regular",
    textAlign: "center",
    lineHeight: 22,
  },
  dots: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 8,
    marginBottom: 24,
  },
  dot: { height: 8, borderRadius: 4 },
  footer: { paddingHorizontal: 24 },
  cta: {
    height: 52,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  ctaText: { fontSize: 16, fontFamily: "Roboto-SemiBold" },
});
