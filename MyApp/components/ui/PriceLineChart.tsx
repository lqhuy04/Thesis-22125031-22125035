import React from "react";
import { CartesianChart, Line } from "victory-native";

const DATA = [
  { x: 1, y: 2 },
  { x: 2, y: 5 },
  { x: 3, y: 3 },
  { x: 4, y: 8 },
  { x: 5, y: 7 },
  { x: 6, y: 12 },
  { x: 7, y: 10 },
  { x: 8, y: 15 },
];

const  PriceLineGraph = () => {
  return (
    <CartesianChart data={DATA} xKey="x" yKeys={["y"]}>
      {({ points }) => (
        //👇 pass a PointsArray to the Line component, as well as options.
        <Line
          points={points.y}
          color="red"
          strokeWidth={3}
          animate={{ type: "timing", duration: 300 }}
        />
      )}
    </CartesianChart>
  );
}

export default PriceLineGraph;
