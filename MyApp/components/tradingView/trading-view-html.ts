import { LIGHTWEIGHT_CHARTS_SCRIPT } from './lightweight-charts-inline';

export const TradingViewHtml = /*html*/ `
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,minimum-scale=1.0" />
    <title>Lightweight Charts™</title>


    <style>
        body {
            overflow: hidden;
            overscroll-behavior: none;
            padding: 0;
            margin: 0;
        }

        #tv-attr-logo {
            pointer-events: none !important;
        }

        .tooltip {
            position: absolute;
            display: none;
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            pointer-events: none;
            z-index: 1000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 10px;
            color: #333333;
            min-width: 120px;
        }

        .tooltip-date {
            display: flex;
            align-items: center;
            margin-bottom: 2px;
        }

        .tooltip-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #3395FF;
            margin-right: 4px;
            flex-shrink: 0;
        }

        .tooltip-date-text {
            font-size: 10px;
            color: #333333;
        }

        .tooltip-price-row {
            display: flex;
            justify-content: flex-start;
            margin-bottom: 2px;
        }

        .tooltip-price-label {
            color: #666666;
            font-size: 10px;
            min-width: 80px;
        }

        .tooltip-price-value {
            color: #333333;
            font-size: 10px;
            font-weight: 500;
            text-align: left;
        }

        .tooltip-volume-row {
            display: flex;
            justify-content: flex-start;
            margin-top: 2px;
        }

        .tooltip-volume-row:last-child {
            margin-bottom: 0;
        }

        .tooltip-volume-label {
            color: #666666;
            font-size: 10px;
            min-width: 80px;
        }

        .tooltip-volume-value {
            color: #333333;
            font-size: 10px;
            font-weight: 500;
            text-align: right;
        }

    </style>
</head>

<body>
    <div id="container" style="position: absolute; width: 100%; height: 100%">
    </div>
    <script type="text/javascript">
        ${LIGHTWEIGHT_CHARTS_SCRIPT}
    </script>
</body>

</html>
`;
