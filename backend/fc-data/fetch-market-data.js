const config = require('./config.js');
const client = require('./ssi-fcdata');
const axios = require('axios');
const fs = require('fs');

/**
 * Script lấy dữ liệu OHLC từ SSI API theo các timeframe
 * Mỗi timeframe là một object riêng trong file JSON
 */

// ==================== CẤU HÌNH ====================
const CONFIG = {
  SYMBOL: "VNM",           // Mã cổ phiếu (VNM, VIC, FPT, HPG, VCB...)
  INDEX_ID: "VN30",        // Mã chỉ số (VN30, VNINDEX, HNX30...)
  
  // Cho Daily data (1D, 1W, 1M) - có thể lấy dài hạn
  DAILY_FROM: "01/01/2024",
  DAILY_TO: "16/10/2024",
  
  // Cho Intraday data (1M, 5M, 15M, 1H) - giới hạn 30 ngày
  INTRADAY_FROM: "16/09/2024",
  INTRADAY_TO: "16/10/2024",
};

let accessToken = "";

// ==================== HÀM LẤY ACCESS TOKEN ====================
async function getAccessToken() {
  try {
    const response = await axios.post(
      config.market.ApiUrl + client.api.GET_ACCESS_TOKEN,
      {
        consumerID: config.market.ConsumerId,
        consumerSecret: config.market.ConsumerSecret,
      }
    );

    if (response.data.status === 200) {
      accessToken = "Bearer " + response.data.data.accessToken;
      console.log("✅ Lấy access token thành công");
      return accessToken;
    } else {
      throw new Error(response.data.message);
    }
  } catch (error) {
    console.error("❌ Lỗi khi lấy access token:", error.message);
    throw error;
  }
}

// ==================== HÀM LẤY DỮ LIỆU ====================

async function getDailyOHLC(symbol, fromDate, toDate) {
  try {
    const response = await axios.get(
      config.market.ApiUrl + client.api.GET_DAILY_OHLC,
      {
        headers: { Authorization: accessToken },
        params: {
          "lookupRequest.symbol": symbol,
          "lookupRequest.fromDate": fromDate,
          "lookupRequest.toDate": toDate,
          "lookupRequest.pageIndex": 1,
          "lookupRequest.pageSize": 5000,
          "lookupRequest.ascending": true,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("❌ Lỗi getDailyOHLC:", error.message);
    return { data: null, status: "Error", message: error.message };
  }
}

async function getIntradayOHLC(symbol, fromDate, toDate) {
  try {
    const response = await axios.get(
      config.market.ApiUrl + client.api.GET_INTRADAY_OHLC,
      {
        headers: { Authorization: accessToken },
        params: {
          "lookupRequest.symbol": symbol,
          "lookupRequest.fromDate": fromDate,
          "lookupRequest.toDate": toDate,
          "lookupRequest.pageIndex": 1,
          "lookupRequest.pageSize": 5000,
          "lookupRequest.ascending": true,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("❌ Lỗi getIntradayOHLC:", error.message);
    return { data: null, status: "Error", message: error.message };
  }
}

async function getDailyIndex(indexId, fromDate, toDate) {
  try {
    const response = await axios.get(
      config.market.ApiUrl + client.api.GET_DAILY_INDEX,
      {
        headers: { Authorization: accessToken },
        params: {
          "lookupRequest.indexId": indexId,
          "lookupRequest.fromDate": fromDate,
          "lookupRequest.toDate": toDate,
          "lookupRequest.pageIndex": 1,
          "lookupRequest.pageSize": 5000,
          "lookupRequest.ascending": true,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("❌ Lỗi getDailyIndex:", error.message);
    return { data: null, status: "Error", message: error.message };
  }
}

async function getDailyStockPrice(symbol, fromDate, toDate) {
  try {
    const response = await axios.get(
      config.market.ApiUrl + client.api.GET_DAILY_STOCKPRICE,
      {
        headers: { Authorization: accessToken },
        params: {
          "lookupRequest.symbol": symbol,
          "lookupRequest.fromDate": fromDate,
          "lookupRequest.toDate": toDate,
          "lookupRequest.market": "",
          "lookupRequest.pageIndex": 1,
          "lookupRequest.pageSize": 5000,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("❌ Lỗi getDailyStockPrice:", error.message);
    return { data: null, status: "Error", message: error.message };
  }
}

async function getSecuritiesList(market = "HOSE", pageIndex = 1, pageSize = 100) {
  try {
    const response = await axios.get(
      config.market.ApiUrl + client.api.GET_SECURITIES_LIST,
      {
        headers: { Authorization: accessToken },
        params: {
          "lookupRequest.market": market,
          "lookupRequest.pageIndex": pageIndex,
          "lookupRequest.pageSize": pageSize,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("❌ Lỗi getSecuritiesList:", error.message);
    return { data: null, status: "Error", message: error.message };
  }
}

async function getSecuritiesDetails(symbol) {
  try {
    const response = await axios.get(
      config.market.ApiUrl + client.api.GET_SECURITIES_DETAILs,
      {
        headers: { Authorization: accessToken },
        params: {
          "lookupRequest.symbol": symbol,
          "lookupRequest.market": "",
          "lookupRequest.pageIndex": 1,
          "lookupRequest.pageSize": 100,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("❌ Lỗi getSecuritiesDetails:", error.message);
    return { data: null, status: "Error", message: error.message };
  }
}

// ==================== HÀM CHÍNH ====================
async function main() {
  console.log("🚀 BẮT ĐẦU LẤY DỮ LIỆU TỪ SSI FASTCONNECT API\n");
  console.log(`📊 Mã cổ phiếu: ${CONFIG.SYMBOL}`);
  console.log(`📈 Chỉ số: ${CONFIG.INDEX_ID}`);
  console.log(`📅 Daily: ${CONFIG.DAILY_FROM} → ${CONFIG.DAILY_TO}`);
  console.log(`⏱️  Intraday: ${CONFIG.INTRADAY_FROM} → ${CONFIG.INTRADAY_TO}\n`);

  try {
    // Lấy access token
    await getAccessToken();

    // ==================== CẤU TRÚC DỮ LIỆU ====================
    const result = {
      metadata: {
        symbol: CONFIG.SYMBOL,
        indexId: CONFIG.INDEX_ID,
        generatedAt: new Date().toISOString(),
        dateRanges: {
          daily: { from: CONFIG.DAILY_FROM, to: CONFIG.DAILY_TO },
          intraday: { from: CONFIG.INTRADAY_FROM, to: CONFIG.INTRADAY_TO },
        },
      },

      // ===== TIMEFRAMES =====
      timeframes: {
        // INTRADAY TIMEFRAMES (từ IntradayOHLC API)
        "1M": {
          name: "1 Minute",
          interval: "1 minute",
          type: "intraday",
          description: "Dữ liệu nến 1 phút (intraday)",
          apiSource: "GET_INTRADAY_OHLC",
          dataStructure: {
            fields: ["Symbol", "TradingDate", "Time", "Open", "High", "Low", "Close", "Volume", "Value"],
            example: "Mỗi record chứa giá OHLC của 1 phút giao dịch",
          },
          data: null,
          recordCount: 0,
        },

        "5M": {
          name: "5 Minutes",
          interval: "5 minutes",
          type: "intraday",
          description: "Dữ liệu nến 5 phút (cần xử lý từ 1M)",
          apiSource: "Calculated from 1M data",
          note: "SSI API không cung cấp sẵn, cần aggregate từ 1M data",
          data: null,
          recordCount: 0,
        },

        "15M": {
          name: "15 Minutes",
          interval: "15 minutes",
          type: "intraday",
          description: "Dữ liệu nến 15 phút (cần xử lý từ 1M)",
          apiSource: "Calculated from 1M data",
          note: "SSI API không cung cấp sẵn, cần aggregate từ 1M data",
          data: null,
          recordCount: 0,
        },

        "1H": {
          name: "1 Hour",
          interval: "1 hour",
          type: "intraday",
          description: "Dữ liệu nến 1 giờ (cần xử lý từ 1M)",
          apiSource: "Calculated from 1M data",
          note: "SSI API không cung cấp sẵn, cần aggregate từ 1M data",
          data: null,
          recordCount: 0,
        },

        // DAILY+ TIMEFRAMES (từ DailyOHLC API)
        "1D": {
          name: "1 Day",
          interval: "1 day",
          type: "daily",
          description: "Dữ liệu nến ngày",
          apiSource: "GET_DAILY_OHLC",
          dataStructure: {
            fields: ["Symbol", "Market", "TradingDate", "Open", "High", "Low", "Close", "Volume", "Value"],
            example: "Mỗi record chứa giá OHLC của 1 ngày giao dịch",
          },
          data: null,
          recordCount: 0,
        },

        "1W": {
          name: "1 Week",
          interval: "1 week",
          type: "weekly",
          description: "Dữ liệu nến tuần (cần xử lý từ 1D)",
          apiSource: "Calculated from 1D data",
          note: "SSI API không cung cấp sẵn, cần aggregate từ 1D data",
          data: null,
          recordCount: 0,
        },

        "1M_period": {
          name: "1 Month",
          interval: "1 month",
          type: "monthly",
          description: "Dữ liệu nến tháng (cần xử lý từ 1D)",
          apiSource: "Calculated from 1D data",
          note: "SSI API không cung cấp sẵn, cần aggregate từ 1D data",
          data: null,
          recordCount: 0,
        },
      },

      // ===== DỮ LIỆU BỔ SUNG =====
      additionalData: {
        // Thông tin giá chi tiết theo ngày
        dailyStockPrice: {
          description: "Giá cổ phiếu theo ngày (chi tiết hơn DailyOHLC)",
          apiSource: "GET_DAILY_STOCKPRICE",
          data: null,
          recordCount: 0,
        },

        // Dữ liệu chỉ số thị trường
        indexData: {
          description: "Dữ liệu chỉ số thị trường theo ngày",
          apiSource: "GET_DAILY_INDEX",
          data: null,
          recordCount: 0,
        },

        // Thông tin cổ phiếu
        securityDetails: {
          description: "Thông tin chi tiết về mã cổ phiếu",
          apiSource: "GET_SECURITIES_DETAILs",
          data: null,
        },
      },
    };

    // ==================== LẤY DỮ LIỆU TỪNG LOẠI ====================

    console.log("📥 1/6 - Đang lấy Intraday OHLC (1M)...");
    const intradayData = await getIntradayOHLC(
      CONFIG.SYMBOL,
      CONFIG.INTRADAY_FROM,
      CONFIG.INTRADAY_TO
    );
    result.timeframes["1M"].data = intradayData;
    result.timeframes["1M"].recordCount = intradayData.data?.length || 0;
    console.log(`   ✅ ${result.timeframes["1M"].recordCount} records\n`);

    console.log("📥 2/6 - Đang lấy Daily OHLC (1D)...");
    const dailyData = await getDailyOHLC(
      CONFIG.SYMBOL,
      CONFIG.DAILY_FROM,
      CONFIG.DAILY_TO
    );
    result.timeframes["1D"].data = dailyData;
    result.timeframes["1D"].recordCount = dailyData.data?.length || 0;
    console.log(`   ✅ ${result.timeframes["1D"].recordCount} records\n`);

    console.log("📥 3/6 - Đang lấy Daily Stock Price...");
    const stockPriceData = await getDailyStockPrice(
      CONFIG.SYMBOL,
      CONFIG.DAILY_FROM,
      CONFIG.DAILY_TO
    );
    result.additionalData.dailyStockPrice.data = stockPriceData;
    result.additionalData.dailyStockPrice.recordCount = stockPriceData.data?.length || 0;
    console.log(`   ✅ ${result.additionalData.dailyStockPrice.recordCount} records\n`);

    console.log("📥 4/6 - Đang lấy Daily Index...");
    const indexData = await getDailyIndex(
      CONFIG.INDEX_ID,
      CONFIG.DAILY_FROM,
      CONFIG.DAILY_TO
    );
    result.additionalData.indexData.data = indexData;
    result.additionalData.indexData.recordCount = indexData.data?.length || 0;
    console.log(`   ✅ ${result.additionalData.indexData.recordCount} records\n`);

    console.log("📥 5/6 - Đang lấy Securities Details...");
    const securityDetails = await getSecuritiesDetails(CONFIG.SYMBOL);
    result.additionalData.securityDetails.data = securityDetails;
    console.log(`   ✅ Done\n`);

    // ==================== LƯU FILE ====================
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const outputFile = `./market-data-${CONFIG.SYMBOL}-${timestamp}.json`;
    
    fs.writeFileSync(outputFile, JSON.stringify(result, null, 2), "utf8");

    // ==================== THỐNG KÊ ====================
    console.log("\n" + "=".repeat(60));
    console.log("✅ HOÀN THÀNH!");
    console.log("=".repeat(60));
    console.log(`📁 File: ${outputFile}`);
    console.log(`📊 Symbol: ${CONFIG.SYMBOL}`);
    console.log("\n📈 TIMEFRAMES:");
    console.log(`   • 1M (Intraday):  ${result.timeframes["1M"].recordCount} records`);
    console.log(`   • 1D (Daily):     ${result.timeframes["1D"].recordCount} records`);
    console.log(`   • 5M, 15M, 1H:    Cần tính từ 1M data`);
    console.log(`   • 1W, 1M_period:  Cần tính từ 1D data`);
    console.log("\n📊 ADDITIONAL DATA:");
    console.log(`   • Stock Price:    ${result.additionalData.dailyStockPrice.recordCount} records`);
    console.log(`   • Index Data:     ${result.additionalData.indexData.recordCount} records`);
    console.log(`   • Security Info:  Available`);
    console.log("\n💡 GHI CHÚ:");
    console.log("   - Intraday OHLC giới hạn 30 ngày");
    console.log("   - Daily OHLC có thể lấy dài hạn");
    console.log("   - Timeframes 5M, 15M, 1H, 1W, 1M cần aggregate ở frontend");
    console.log("=".repeat(60) + "\n");

  } catch (error) {
    console.error("\n❌ LỖI:", error.message);
    process.exit(1);
  }
}

// Chạy script
main();
