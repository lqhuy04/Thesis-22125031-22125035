import React, { useState } from "react";
import { WebView, WebViewMessageEvent } from "react-native-webview";

interface Props {
  /** Mã LaTeX thuần (đã bỏ delimiter). */
  latex: string;
  /** Màu chữ của công thức. */
  color: string;
  /** true: công thức block (căn giữa), false: inline (căn trái). */
  display?: boolean;
}

const KATEX_VERSION = "0.16.22";

const buildHtml = (latex: string, color: string, display: boolean) => `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.min.css" />
<script defer src="https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.min.js"></script>
<style>
  html, body { margin: 0; padding: 0; background-color: transparent; }
  /* Cuộn ngang cho công thức dài, để overflow dọc hiển thị đầy đủ (tránh cắt mẫu số). */
  #wrap {
    ${display ? "text-align: center;" : ""}
    overflow-x: auto;
    overflow-y: visible;
    -webkit-overflow-scrolling: touch;
  }
  #m { display: inline-block; color: ${color}; font-size: 16px; padding: 2px 0; }
  .katex { white-space: nowrap; }
  .katex-display { margin: 0; }
</style>
</head>
<body>
<div id="wrap"><span id="m"></span></div>
<script>
  var LATEX = ${JSON.stringify(latex)};
  function sendH() {
    var el =
      document.querySelector('.katex-display') ||
      document.querySelector('.katex') ||
      document.getElementById('m');
    // +4px buffer cho phần tử nhô trên/dưới đường baseline (tử số/mẫu số).
    var h = Math.ceil(el.getBoundingClientRect().height) + 4;
    if (window.ReactNativeWebView) window.ReactNativeWebView.postMessage(String(h));
  }
  function go() {
    try {
      katex.render(LATEX, document.getElementById('m'), { displayMode: ${display}, throwOnError: false });
    } catch (e) {
      document.getElementById('m').textContent = LATEX;
    }
    var f = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
    f.then(function () { setTimeout(sendH, 0); setTimeout(sendH, 300); });
  }
  function boot() { if (window.katex) { go(); } else { setTimeout(boot, 30); } }
  boot();
</script>
</body>
</html>`;

const KatexWebView = ({ latex, color, display = false }: Props) => {
  const [height, setHeight] = useState(display ? 60 : 26);

  const onMessage = (e: WebViewMessageEvent) => {
    const h = Number(e.nativeEvent.data);
    if (h && Math.abs(h - height) > 1) setHeight(h);
  };

  return (
    <WebView
      originWhitelist={["*"]}
      source={{ html: buildHtml(latex, color, display) }}
      onMessage={onMessage}
      scrollEnabled={false}
      showsHorizontalScrollIndicator={false}
      showsVerticalScrollIndicator={false}
      androidLayerType="hardware"
      style={{
        height,
        backgroundColor: "transparent",
        marginVertical: display ? 6 : 2,
      }}
    />
  );
};

export default React.memo(KatexWebView);
