import json
import os
from datetime import datetime
from typing import Any
import numpy as np
import pandas as pd


def generate_backtest_html(
    df: pd.DataFrame,
    trades: list[dict[str, Any]],
    metrics: dict[str, Any],
    symbol: str,
    output_path: str,
) -> None:
    """
    Generates a standalone, fully-interactive TradingView-like HTML chart for the backtest.
    Loads Lightweight Charts from CDN and saves the result in a local file.
    """
    # Create copy to avoid modifying original
    data = df.copy()
    
    # Identify datetime column
    if "datetime" in data.columns:
        times = pd.to_datetime(data["datetime"])
    else:
        times = pd.to_datetime(data.index)
        data["datetime"] = times
        
    # Check if data is intraday
    is_intraday = False
    if len(times) > 1:
        time_diff = (times.iloc[1] - times.iloc[0]).total_seconds()
        if time_diff < 86400:
            is_intraday = True

    # Format times for Lightweight Charts
    if is_intraday:
        # UNIX timestamp in seconds
        data["time"] = times.astype(np.int64) // 10**9
    else:
        # Date string YYYY-MM-DD
        data["time"] = times.dt.strftime("%Y-%m-%d")

    # Prepare candlestick data
    ohlc_data = []
    for _, row in data.iterrows():
        ohlc_data.append({
            "time": row["time"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
        })

    # Prepare volume data
    volume_data = []
    for _, row in data.iterrows():
        volume_data.append({
            "time": row["time"],
            "value": float(row["volume"]) if pd.notna(row.get("volume")) else 0.0,
            "color": "#26a69a" if row["close"] >= row["open"] else "#ef5350"
        })

    # Prepare indicators
    sma20_data = []
    sma50_data = []
    rsi_data = []
    macd_line_data = []
    macd_signal_data = []
    macd_hist_data = []

    for _, row in data.iterrows():
        t = row["time"]
        if pd.notna(row.get("sma_20")):
            sma20_data.append({"time": t, "value": float(row["sma_20"])})
        if pd.notna(row.get("sma_50")):
            sma50_data.append({"time": t, "value": float(row["sma_50"])})
        if pd.notna(row.get("rsi_14")):
            rsi_data.append({"time": t, "value": float(row["rsi_14"])})
        if pd.notna(row.get("macd")):
            macd_line_data.append({"time": t, "value": float(row["macd"])})
        if pd.notna(row.get("macd_signal")):
            macd_signal_data.append({"time": t, "value": float(row["macd_signal"])})
        if pd.notna(row.get("macd_histogram")):
            macd_hist_data.append({
                "time": t,
                "value": float(row["macd_histogram"]),
                "color": "#26a69a" if row["macd_histogram"] >= 0 else "#ef5350"
            })

    # Prepare trade markers and lines
    # Map dates to their formatted string representation for matching
    date_to_time = {}
    for _, row in data.iterrows():
        dt_str = pd.to_datetime(row["datetime"]).strftime("%Y-%m-%d")
        date_to_time[dt_str] = row["time"]
        
    formatted_trades = []
    for idx, trade in enumerate(trades):
        entry_dt = pd.to_datetime(trade["entry_date"]).strftime("%Y-%m-%d")
        exit_dt = pd.to_datetime(trade["exit_date"]).strftime("%Y-%m-%d")
        
        entry_time = date_to_time.get(entry_dt)
        exit_time = date_to_time.get(exit_dt)
        
        if entry_time is None or exit_time is None:
            continue
            
        # Extract trade details
        formatted_trade = {
            "index": idx + 1,
            "entry_date": trade["entry_date"],
            "exit_date": trade["exit_date"],
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_price": float(trade["entry_price"]),
            "exit_price": float(trade["exit_price"]),
            "take_profit": float(trade["take_profit"]) if trade.get("take_profit") else None,
            "stop_loss": float(trade["stop_loss"]) if trade.get("stop_loss") else None,
            "return_pct": float(trade["return_pct"]),
            "exit_reason": trade.get("exit_reason", "TIMEOUT"),
            "confidence": trade.get("confidence", "N/A"),
        }
        
        # Build segment data points for the visual line of this trade
        # Find all records in our data window
        trade_indices = data[(times >= pd.to_datetime(trade["entry_date"])) & (times <= pd.to_datetime(trade["exit_date"]))]
        segment_points = []
        for _, r in trade_indices.iterrows():
            segment_points.append(r["time"])
        
        formatted_trade["segment_times"] = segment_points
        formatted_trades.append(formatted_trade)

    # Serialize to JSON strings
    ohlc_json = json.dumps(ohlc_data)
    volume_json = json.dumps(volume_data)
    sma20_json = json.dumps(sma20_data)
    sma50_json = json.dumps(sma50_data)
    rsi_json = json.dumps(rsi_data)
    macd_line_json = json.dumps(macd_line_data)
    macd_signal_json = json.dumps(macd_signal_data)
    macd_hist_json = json.dumps(macd_hist_data)
    trades_json = json.dumps(formatted_trades)
    metrics_json = json.dumps(metrics)

    # HTML/JS template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{symbol} Backtest Visualization Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: #0b0e14;
            color: #ecf0f1;
        }}
        .glass {{
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        /* Scrollbars */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: #0b0e14;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #1e293b;
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #334155;
        }}
    </style>
</head>
<body class="min-h-screen flex flex-col p-4 md:p-6 space-y-6">
    <!-- Header with Stats -->
    <header class="glass rounded-2xl p-6 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 shadow-2xl">
        <div>
            <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">{symbol} Backtest Result</h1>
            <p class="text-slate-400 text-sm mt-1">Interactive TradingView Chart & Order Logs</p>
        </div>
        
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full lg:w-auto text-center">
            <div class="bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 min-w-[120px]">
                <div class="text-xs text-slate-400 font-medium">Net Profit</div>
                <div class="text-lg font-bold id-net-profit">--</div>
            </div>
            <div class="bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 min-w-[120px]">
                <div class="text-xs text-slate-400 font-medium">Win Rate</div>
                <div class="text-lg font-bold id-win-rate">--</div>
            </div>
            <div class="bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 min-w-[120px]">
                <div class="text-xs text-slate-400 font-medium">Total Trades</div>
                <div class="text-lg font-bold id-total-trades">--</div>
            </div>
            <div class="bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 min-w-[120px]">
                <div class="text-xs text-slate-400 font-medium">Sharpe Ratio</div>
                <div class="text-lg font-bold id-sharpe">--</div>
            </div>
        </div>
    </header>

    <!-- Main Workspace -->
    <div class="grid grid-cols-1 xl:grid-cols-4 gap-6 flex-grow items-stretch">
        <!-- Chart Container -->
        <div class="xl:col-span-3 flex flex-col space-y-4">
            <div class="glass rounded-2xl p-4 shadow-2xl flex-grow flex flex-col relative min-h-[500px]">
                <div class="flex justify-between items-center mb-3">
                    <div class="flex items-center space-x-4">
                        <span class="text-sm font-semibold text-slate-300">Price Chart (1D)</span>
                        <div class="flex items-center space-x-2 text-xs">
                            <span class="inline-block w-2.5 h-2.5 bg-blue-500 rounded-full"></span>
                            <span class="text-slate-400">SMA 20</span>
                            <span class="inline-block w-2.5 h-2.5 bg-amber-500 rounded-full"></span>
                            <span class="text-slate-400">SMA 50</span>
                        </div>
                    </div>
                    <div class="text-xs text-slate-500" id="hover-legend">Move mouse over chart to view details</div>
                </div>
                <!-- Price Chart DIV -->
                <div id="chart" class="w-full flex-grow rounded-lg overflow-hidden border border-slate-900"></div>
            </div>

            <!-- Subcharts (RSI / MACD) -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div class="glass rounded-2xl p-4 shadow-2xl h-[200px] flex flex-col">
                    <span class="text-xs font-semibold text-slate-400 mb-2">RSI (14)</span>
                    <div id="rsi-chart" class="w-full flex-grow rounded-lg overflow-hidden border border-slate-900"></div>
                </div>
                <div class="glass rounded-2xl p-4 shadow-2xl h-[200px] flex flex-col">
                    <span class="text-xs font-semibold text-slate-400 mb-2">MACD</span>
                    <div id="macd-chart" class="w-full flex-grow rounded-lg overflow-hidden border border-slate-900"></div>
                </div>
            </div>
        </div>

        <!-- Sidebar (Trades Log) -->
        <div class="glass rounded-2xl p-4 shadow-2xl flex flex-col max-h-[720px] overflow-hidden">
            <h2 class="text-lg font-bold mb-3 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Execution Logs</h2>
            <div class="overflow-y-auto flex-grow rounded-xl border border-slate-800/80 bg-slate-950/20" id="trade-log-container">
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800">
                            <th class="p-3">#</th>
                            <th class="p-3">Date</th>
                            <th class="p-3">Type</th>
                            <th class="p-3 text-right">Profit</th>
                        </tr>
                    </thead>
                    <tbody id="trade-log-body">
                        <!-- Filled in JS -->
                    </tbody>
                </table>
            </div>
            
            <div class="mt-4 p-3 bg-slate-900/50 border border-slate-800/80 rounded-xl hidden" id="trade-detail-card">
                <div class="text-xs font-semibold text-slate-300 border-b border-slate-800 pb-1 mb-2 flex justify-between">
                    <span>Trade Details</span>
                    <span id="detail-confidence" class="text-[10px] px-1.5 py-0.5 rounded uppercase font-bold"></span>
                </div>
                <div class="grid grid-cols-2 gap-y-2 text-[11px] text-slate-400">
                    <div>Entry Date:</div> <div class="text-right text-slate-200" id="detail-entry-date">--</div>
                    <div>Exit Date:</div> <div class="text-right text-slate-200" id="detail-exit-date">--</div>
                    <div>Entry Price:</div> <div class="text-right text-slate-200" id="detail-entry-price">--</div>
                    <div>Exit Price:</div> <div class="text-right text-slate-200" id="detail-exit-price">--</div>
                    <div>Take Profit:</div> <div class="text-right text-green-400" id="detail-tp">--</div>
                    <div>Stop Loss:</div> <div class="text-right text-red-400" id="detail-sl">--</div>
                    <div>Exit Reason:</div> <div class="text-right text-slate-200 font-semibold" id="detail-reason">--</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Data injected from Python
        const ohlcData = {ohlc_json};
        const volumeData = {volume_json};
        const sma20Data = {sma20_json};
        const sma50Data = {sma50_json};
        const rsiData = {rsi_json};
        const macdLineData = {macd_line_json};
        const macdSignalData = {macd_signal_json};
        const macdHistData = {macd_hist_json};
        const trades = {trades_json};
        const metrics = {metrics_json};

        // Populate metrics card
        document.querySelector('.id-net-profit').innerText = (metrics.pnl.total_return * 100).toFixed(1) + '%';
        if(metrics.pnl.total_return >= 0) {{
            document.querySelector('.id-net-profit').className += ' text-green-400';
        }} else {{
            document.querySelector('.id-net-profit').className += ' text-red-400';
        }}
        document.querySelector('.id-win-rate').innerText = (metrics.volume.win_rate * 100).toFixed(1) + '%';
        document.querySelector('.id-total-trades').innerText = metrics.volume.n_trades;
        document.querySelector('.id-sharpe').innerText = metrics.risk.sharpe_ratio.toFixed(2);

        // Chart Init
        const chartElement = document.getElementById('chart');
        const chart = LightweightCharts.createChart(chartElement, {{
            layout: {{
                backgroundColor: '#0f172a',
                textColor: '#94a3b8',
            }},
            grid: {{
                vertLines: {{ color: '#1e293b' }},
                horzLines: {{ color: '#1e293b' }},
            }},
            crosshair: {{
                mode: 0,
            }},
            rightPriceScale: {{
                borderColor: '#334155',
            }},
            timeScale: {{
                borderColor: '#334155',
                timeVisible: true,
            }},
        }});

        // Main candlestick series
        const candlestickSeries = chart.addCandlestickSeries({{
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        }});
        candlestickSeries.setData(ohlcData);

        // Add Volume series
        const volumeSeries = chart.addHistogramSeries({{
            color: '#26a69a',
            priceFormat: {{
                type: 'volume',
            }},
            priceScaleId: '', // set to overlay on price chart
        }});
        volumeSeries.priceScale().applyOptions({{
            scaleMargins: {{
                top: 0.8,
                bottom: 0,
            }},
        }});
        volumeSeries.setData(volumeData);

        // Add SMAs
        const sma20Series = chart.addLineSeries({{
            color: '#3b82f6',
            lineWidth: 1.5,
            title: 'SMA 20',
        }});
        sma20Series.setData(sma20Data);

        const sma50Series = chart.addLineSeries({{
            color: '#f59e0b',
            lineWidth: 1.5,
            title: 'SMA 50',
        }});
        sma50Series.setData(sma50Data);

        // Subcharts: RSI
        const rsiChart = LightweightCharts.createChart(document.getElementById('rsi-chart'), {{
            layout: {{
                backgroundColor: '#0f172a',
                textColor: '#94a3b8',
            }},
            grid: {{
                vertLines: {{ color: '#1e293b' }},
                horzLines: {{ color: '#1e293b' }},
            }},
            rightPriceScale: {{
                borderColor: '#334155',
            }},
            timeScale: {{
                borderColor: '#334155',
            }},
        }});
        const rsiSeries = rsiChart.addLineSeries({{
            color: '#a855f7',
            lineWidth: 1.5,
        }});
        rsiSeries.setData(rsiData);
        
        // Add RSI boundary lines
        const rsiUpper = rsiChart.addLineSeries({{
            color: 'rgba(168, 85, 247, 0.3)',
            lineWidth: 1,
            lineStyle: 1,
        }});
        rsiUpper.setData(rsiData.map(d => ({{time: d.time, value: 70}})));
        const rsiLower = rsiChart.addLineSeries({{
            color: 'rgba(168, 85, 247, 0.3)',
            lineWidth: 1,
            lineStyle: 1,
        }});
        rsiLower.setData(rsiData.map(d => ({{time: d.time, value: 30}})));

        // Subcharts: MACD
        const macdChart = LightweightCharts.createChart(document.getElementById('macd-chart'), {{
            layout: {{
                backgroundColor: '#0f172a',
                textColor: '#94a3b8',
            }},
            grid: {{
                vertLines: {{ color: '#1e293b' }},
                horzLines: {{ color: '#1e293b' }},
            }},
            rightPriceScale: {{
                borderColor: '#334155',
            }},
            timeScale: {{
                borderColor: '#334155',
            }},
        }});
        const macdLineSeries = macdChart.addLineSeries({{
            color: '#2563eb',
            lineWidth: 1,
        }});
        macdLineSeries.setData(macdLineData);
        
        const macdSignalSeries = macdChart.addLineSeries({{
            color: '#ea580c',
            lineWidth: 1,
        }});
        macdSignalSeries.setData(macdSignalData);

        const macdHistSeries = macdChart.addHistogramSeries({{
            color: '#26a69a',
        }});
        macdHistSeries.setData(macdHistData);

        // Keep scales in sync
        chart.timeScale().subscribeVisibleTimeRangeChange(range => {{
            rsiChart.timeScale().setVisibleRange(range);
            macdChart.timeScale().setVisibleRange(range);
        }});
        rsiChart.timeScale().subscribeVisibleTimeRangeChange(range => {{
            chart.timeScale().setVisibleRange(range);
            macdChart.timeScale().setVisibleRange(range);
        }});
        macdChart.timeScale().subscribeVisibleTimeRangeChange(range => {{
            chart.timeScale().setVisibleRange(range);
            rsiChart.timeScale().setVisibleRange(range);
        }});

        // Sync crosshair hover values to Legend
        chart.subscribeCrosshairMove(param => {{
            if (!param.time || param.point === undefined) {{
                document.getElementById('hover-legend').innerText = 'Move mouse over chart to view details';
                return;
            }}
            const dataPoint = param.seriesData.get(candlestickSeries);
            if (dataPoint) {{
                document.getElementById('hover-legend').innerHTML = 
                    `<span class="text-slate-400">O:</span> <span class="text-slate-200 font-semibold">${{dataPoint.open.toFixed(1)}}</span> | ` +
                    `<span class="text-slate-400">H:</span> <span class="text-slate-200 font-semibold">${{dataPoint.high.toFixed(1)}}</span> | ` +
                    `<span class="text-slate-400">L:</span> <span class="text-slate-200 font-semibold">${{dataPoint.low.toFixed(1)}}</span> | ` +
                    `<span class="text-slate-400">C:</span> <span class="text-slate-200 font-semibold">${{dataPoint.close.toFixed(1)}}</span>`;
            }}
        }});

        // Setup markers (BUY / SELL arrows) on Candlestick Series
        const markers = [];
        const activeTradeSeries = []; // hold reference to temporary trade lines so we can clear/manage them
        
        trades.forEach(trade => {{
            // BUY Marker
            markers.push({{
                time: trade.entry_time,
                position: 'belowBar',
                color: '#10b981',
                shape: 'arrowUp',
                text: 'BUY @ ' + trade.entry_price.toFixed(0),
            }});
            
            // SELL Marker
            const retPctStr = (trade.return_pct * 100).toFixed(1) + '%';
            markers.push({{
                time: trade.exit_time,
                position: 'aboveBar',
                color: trade.return_pct >= 0 ? '#10b981' : '#ef4444',
                shape: 'arrowDown',
                text: `${{trade.exit_reason}} (${{retPctStr}})`,
            }});

            // Draw Stop Loss & Take Profit segment lines for each trade
            if (trade.take_profit) {{
                const tpLineSeries = chart.addLineSeries({{
                    color: 'rgba(16, 185, 129, 0.4)',
                    lineWidth: 2,
                    lineStyle: 1,
                    priceLineVisible: false,
                    lastValueVisible: false,
                }});
                const tpData = trade.segment_times.map(t => ({{ time: t, value: trade.take_profit }}));
                tpLineSeries.setData(tpData);
            }}

            if (trade.stop_loss) {{
                const slLineSeries = chart.addLineSeries({{
                    color: 'rgba(239, 68, 68, 0.4)',
                    lineWidth: 2,
                    lineStyle: 1,
                    priceLineVisible: false,
                    lastValueVisible: false,
                }});
                const slData = trade.segment_times.map(t => ({{ time: t, value: trade.stop_loss }}));
                slLineSeries.setData(slData);
            }}
        }});

        candlestickSeries.setMarkers(markers);

        // Fill Trade Log Table & Handle clicks
        const tableBody = document.getElementById('trade-log-body');
        
        trades.forEach(trade => {{
            const row = document.createElement('tr');
            const returnPct = (trade.return_pct * 100).toFixed(1) + '%';
            const colorClass = trade.return_pct >= 0 ? 'text-green-400 font-semibold' : 'text-red-400 font-semibold';
            
            row.className = 'border-b border-slate-900 hover:bg-slate-900/60 cursor-pointer transition-colors';
            row.innerHTML = `
                <td class="p-3 font-semibold text-slate-500">${{trade.index}}</td>
                <td class="p-3 text-slate-300 font-medium">${{trade.entry_date}}</td>
                <td class="p-3 text-slate-400 font-mono">${{trade.exit_reason}}</td>
                <td class="p-3 text-right ${{colorClass}}">${{returnPct}}</td>
            `;
            
            row.addEventListener('click', () => {{
                // Highlight row
                document.querySelectorAll('#trade-log-body tr').forEach(r => r.classList.remove('bg-indigo-900/20'));
                row.classList.add('bg-indigo-900/20');
                
                // Show detail card
                showTradeDetails(trade);
                
                // Zoom/Focus chart on this trade window
                focusChartOnTrade(trade);
            }});
            
            tableBody.appendChild(row);
        }});

        function showTradeDetails(trade) {{
            document.getElementById('trade-detail-card').classList.remove('hidden');
            document.getElementById('detail-entry-date').innerText = trade.entry_date;
            document.getElementById('detail-exit-date').innerText = trade.exit_date;
            document.getElementById('detail-entry-price').innerText = trade.entry_price.toLocaleString();
            document.getElementById('detail-exit-price').innerText = trade.exit_price.toLocaleString();
            document.getElementById('detail-tp').innerText = trade.take_profit ? trade.take_profit.toLocaleString() : 'N/A';
            document.getElementById('detail-sl').innerText = trade.stop_loss ? trade.stop_loss.toLocaleString() : 'N/A';
            document.getElementById('detail-reason').innerText = trade.exit_reason;
            
            const confBadge = document.getElementById('detail-confidence');
            confBadge.innerText = 'Confidence: ' + trade.confidence;
            if (trade.confidence === 'high') {{
                confBadge.className = 'text-[10px] px-1.5 py-0.5 rounded font-bold bg-green-500/20 text-green-400 uppercase';
            }} else if (trade.confidence === 'medium') {{
                confBadge.className = 'text-[10px] px-1.5 py-0.5 rounded font-bold bg-yellow-500/20 text-yellow-400 uppercase';
            }} else {{
                confBadge.className = 'text-[10px] px-1.5 py-0.5 rounded font-bold bg-red-500/20 text-red-400 uppercase';
            }}
        }}

        function focusChartOnTrade(trade) {{
            // Find margin indexes to frame the trade nicely
            const entryTime = trade.entry_time;
            const exitTime = trade.exit_time;
            
            // Set scale visible range (approx 10 candles before entry to 10 candles after exit)
            // Or just frame the trade times
            chart.timeScale().setVisibleRange({{
                from: typeof entryTime === 'number' ? entryTime - (60 * 60 * 24 * 10) : getOffsetDateString(trade.entry_date, -10),
                to: typeof exitTime === 'number' ? exitTime + (60 * 60 * 24 * 10) : getOffsetDateString(trade.exit_date, 10),
            }});
        }}

        function getOffsetDateString(dateStr, offsetDays) {{
            const date = new Date(dateStr);
            date.setDate(date.getDate() + offsetDays);
            return date.toISOString().split('T')[0];
        }}
        
        // Auto resize charts on window resize
        window.addEventListener('resize', () => {{
            chart.resize(chartElement.clientWidth, chartElement.clientHeight);
            rsiChart.resize(document.getElementById('rsi-chart').clientWidth, document.getElementById('rsi-chart').clientHeight);
            macdChart.resize(document.getElementById('macd-chart').clientWidth, document.getElementById('macd-chart').clientHeight);
        }});
    </script>
</body>
</html>
"""

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the output HTML file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Visualization saved successfully to {output_path}")
