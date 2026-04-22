// components/TreeMap.tsx
import React, { useCallback, useMemo, useState } from "react";
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  Pressable,
  StyleSheet,
} from "react-native";
import Svg, { Rect, Text as SvgText } from "react-native-svg";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { CurrentPriceData } from "@/helpers/DetailHelpers";

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

function squarify(
  data: TreeNode[],
  x: number,
  y: number,
  width: number,
  height: number,
): LayoutRect[] {
  const rects: LayoutRect[] = [];
  const total = data.reduce((s, n) => s + n.value, 0);
  if (total === 0 || data.length === 0) return rects;

  const sorted = [...data].sort((a, b) => b.value - a.value);
  let curX = x,
    curY = y,
    remW = width,
    remH = height,
    usedValue = 0;

  sorted.forEach((node) => {
    const ratio = node.value / (total - usedValue);
    usedValue += node.value;
    if (remW >= remH) {
      const rw = remW * ratio;
      rects.push({ ...node, x: curX, y: curY, width: rw, height: remH });
      curX += rw;
      remW -= rw;
    } else {
      const rh = remH * ratio;
      rects.push({ ...node, x: curX, y: curY, width: remW, height: rh });
      curY += rh;
      remH -= rh;
    }
  });
  return rects;
}

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

function formatVal(val: number): string {
  if (val >= 1_000_000_000_000)
    return (val / 1_000_000_000_000).toFixed(2) + " nghìn tỷ";
  if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(2) + " tỷ";
  return val.toLocaleString();
}

function formatVol(vol: number): string {
  if (vol >= 1_000_000) return (vol / 1_000_000).toFixed(2) + " triệu cp";
  if (vol >= 1_000) return (vol / 1_000).toFixed(2) + " nghìn cp";
  return vol.toLocaleString() + " cp";
}

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
  const { theme } = useTheme();
  const [selectedItem, setSelectedItem] = useState<CurrentPriceData | null>(
    null,
  );

  const titleHeight = title ? 28 : 0;
  const chartW = width;
  const chartH = height - titleHeight;

  const perText = (item: CurrentPriceData) => {
    const sign = item.PerPriceChange > 0 ? "+" : "";
    return `${sign}${item.PerPriceChange.toFixed(2)}%`;
  };

  const perColor = useCallback(
    (item: CurrentPriceData) =>
      item.PerPriceChange > 6
        ? theme.base.primary
        : item.PerPriceChange > 0
          ? theme.base.success
          : item.PerPriceChange < 0
            ? theme.base.error
            : theme.base.warning,
    [
      theme.base.error,
      theme.base.primary,
      theme.base.success,
      theme.base.warning,
    ],
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

  const rects = useMemo(
    () => squarify(nodes, 0, 0, chartW, chartH),
    [nodes, chartW, chartH],
  );

  return (
    <View style={{ width, height }}>
      {title && (
        <Text
          style={{
            textAlign: "center",
            fontWeight: "bold",
            height: titleHeight,
            lineHeight: titleHeight,
            fontSize: 16,
            color: theme.text?.primary,
          }}
        >
          {title}
        </Text>
      )}

      <Svg width={chartW} height={chartH}>
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
                onPress={() => setSelectedItem(r.raw)}
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
                    onPress={() => setSelectedItem(r.raw)}
                  >
                    {r.label}
                  </SvgText>
                  <SvgText
                    x={cx}
                    y={cy + labelSize / 2}
                    textAnchor="middle"
                    fill="#ffffffdd"
                    fontSize={valueSize}
                    onPress={() => setSelectedItem(r.raw)}
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
                  onPress={() => setSelectedItem(r.raw)}
                >
                  {r.label}
                </SvgText>
              )}
            </React.Fragment>
          );
        })}
      </Svg>

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
              <View>
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

            <View style={styles.divider} />

            {/* Rows */}
            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: theme.text?.primary }]}>
                Giá:
              </Text>
              <View
                style={{ flexDirection: "row", gap: 8, alignItems: "center" }}
              >
                <Text style={[styles.rowValue, { color: theme.text?.primary }]}>
                  {selectedItem?.CurrentPrice.toLocaleString()}
                </Text>
                {selectedItem && (
                  <>
                    <Text
                      style={[
                        styles.rowValue,
                        { color: perColor(selectedItem) },
                      ]}
                    >
                      ({selectedItem.PriceChange > 0 ? "+" : ""}
                      {selectedItem.PriceChange})
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
                      {selectedItem.PriceChange > 0
                        ? "▲"
                        : selectedItem.PriceChange < 0
                          ? "▼"
                          : ""}
                      {perText(selectedItem)}
                    </Text>
                  </>
                )}
              </View>
            </View>

            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: theme.text?.primary }]}>
                Giá trị GD:
              </Text>
              <Text style={[styles.rowValue, { color: theme.text?.primary }]}>
                {selectedItem ? formatVal(selectedItem.TotalMatchVal) : ""}
              </Text>
            </View>

            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: theme.text?.primary }]}>
                Khối lượng GD:
              </Text>
              <Text style={[styles.rowValue, { color: theme.text?.primary }]}>
                {selectedItem ? formatVol(selectedItem.TotalMatchVol) : ""}
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
              <Text style={styles.ctaText}>Xem chi tiết</Text>
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
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  popupSymbol: { fontSize: 20, fontWeight: "bold" },
  popupCompany: { fontSize: 13, marginTop: 2, maxWidth: 240 },
  closeBtn: { padding: 4 },
  divider: { height: 1, backgroundColor: "#00000015", marginVertical: 14 },
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
