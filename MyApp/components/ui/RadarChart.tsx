// RadarChart.tsx
//
// Animated radar (spider) chart built on react-native-svg + reanimated.
// The data polygon grows out from the center and fades in on mount / data change.
// Filled with the brand purple gradient and a soft radial glow for emphasis.
// Each axis value is expected to be a ratio between 0 and 1 (rendered as %).

import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useMemo } from "react";
import { Pressable, View } from "react-native";
import Animated, {
  interpolate,
  SharedValue,
  useAnimatedProps,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import Svg, {
  Circle,
  Defs,
  Line,
  LinearGradient,
  Path,
  Polygon,
  RadialGradient,
  Stop,
} from "react-native-svg";

const AnimatedPath = Animated.createAnimatedComponent(Path);
const AnimatedCircle = Animated.createAnimatedComponent(Circle);

// Brand purple gradient (light → deep), matching the app theme.
const PURPLE_LIGHT = "#9D8CFF";
const PURPLE_MID = "#7B5CFF";
const PURPLE_DEEP = "#613DE4";

export interface RadarAxis {
  label: string;
  value: number; // 0..1
}

interface RadarChartProps {
  data: RadarAxis[];
  size?: number;
  maxValue?: number;
  levels?: number;
  duration?: number;
  selectedIndex?: number | null;
  onAxisPress?: (index: number) => void;
}

type Point = { x: number; y: number };

// ─── Animated data layer ─────────────────────────────────────────────────────

const DataPolygon = ({
  progress,
  points,
  centerX,
  centerY,
}: {
  progress: SharedValue<number>;
  points: Point[];
  centerX: number;
  centerY: number;
}) => {
  const animatedProps = useAnimatedProps(() => {
    let d = "";
    for (let i = 0; i < points.length; i++) {
      const x = interpolate(progress.value, [0, 1], [centerX, points[i].x]);
      const y = interpolate(progress.value, [0, 1], [centerY, points[i].y]);
      d += `${i === 0 ? "M" : "L"}${x},${y} `;
    }
    d += "Z";
    return { d, fillOpacity: progress.value, strokeOpacity: progress.value };
  });

  return (
    <AnimatedPath
      animatedProps={animatedProps}
      fill="url(#radarFill)"
      stroke={PURPLE_MID}
      strokeWidth={2.5}
      strokeLinejoin="round"
    />
  );
};

const DataDot = ({
  progress,
  point,
  centerX,
  centerY,
}: {
  progress: SharedValue<number>;
  point: Point;
  centerX: number;
  centerY: number;
}) => {
  const animatedProps = useAnimatedProps(() => ({
    cx: interpolate(progress.value, [0, 1], [centerX, point.x]),
    cy: interpolate(progress.value, [0, 1], [centerY, point.y]),
    opacity: progress.value,
  }));

  return (
    <AnimatedCircle
      animatedProps={animatedProps}
      r={5}
      fill={PURPLE_LIGHT}
      stroke="#FFFFFF"
      strokeWidth={2}
    />
  );
};

// ─── Chart ───────────────────────────────────────────────────────────────────

export const RadarChart = ({
  data,
  size = 260,
  maxValue = 1,
  levels = 4,
  duration = 900,
  selectedIndex = null,
  onAxisPress,
}: RadarChartProps) => {
  const { theme } = useTheme();
  const webColor = theme.border.default;

  const padding = 48; // room for labels around the chart
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - padding;
  const n = data.length;

  const progress = useSharedValue(0);

  useEffect(() => {
    progress.value = 0;
    progress.value = withTiming(1, { duration });
  }, [data, duration, progress]);

  const angleFor = (i: number) => (2 * Math.PI * i) / n - Math.PI / 2;

  // Final coordinates of each data point.
  const dataPoints = useMemo<Point[]>(
    () =>
      data.map((axis, i) => {
        const ratio = Math.min(Math.max(axis.value / maxValue, 0), 1);
        const a = angleFor(i);
        return {
          x: cx + radius * ratio * Math.cos(a),
          y: cy + radius * ratio * Math.sin(a),
        };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, maxValue, radius, cx, cy, n],
  );

  // Concentric grid rings.
  const rings = useMemo(() => {
    const out: string[] = [];
    for (let l = 1; l <= levels; l++) {
      const rr = (radius * l) / levels;
      const pts = data
        .map((_, i) => {
          const a = angleFor(i);
          return `${cx + rr * Math.cos(a)},${cy + rr * Math.sin(a)}`;
        })
        .join(" ");
      out.push(pts);
    }
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, levels, radius, cx, cy, n]);

  // Axis spokes + label anchor positions.
  const axes = useMemo(
    () =>
      data.map((axis, i) => {
        const a = angleFor(i);
        return {
          x: cx + radius * Math.cos(a),
          y: cy + radius * Math.sin(a),
          lx: cx + (radius + padding * 0.8) * Math.cos(a),
          ly: cy + (radius + padding * 0.8) * Math.sin(a),
          label: axis.label,
          value: axis.value,
        };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, radius, cx, cy, n],
  );

  return (
    <View style={{ width: size, height: size, alignSelf: "center" }}>
      <Svg width={size} height={size}>
        <Defs>
          <LinearGradient id="radarFill" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={PURPLE_LIGHT} stopOpacity={0.55} />
            <Stop offset="1" stopColor={PURPLE_DEEP} stopOpacity={0.35} />
          </LinearGradient>
          <RadialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
            <Stop offset="0" stopColor={PURPLE_MID} stopOpacity={0.28} />
            <Stop offset="1" stopColor={PURPLE_MID} stopOpacity={0} />
          </RadialGradient>
        </Defs>

        {/* Soft glow behind the web */}
        <Circle cx={cx} cy={cy} r={radius} fill="url(#radarGlow)" />

        {rings.map((pts, i) => (
          <Polygon
            key={`ring-${i}`}
            points={pts}
            fill="none"
            stroke={webColor}
            strokeWidth={1}
            opacity={0.5}
          />
        ))}
        {axes.map((ax, i) => (
          <Line
            key={`axis-${i}`}
            x1={cx}
            y1={cy}
            x2={ax.x}
            y2={ax.y}
            stroke={webColor}
            strokeWidth={1}
            opacity={0.5}
          />
        ))}
        <DataPolygon
          progress={progress}
          points={dataPoints}
          centerX={cx}
          centerY={cy}
        />
        {dataPoints.map((p, i) => (
          <DataDot
            key={`dot-${i}`}
            progress={progress}
            point={p}
            centerX={cx}
            centerY={cy}
          />
        ))}
      </Svg>

      {/* Labels overlay (RN text for theming/typography) */}
      {axes.map((ax, i) => {
        const isSelected = selectedIndex === i;
        return (
          <Pressable
            key={`label-${i}`}
            onPress={() => onAxisPress?.(i)}
            style={{
              position: "absolute",
              left: ax.lx - 52,
              top: ax.ly - 16,
              width: 104,
              alignItems: "center",
            }}
          >
            <Text
              typography="labelMedium"
              color={isSelected ? "#FFFFFF" : theme.text.primary + "99"}
              style={{ textAlign: "center" }}
            >
              {ax.label}
            </Text>
            <Text typography="labelLarge" color={isSelected ? "#FFFFFF" : PURPLE_LIGHT}>
              {Math.round((ax.value / maxValue) * 100)}%
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
};

export default RadarChart;
