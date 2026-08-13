// components/TreeMap.tsx
import React, { useCallback, useMemo, useState } from "react";
import type { GestureResponderEvent } from "react-native";
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  Pressable,
  StyleSheet,
  Image,
} from "react-native";
import Svg, { Rect, Text as SvgText } from "react-native-svg";
import { hierarchy, treemap, treemapSquarify } from "d3-hierarchy";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { CurrentPriceData } from "@/helpers/DetailHelpers";
import { useLocalization } from "@/hooks/LocalizationContext";
import {
  formatPercentageChange,
  formatPriceChange,
  getStockChangeColor,
} from "@/helpers/stockChange";

// ─── Types ────────────────────────────────────────────────────────────────────

interface TreeNode {
  label: string;
  value: number;
  color: string;
  raw: CurrentPriceData;
}

interface LayoutRect extends TreeNode {
  x: number;
  y: number;
  width: number;
  height: number;
}

// ─── D3 layout ────────────────────────────────────────────────────────────────

function computeLayout(
  nodes: TreeNode[],
  width: number,
  height: number,
): LayoutRect[] {
  if (!nodes.length || width <= 0 || height <= 0) return [];

  const root = hierarchy<{ children?: TreeNode[] }>({ children: nodes })
    .sum((d) => (d as any).value ?? 0)
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  treemap<{ children?: TreeNode[] }>()
    .tile(treemapSquarify)
    .size([width, height])
    .paddingInner(0)(root);

  return root.leaves().map((leaf) => {
    const l = leaf as any;
    return {
      ...(leaf.data as unknown as TreeNode),
      x: l.x0,
      y: l.y0,
      width: l.x1 - l.x0,
      height: l.y1 - l.y0,
    };
  });
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getFontSize(
  rectWidth: number,
  rectHeight: number,
  text: string,
  minSize = 6,
  maxSize = 16,
): number {
  const maxByWidth = rectWidth / (text.length * 0.8);
  const maxByHeight = rectHeight * 0.55;
  return Math.min(
    maxSize,
    Math.max(minSize, Math.min(maxByWidth, maxByHeight)),
  );
}

function formatVal(val: number, t: (k: string) => string): string {
  if (val >= 1_000_000_000_000)
    return (
      (val / 1_000_000_000_000).toLocaleString("vi-VN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) +
      " " +
      t("treeMap.trillion")
    );
  if (val >= 1_000_000_000)
    return (
      (val / 1_000_000_000).toLocaleString("vi-VN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) +
      " " +
      t("treeMap.billion")
    );
  return val.toLocaleString("vi-VN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

function formatVol(vol: number, t: (k: string) => string): string {
  if (vol >= 1_000_000)
    return (
      (vol / 1_000_000).toLocaleString("vi-VN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) +
      " " +
      t("treeMap.millionShares")
    );
  if (vol >= 1_000)
    return (
      (vol / 1_000).toLocaleString("vi-VN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) +
      " " +
      t("treeMap.thousandShares")
    );
  return (
    vol.toLocaleString("vi-VN", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }) +
    " " +
    t("treeMap.shares")
  );
}

// ─── Component ────────────────────────────────────────────────────────────────

interface Props {
  data: CurrentPriceData[];
  width: number;
  height: number;
  padding?: number;
  title?: string;
}

export const TreeMap: React.FC<Props> = ({
  data,
  width,
  height,
  padding = 2,
  title,
}) => {
  const { t } = useLocalization();
  const { theme } = useTheme();
  const [selectedItem, setSelectedItem] = useState<CurrentPriceData | null>(
    null,
  );

  const chartW = width;
  const chartH = height - 24;

  const perText = (item: CurrentPriceData) => {
    return formatPercentageChange(item.PerPriceChange);
  };

  const perColor = useCallback(
    (item: CurrentPriceData) =>
      getStockChangeColor(item.PerPriceChange, theme.base),
    [theme.base],
  );

  const nodes: TreeNode[] = useMemo(
    () =>
      data.map((item) => ({
        label: item.symbol,
        value: item.TotalMatchVal,
        color: perColor(item),
        raw: item,
      })),
    [data, perColor],
  );

  // ← d3-hierarchy treemapSquarify thay vì tự viết
  const rects = useMemo(
    () => computeLayout(nodes, chartW, chartH),
    [nodes, chartW, chartH],
  );

  const handleTreeMapPress = useCallback(
    (event: GestureResponderEvent) => {
      const { locationX, locationY } = event.nativeEvent;
      const selectedRect = rects.find(
        (rect) =>
          locationX >= rect.x + padding &&
          locationX <= rect.x + rect.width - padding &&
          locationY >= rect.y + padding &&
          locationY <= rect.y + rect.height - padding,
      );

      if (selectedRect) setSelectedItem(selectedRect.raw);
    },
    [padding, rects],
  );

  return (
    <View style={{ width, height }}>
      {title && (
        <Text
          style={{
            fontSize: 14,
            color: theme.text?.primary,
            marginTop: 8,
            fontWeight: 700,
          }}
        >
          {title}
        </Text>
      )}

      <Pressable
        onPress={handleTreeMapPress}
        style={{ width: chartW, height: chartH }}
      >
        <Svg width={chartW} height={chartH} pointerEvents="none">
          {rects.map((r, i) => {
            const rw = Math.max(0, r.width - padding * 2);
            const rh = Math.max(0, r.height - padding * 2);
            const cx = r.x + r.width / 2;
            const cy = r.y + r.height / 2;

            const labelSize = getFontSize(rw * 0.9, rh * 0.5, r.label);
            const perStr = perText(r.raw);
            const valueSize = getFontSize(rw * 0.9, rh * 0.4, perStr, 5, 13);
            const twoLines = rh >= labelSize + valueSize + 6;

            return (
              <React.Fragment key={i}>
                <Rect
                  x={r.x + padding}
                  y={r.y + padding}
                  width={rw}
                  height={rh}
                  fill={r.color}
                  rx={4}
                />
                {twoLines ? (
                  <>
                    <SvgText
                      x={cx}
                      y={cy - valueSize / 2}
                      textAnchor="middle"
                      fill="#fff"
                      fontSize={labelSize}
                      fontWeight="bold"
                      dy={-labelSize * 0.2}
                    >
                      {r.label}
                    </SvgText>
                    <SvgText
                      x={cx}
                      y={cy + labelSize / 2}
                      textAnchor="middle"
                      fill="#ffffffdd"
                      fontSize={valueSize}
                    >
                      {perStr}
                    </SvgText>
                  </>
                ) : (
                  <SvgText
                    x={cx}
                    y={cy + labelSize * 0.35}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={labelSize}
                    fontWeight="bold"
                  >
                    {r.label}
                  </SvgText>
                )}
              </React.Fragment>
            );
          })}
        </Svg>
      </Pressable>

      {/* Popup */}
      <Modal
        visible={!!selectedItem}
        transparent
        animationType="fade"
        onRequestClose={() => setSelectedItem(null)}
      >
        <Pressable style={styles.overlay} onPress={() => setSelectedItem(null)}>
          <Pressable
            style={[
              styles.popup,
              { backgroundColor: theme.background?.bg ?? "#fff" },
            ]}
            onPress={() => {}}
          >
            {/* Header */}
            <View style={styles.popupHeader}>
              <Image
                resizeMode="contain"
                source={{
                  uri:
                    selectedItem?.logo ||
                    "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png",
                }}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 2,
                  marginRight: 12,
                }}
              />
              <View style={{ flex: 1 }}>
                <Text
                  style={[styles.popupSymbol, { color: theme.text?.primary }]}
                >
                  {selectedItem?.symbol}
                </Text>
                <Text
                  style={[styles.popupCompany, { color: theme.text?.primary }]}
                  numberOfLines={1}
                >
                  {selectedItem?.company_name}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => setSelectedItem(null)}
                style={styles.closeBtn}
              >
                <Text style={{ fontSize: 16, color: theme.text?.primary }}>
                  ✕
                </Text>
              </TouchableOpacity>
            </View>

            <View
              style={{
                height: 1,
                backgroundColor: theme.border.default,
                marginVertical: 14,
              }}
            />

            {/* Rows */}
            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: theme.text?.primary }]}>
                {t("treeMap.price")}
              </Text>
              <View
                style={{ flexDirection: "row", gap: 8, alignItems: "center" }}
              >
                <Text style={[styles.rowValue, { color: theme.text?.primary }]}>
                  {selectedItem?.CurrentPrice.toLocaleString("vi-VN", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </Text>
                {selectedItem && (
                  <>
                    <Text
                      style={[
                        styles.rowValue,
                        {
                          color: getStockChangeColor(
                            selectedItem.PriceChange,
                            theme.base,
                          ),
                        },
                      ]}
                    >
                      ({formatPriceChange(selectedItem.PriceChange)})
                    </Text>
                    <Text
                      style={[
                        styles.badge,
                        {
                          backgroundColor: perColor(selectedItem) + "22",
                          color: perColor(selectedItem),
                        },
                      ]}
                    >
                      {perText(selectedItem)}
                    </Text>
                  </>
                )}
              </View>
            </View>

            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: theme.text?.primary }]}>
                {t("treeMap.tradingValue")}
              </Text>
              <Text style={[styles.rowValue, { color: theme.text?.primary }]}>
                {selectedItem ? formatVal(selectedItem.TotalMatchVal, t) : ""}
              </Text>
            </View>

            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: theme.text?.primary }]}>
                {t("treeMap.tradingVolume")}
              </Text>
              <Text style={[styles.rowValue, { color: theme.text?.primary }]}>
                {selectedItem ? formatVol(selectedItem.TotalMatchVol, t) : ""}
              </Text>
            </View>

            {/* CTA */}
            <TouchableOpacity
              style={[styles.ctaBtn, { backgroundColor: theme.base.primary }]}
              onPress={() => {
                setSelectedItem(null);
                router.push({
                  pathname: "/Detail",
                  params: { data: selectedItem?.symbol },
                });
              }}
            >
              <Text style={styles.ctaText}>{t("treeMap.viewDetail")}</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "center",
    alignItems: "center",
  },
  popup: {
    width: 320,
    borderRadius: 16,
    padding: 20,
    elevation: 8,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 12,
  },
  popupHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  popupSymbol: { fontSize: 20, fontWeight: "bold" },
  popupCompany: { fontSize: 13, marginTop: 2, maxWidth: 240 },
  closeBtn: { padding: 4 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  rowLabel: { fontSize: 14 },
  rowValue: { fontSize: 14, fontWeight: "600" },
  badge: {
    fontSize: 12,
    fontWeight: "600",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  ctaBtn: {
    marginTop: 16,
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: "center",
  },
  ctaText: { color: "#fff", fontWeight: "bold", fontSize: 15 },
});
