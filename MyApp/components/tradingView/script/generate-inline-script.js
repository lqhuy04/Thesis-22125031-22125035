#!/usr/bin/env node
// Generate a TypeScript file with the lightweight-charts script inlined
const fs = require("fs");
const path = require("path");

const scriptPath = path.resolve(
  __dirname,
  "../lib/lightweight-charts.standalone.production.js",
);
const outputPath = path.resolve(__dirname, "../lightweight-charts-inline.ts");

console.log("Reading script from:", scriptPath);
const scriptContent = fs.readFileSync(scriptPath, "utf8");

const tsContent = `// Auto-generated file - do not edit manually
// Generated from: src/assets/cdnjs/lightweight-charts.standalone.production.js
// To regenerate: node scripts/generate-inline-script.js

export const LIGHTWEIGHT_CHARTS_SCRIPT = ${JSON.stringify(scriptContent)};
`;

fs.writeFileSync(outputPath, tsContent, "utf8");
console.log("Generated:", outputPath);
console.log("Script size:", Math.round(scriptContent.length / 1024), "KB");
