// RadarChart.tsx
//
// Animated radar (spider) chart built on react-native-svg + reanimated.
// The data polygon grows out from the center and fades in on mount / data change.
// Each axis value is expected to be a ratio between 0 and 1 (rendered as %).

import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useMemo } from "react";
import { View } from "react-native";
import Animated, {
  interpolate,
  SharedValue,
  useAnimatedProps,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import Svg, { Circle, Line, Path, Polygon } from "react-native-svg";

const AnimatedPath = Animated.createAnimatedComponent(Path);
const AnimatedCircle = Animated.createAnimatedComponent(Circle);

export interface RadarAxis {
  label: string;
  value: number; // 0..1
}

interface RadarChartProps {
  data: RadarAxis[];
  size?: number;
  maxValue?: number;
  levels?: number;
  color?: string;
  duration?: number;
}

type Point = { x: number; y: number };

// ─── Animated data layer ─────────────────────────────────────────────────────

const DataPolygon = ({
  progress,
  points,
  centerX,
  centerY,
  color,
}: {
  progress: SharedValue<number>;
  points: Point[];
  centerX: number;
  centerY: number;
  color: string;
}) => {
  const animatedProps = useAnimatedProps(() => {
    let d = "";
    for (let i = 0; i < points.length; i++) {
      const x = interpolate(progress.value, [0, 1], [centerX, points[i].x]);
      const y = interpolate(progress.value, [0, 1], [centerY, points[i].y]);
      d += `${i === 0 ? "M" : "L"}${x},${y} `;
    }
    d += "Z";
    return { d, fillOpacity: 0.25 * progress.value };
  });

  return (
    <AnimatedPath
      animatedProps={animatedProps}
      fill={color}
      stroke={color}
      strokeWidth={2}
    />
  );
};

const DataDot = ({
  progress,
  point,
  centerX,
  centerY,
  color,
}: {
  progress: SharedValue<number>;
  point: Point;
  centerX: number;
  centerY: number;
  color: string;
}) => {
  const animatedProps = useAnimatedProps(() => ({
    cx: interpolate(progress.value, [0, 1], [centerX, point.x]),
    cy: interpolate(progress.value, [0, 1], [centerY, point.y]),
    opacity: progress.value,
  }));

  return (
    <AnimatedCircle
      animatedProps={animatedProps}
      r={4}
      fill={color}
      stroke="#FFFFFF"
      strokeWidth={1.5}
    />
  );
};

// ─── Chart ───────────────────────────────────────────────────────────────────

export const RadarChart = ({
  data,
  size = 260,
  maxValue = 1,
  levels = 4,
  color,
  duration = 900,
}: RadarChartProps) => {
  const { theme } = useTheme();
  const accent = color ?? theme.base.primary;
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
          lx: cx + (radius + padding * 0.6) * Math.cos(a),
          ly: cy + (radius + padding * 0.6) * Math.sin(a),
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
        {rings.map((pts, i) => (
          <Polygon
            key={`ring-${i}`}
            points={pts}
            fill="none"
            stroke={webColor}
            strokeWidth={1}
            opacity={0.6}
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
            opacity={0.6}
          />
        ))}
        <DataPolygon
          progress={progress}
          points={dataPoints}
          centerX={cx}
          centerY={cy}
          color={accent}
        />
        {dataPoints.map((p, i) => (
          <DataDot
            key={`dot-${i}`}
            progress={progress}
            point={p}
            centerX={cx}
            centerY={cy}
            color={accent}
          />
        ))}
      </Svg>

      {/* Labels overlay (RN text for theming/typography) */}
      {axes.map((ax, i) => (
        <View
          key={`label-${i}`}
          style={{
            position: "absolute",
            left: ax.lx - 44,
            top: ax.ly - 16,
            width: 88,
            alignItems: "center",
          }}
        >
          <Text
            typography="labelSmall"
            color={theme.text.primary + "99"}
            style={{ textAlign: "center" }}
          >
            {ax.label}
          </Text>
          <Text typography="labelMedium" color={accent}>
            {Math.round((ax.value / maxValue) * 100)}%
          </Text>
        </View>
      ))}
    </View>
  );
};

export default RadarChart;
