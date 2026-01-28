import { baseUrl } from "./base";

export type Content = {
  type: "text" | "image";
  url?: string;
  content?: string;
};

export type New = {
  id: string;
  title: string;
  link: string;
  stock_symbol: string;
  description: string;
  time: string;
  image_url: string;
  published_at: string;
  content: {
    blocks: Content[];
  };
  source: string;
};

export const fetchNews = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const response = await fetch(baseUrl + `news?stock_symbol=${symbol}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();
    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data?.items as New[],
      };
    }

    return {
      status: false,
      data: [],
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
    };
  }
};

//------------------------------------------------------------
export type FundamentalAnalysisIndexes = {
  pe_ratio: number; // P/E
  pb_ratio: number; // P/B
  eps: number; // EPS
  market_cap_billion: number; // Vốn hóa (tỷ đồng)
  shares_outstanding_million: number; // Khối lượng lưu hành (triệu cổ phiếu)
  roe: number; // ROE
  gross_margin: number; // Biên lợi nhuận gộp
  revenue_yoy: number; // Doanh thu YoY
  eps_yoy: number; // EPS YoY
  debt_to_equity: number; // Nợ/VCSH
  current_ratio: number; // Hệ số thanh toán hiện hành
  fcf: number; // FCF
  ev_ebitda: number; // EV/EBITDA
};

export const fetchFundamentalAnalysisIndexes = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: FundamentalAnalysisIndexes | null;
}> => {
  try {
    const response = await fetch(baseUrl + `api/financial/analysis/${symbol}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();
    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data?.metrics as FundamentalAnalysisIndexes,
      };
    }
    return {
      status: false,
      data: null,
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
    };
  }
};

//------------------------------------------------------------
export type StockData = {
  Symbol: string;
  TradingDate: string;
  Time: string;
  Open: string;
  High: string;
  Low: string;
  Close: string;
  Volume: string;
  Value: string;
};

export const fetchStockData = async (
  symbol: string,
  timeframe: "1D" | "1W" | "1M" | "1Y" | "5Y",
): Promise<{
  status: boolean;
  data: StockData[];
}> => {
  try {
    const response = await fetch(
      baseUrl +
        `market-data/stock-price/timeframe/${symbol}?timeframe=${timeframe}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      },
    );

    const result = await response.json();
    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data?.data as StockData[],
      };
    }

    return {
      status: false,
      data: [],
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
    };
  }
};

//------------------------------------------------------------
export type AnalysisData = {
  symbol: string,
  fundamental_analysis: string,
  technical_analysis: string,
  final_report: string,
}

export const getAnalysis = async (
  symbol: string,
  fundamentalAnalysisInput: string,
  technicalAnalysisInput: string,
): Promise<{
  status: boolean;
  data: AnalysisData | null;
}> => {
  try {
    const response = {
      "data": {
        "symbol": "VNM",
        "fundamental_analysis": "Dưới đây là phân tích các chỉ số tài chính cơ bản cho cổ phiếu VNM dựa trên dữ liệu bạn cung cấp:\n\n---\n\n**Phân tích các chỉ số tài chính cơ bản của VNM**\n\n**1. Định giá (Valuation)**\n\n*   **P/E (Price/Earnings Ratio) = 14.54:**\n    *   **Đánh giá:** Mức P/E 14.54 cho thấy nhà đầu tư sẵn sàng trả 14.54 đồng cho mỗi đồng lợi nhuận mà VNM tạo ra. Đây là một mức P/E **tương đối hợp lý** cho một công ty hàng tiêu dùng thiết yếu (FMCG) lớn, dẫn đầu thị trường và có dòng tiền ổn định. So với mặt bằng chung thị trường Việt Nam (thường cao hơn) và ngành FMCG (thường có P/E cao hơn do tính ổn định), mức này không quá đắt đỏ nhưng cũng không quá rẻ. Cần so sánh thêm với P/E trung bình ngành và P/E lịch sử của VNM để có đánh giá chính xác hơn.\n*   **P/B (Price/Book Ratio) = 3.38:**\n    *   **Đánh giá:** Mức P/B 3.38 cho thấy thị trường đang định giá VNM cao gấp 3.38 lần giá trị sổ sách của công ty. Đây là một mức P/B **khá cao**, thường đi kèm với các công ty có khả năng sinh lời trên vốn chủ sở hữu (ROE) vượt trội và có lợi thế cạnh tranh bền vững (thương hiệu mạnh, thị phần lớn). Điều này cho thấy thị trường đánh giá cao tài sản vô hình và khả năng tạo ra lợi nhuận của VNM.\n*   **EV/EBITDA (Enterprise Value/EBITDA) = 11.11:**\n    *   **Đánh giá:** EV/EBITDA là một chỉ số định giá tốt, đặc biệt khi so sánh các công ty trong cùng ngành có cấu trúc vốn khác nhau. Mức 11.11 là **tương đối hợp lý đến hơi cao** cho một doanh nghiệp có quy mô và sự ổn định như VNM. Nó cho thấy giá trị doanh nghiệp bao gồm cả nợ đang được định giá khoảng 11 lần lợi nhuận trước lãi vay, thuế và khấu hao.\n\n*   **Nhận định tổng quan về Định giá:** VNM có vẻ đang được định giá ở mức **hợp lý đến hơi cao** trên thị trường, phản ánh vị thế dẫn đầu, khả năng sinh lời tốt và sự ổn định của công ty. Các chỉ số này không cho thấy công ty đang bị định giá quá thấp (undervalued) một cách rõ ràng.\n\n**2. Khả năng sinh lời (Profitability)**\n\n*   **ROE (Return on Equity) = 25.96%:**\n    *   **Đánh giá:** ROE 25.96% là một con số **rất ấn tượng và xuất sắc**. Điều này cho thấy VNM đang sử dụng vốn chủ sở hữu của cổ đông cực kỳ hiệu quả để tạo ra lợi nhuận. Cứ 100 đồng vốn chủ sở hữu, công ty tạo ra gần 26 đồng lợi nhuận ròng. Đây là một điểm mạnh lớn của VNM.\n*   **Gross Margin (Biên lợi nhuận gộp) = 41.42%:**\n    *   **Đánh giá:** Biên lợi nhuận gộp 41.42% là một mức **rất tốt** đối với một công ty sản xuất hàng tiêu dùng quy mô lớn. Nó cho thấy VNM có khả năng kiểm soát chi phí sản xuất tốt và/hoặc có sức mạnh định giá sản phẩm (pricing power) nhờ thương hiệu mạnh, giúp công ty giữ được tỷ lệ lợi nhuận cao sau khi trừ đi giá vốn hàng bán.\n*   **Net Margin (Biên lợi nhuận ròng) = None:**\n    *   **Đánh giá:** Không có dữ liệu để đánh giá.\n*   **ROA (Return on Assets) = None:**\n    *   **Đánh giá:** Không có dữ liệu để đánh giá.\n\n*   **Nhận định tổng quan về Khả năng sinh lời:** Mặc dù thiếu dữ liệu về Net Margin và ROA, ROE và Gross Margin đã cho thấy VNM là một công ty có **khả năng sinh lời vượt trội và hiệu quả hoạt động rất cao**. Đây là một trong những điểm mạnh cốt lõi của VNM.\n\n**3. Tăng trưởng (Growth)**\n\n*   **Revenue YoY (Tăng trưởng doanh thu so với cùng kỳ) = 2.34%:**\n    *   **Đánh giá:** Mức tăng trưởng doanh thu 2.34% là **khá khiêm tốn**. Đối với một công ty đã đạt quy mô lớn và thị phần thống lĩnh như VNM, việc duy trì mức tăng trưởng doanh thu cao là một thách thức. Mức này cho thấy VNM đang trong giai đoạn tăng trưởng chậm lại, tập trung vào củng cố thị phần và hiệu quả hoạt động hơn là mở rộng nhanh chóng.\n*   **EPS YoY (Tăng trưởng lợi nhuận trên mỗi cổ phiếu so với cùng kỳ) = 5.95%:**\n    *   **Đánh giá:** Mức tăng trưởng EPS 5.95% **tốt hơn so với tăng trưởng doanh thu**. Điều này có thể đến từ việc VNM đã cải thiện hiệu quả hoạt động, tối ưu hóa chi phí hoặc thực hiện mua lại cổ phiếu quỹ (nếu có), giúp lợi nhuận trên mỗi cổ phiếu tăng nhanh hơn doanh thu. Đây là một dấu hiệu tích cực cho cổ đông.\n*   **Profit YoY (Tăng trưởng lợi nhuận ròng so với cùng kỳ) = None:**\n    *   **Đánh giá:** Không có dữ liệu để đánh giá.\n\n*   **Nhận định tổng quan về Tăng trưởng:** VNM đang cho thấy mức tăng trưởng doanh thu **ổn định nhưng chậm**, phù hợp với một doanh nghiệp lớn và trưởng thành. Tuy nhiên, tăng trưởng EPS tốt hơn cho thấy công ty đang tập trung vào việc nâng cao hiệu quả và giá trị cho cổ đông.\n\n**4. Tình hình tài chính (Financial Health)**\n\n*   **Debt to Equity (Nợ trên vốn chủ sở hữu) = 0.52:**\n    *   **Đánh giá:** Tỷ lệ Nợ/Vốn chủ sở hữu là 0.52 là một con số **rất khỏe mạnh**. Điều này cho thấy VNM chủ yếu dựa vào vốn chủ sở hữu để tài trợ cho hoạt động kinh doanh, với mức nợ phải trả tương đối thấp. Tỷ lệ này thấp hơn nhiều so với 1.0, cho thấy rủi ro tài chính của công ty rất thấp và khả năng thanh toán nợ tốt.\n*   **Current Ratio (Tỷ lệ thanh toán hiện hành) = 2.03:**\n    *   **Đánh giá:** Tỷ lệ thanh toán hiện hành là 2.03 là một con số **rất tốt và lành mạnh**. Điều này có nghĩa là tài sản ngắn hạn của VNM gấp hơn 2 lần nợ ngắn hạn, cho thấy công ty có khả năng cao trong việc thanh toán các khoản nợ đến hạn trong ngắn hạn mà không gặp khó khăn về thanh khoản.\n\n*   **Nhận định tổng quan về Tình hình tài chính:** VNM có một **tình hình tài chính cực kỳ vững chắc và an toàn**, với mức nợ thấp và khả năng thanh khoản cao. Điều này mang lại sự ổn định và linh hoạt cho công ty trong các hoạt động kinh doanh và đối phó với những biến động thị trường.\n\n**5. Dòng tiền tự do (Free Cash Flow - FCF)**\n\n*   **FCF (Dòng tiền tự do) = 5946.85 (tỷ đồng, giả định):**\n    *   **Đánh giá:** Mức FCF 5946.85 tỷ đồng là một con số **rất lớn và ấn tượng**. Dòng tiền tự do dương và lớn cho thấy VNM không chỉ tạo ra lợi nhuận trên giấy tờ mà còn tạo ra lượng tiền mặt đáng kể sau khi đã trừ đi các chi phí hoạt động và đầu tư tài sản cố định. Điều này mang lại cho công ty sự linh hoạt cao trong việc chi trả cổ tức, mua lại cổ phiếu, giảm nợ hoặc đầu tư vào các dự án mới mà không cần phụ thuộc nhiều vào tài trợ bên ngoài. Đây là một chỉ số cực kỳ quan trọng và tích cực.\n\n---\n\n**Nhận định tổng quan về sức khỏe tài chính của VNM:**\n\nVNM đang thể hiện là một công ty có **sức khỏe tài chính rất mạnh mẽ và vững chắc**.\n\n*   **Điểm mạnh nổi bật:**\n    *   **Khả năng sinh lời vượt trội:** ROE và Gross Margin cực kỳ cao cho thấy hiệu quả hoạt động và quản lý chi phí xuất sắc.\n    *   **Tình hình tài chính an toàn:** Tỷ lệ Nợ/Vốn chủ sở hữu thấp và Tỷ lệ thanh toán hiện hành cao đảm bảo sự ổn định và thanh khoản.\n    *   **Dòng tiền dồi dào:** FCF lớn cung cấp sự linh hoạt tài chính cao cho công ty.\n*   **Điểm cần lưu ý:**\n    *   **Tăng trưởng doanh thu khiêm tốn:** Phản ánh giai đoạn trưởng thành của doanh nghiệp. Tuy nhiên, tăng trưởng EPS vẫn tốt cho thấy nỗ lực nâng cao hiệu quả.\n    *   **Định giá hợp lý đến hơi cao:** Thị trường đã phản ánh phần lớn các yếu tố tích cực của VNM vào giá cổ phiếu.\n\n**Kết luận:** VNM là một doanh nghiệp \"blue-chip\" điển hình với nền tảng tài chính cực kỳ vững chắc, khả năng sinh lời cao và dòng tiền dồi dào. Mặc dù tốc độ tăng trưởng doanh thu đã chậm lại, công ty vẫn tạo ra giá trị tốt cho cổ đông thông qua việc tối ưu hóa lợi nhuận trên mỗi cổ phiếu và duy trì một bảng cân đối kế toán lành mạnh. VNM có thể được xem là một khoản đầu tư ổn định, an toàn, phù hợp cho những nhà đầu tư tìm kiếm sự ổn định và cổ tức, hơn là tăng trưởng đột phá.",
        "technical_analysis": "Dưới đây là phân tích kỹ thuật cho cổ phiếu VNM dựa trên dữ liệu giá gần đây:\n\n**1. Xu hướng giá (Trend) trong giai đoạn này:**\n\n*   **Giai đoạn đầu (29/12/2025 - 05/01/2026):** VNM có xu hướng giảm nhẹ, từ 62,100 VND xuống mức thấp nhất 60,300 VND (giá đóng cửa) vào ngày 05/01/2026.\n*   **Giai đoạn tăng mạnh (06/01/2026 - 20/01/2026):** Cổ phiếu VNM đã có một đợt tăng giá rất ấn tượng và mạnh mẽ. Từ mức 60,300 VND, giá đã liên tục bứt phá và đạt đỉnh 73,400 VND (giá đóng cửa) vào ngày 20/01/2026, thậm chí chạm mức 75,500 VND trong phiên. Đây là một xu hướng tăng rõ ràng và mạnh mẽ.\n*   **Giai đoạn điều chỉnh/tích lũy (21/01/2026 - 28/01/2026):** Sau đợt tăng nóng, VNM bước vào giai đoạn điều chỉnh. Giá giảm từ 73,400 VND xuống 67,200 VND vào ngày 23/01/2026, sau đó có sự hồi phục nhẹ và dao động quanh vùng 67,000 - 68,900 VND. Xu hướng ngắn hạn trong giai đoạn này là điều chỉnh giảm/đi ngang.\n\n**Tóm lại:** VNM đã trải qua một đợt tăng giá mạnh mẽ sau đó là giai đoạn điều chỉnh. Xu hướng tổng thể trong giai đoạn quan sát là tăng nhẹ (từ 62,100 lên 68,000), nhưng quan trọng hơn là sự xuất hiện của một đợt tăng trưởng bùng nổ theo sau là một sự điều chỉnh.\n\n**2. Mức hỗ trợ và kháng cự:**\n\n*   **Mức hỗ trợ:**\n    *   **60,000 - 60,300 VND:** Đây là vùng hỗ trợ mạnh mẽ được xác lập vào đầu tháng 1 (ngày 05/01/2026) khi giá bật tăng trở lại từ mức này.\n    *   **67,000 - 67,200 VND:** Vùng này đã được kiểm định vào ngày 23/01/2026 và 27/01/2026. Giá có xu hướng phản ứng và bật lên từ vùng này, cho thấy đây là một mức hỗ trợ quan trọng sau đợt tăng giá.\n*   **Mức kháng cự:**\n    *   **70,000 - 71,000 VND:** Sau khi giảm từ đỉnh, vùng giá này đã trở thành kháng cự khi VNM không thể vượt qua một cách thuyết phục (ví dụ: ngày 21/01/2026 giá mở cửa 73,000 nhưng đóng cửa 70,300; ngày 22/01/2026 giá mở cửa 71,100 nhưng đóng cửa 70,900).\n    *   **73,000 - 75,500 VND:** Đây là vùng đỉnh lịch sử gần nhất trong giai đoạn này, là kháng cự rất mạnh mà VNM sẽ cần nhiều lực để vượt qua nếu muốn tiếp tục xu hướng tăng.\n\n**3. Khối lượng giao dịch và thanh khoản:**\n\n*   **Giai đoạn đầu (29/12/2025 - 07/01/2026):** Khối lượng giao dịch ở mức trung bình thấp, dao động từ 1.5 triệu đến 3.2 triệu cổ phiếu/phiên. Thanh khoản ở mức ổn định nhưng không quá sôi động.\n*   **Giai đoạn tăng giá mạnh (08/01/2026 - 20/01/2026):** Khối lượng giao dịch tăng đột biến và duy trì ở mức rất cao, đặc biệt là các phiên bứt phá:\n    *   08/01/2026: 5.6 triệu cổ phiếu (tăng giá)\n    *   13/01/2026: 6.7 triệu cổ phiếu (tăng giá)\n    *   14/01/2026: **24.8 triệu cổ phiếu** (bứt phá mạnh mẽ, tăng trần) - đây là phiên có khối lượng cao nhất và giá tăng mạnh nhất.\n    *   15/01/2026: 19.2 triệu cổ phiếu (tiếp tục tăng)\n    *   20/01/2026: 21.5 triệu cổ phiếu (đạt đỉnh giá)\n    *   Sự tăng vọt về khối lượng đồng thuận với sự tăng giá mạnh mẽ cho thấy dòng tiền lớn đã tham gia vào cổ phiếu VNM, xác nhận xu hướng tăng.\n*   **Giai đoạn điều chỉnh (21/01/2026 - 28/01/2026):** Khối lượng giao dịch có xu hướng giảm dần sau phiên đỉnh điểm, cho thấy áp lực bán đã giảm bớt hoặc người mua thận trọng hơn:\n    *   21/01/2026: 11.2 triệu cổ phiếu\n    *   22/01/2026: 8.0 triệu cổ phiếu\n    *   23/01/2026: 16.0 triệu cổ phiếu (phiên giảm mạnh với khối lượng cao cho thấy có sự thoát hàng hoặc cắt lỗ).\n    *   26/01/2026 - 28/01/2026: Giảm dần từ 8.8 triệu xuống 6.3 triệu cổ phiếu, cho thấy sự ổn định trở lại và áp lực bán không còn quá lớn.\n\n**Kết luận về thanh khoản:** Thanh khoản VNM tăng mạnh đột biến trong giai đoạn tăng giá, đặc biệt là các phiên bứt phá, cho thấy sự quan tâm rất lớn của thị trường. Sau đó giảm dần trong giai đoạn điều chỉnh/tích lũy, điều này có thể là dấu hiệu tích cực nếu khối lượng giảm đi cùng với giá không giảm quá sâu, cho thấy không có quá nhiều người muốn bán ở mức giá thấp hơn.\n\n**4. Biên độ dao động giá:**\n\n*   **Giai đoạn đầu (29/12/2025 - 07/01/2026):** Biên độ dao động giá trong ngày tương đối hẹp, thường chỉ khoảng 500 - 1,000 VND (ví dụ: 29/12: 800 VND, 30/12: 600 VND).\n*   **Giai đoạn tăng giá mạnh (08/01/2026 - 20/01/2026):** Biên độ dao động giá tăng lên đáng kể, cho thấy sự biến động mạnh và sôi động của cổ phiếu:\n    *   08/01/2026: 2,300 VND (từ 61,100 lên 63,400)\n    *   14/01/2026: 4,300 VND (từ 63,400 lên 67,700) - biên độ rất lớn.\n    *   20/01/2026: 4,400 VND (từ 71,100 lên 75,500) - biên độ lớn nhất.\n*   **Giai đoạn điều chỉnh (21/01/2026 - 28/01/2026):** Biên độ vẫn duy trì ở mức cao hơn so với giai đoạn đầu nhưng có phần hẹp lại so với đỉnh điểm của đợt tăng:\n    *   21/01/2026: 3,000 VND (từ 70,000 lên 73,000)\n    *   23/01/2026: 2,900 VND (từ 67,200 lên 70,100)\n    *   27/01/2026: 2,500 VND (từ 66,100 lên 68,600)\n\n**Kết luận về biên độ:** Biên độ dao động giá của VNM đã tăng đáng kể trong giai đoạn tăng trưởng và vẫn duy trì ở mức cao hơn so với ban đầu trong giai đoạn điều chỉnh, cho thấy cổ phiếu này đang có tính biến động cao, phù hợp với nhà đầu tư ưa thích lướt sóng nhưng cũng tiềm ẩn rủi ro lớn hơn.\n\n**5. Các tín hiệu mua/bán tiềm năng:**\n\n*   **Tín hiệu mua:**\n    *   **Bứt phá kháng cự với khối lượng lớn:** Các phiên như 08/01, 12/01, 14/01 là các tín hiệu mua mạnh mẽ tại thời điểm đó khi giá vượt qua các ngưỡng kháng cự cũ với khối lượng tăng vọt.\n    *   **Hồi phục từ vùng hỗ trợ với khối lượng tăng:** Nếu VNM giữ vững vùng 67,000 - 67,200 VND và có một phiên tăng giá mạnh trở lại với khối lượng giao dịch tăng cao, đây có thể là tín hiệu mua.\n    *   **Khối lượng giảm dần khi điều chỉnh:** Khối lượng giảm trong các phiên giảm giá gần đây (26/01, 27/01, 28/01) có thể cho thấy áp lực bán đang cạn kiệt, tạo điều kiện cho một đợt phục hồi ngắn hạn.\n*   **Tín hiệu bán:**\n    *   **Phá vỡ hỗ trợ với khối lượng lớn:** Phiên 23/01 khi giá giảm mạnh xuống 67,200 VND với khối lượng lớn là một tín hiệu bán mạnh mẽ cho những ai đang nắm giữ từ vùng giá cao hơn.\n    *   **Mô hình nến đảo chiều tại vùng kháng cự:** Phiên 21/01 với nến giảm mạnh sau một phiên tăng mạnh trước đó (có thể xem là nến Bearish Engulfing hoặc Shooting Star tùy vào hình thái chi tiết của nến) là một tín hiệu bán/chốt lời tại đỉnh.\n    *   **Thất bại khi kiểm định lại kháng cự:** Nếu VNM cố gắng vượt qua vùng kháng cự 70,000 - 71,000 VND nhưng không thành công và đảo chiều giảm với khối lượng cao, đây sẽ là tín hiệu bán.\n\n**Nhận định về xu hướng ngắn hạn và trung hạn:**\n\n*   **Xu hướng ngắn hạn:** VNM đang trong giai đoạn điều chỉnh/tích lũy sau một đợt tăng nóng. Giá đang tìm điểm cân bằng quanh vùng 67,000 - 68,000 VND. Khối lượng giao dịch giảm dần trong các phiên gần nhất cho thấy áp lực bán đã giảm.\n    *   **Dự báo:** Trong vài phiên tới, VNM có thể tiếp tục dao động trong biên độ 67,000 - 70,000 VND. Nếu giữ vững hỗ trợ 67,000 VND và có tín hiệu tăng trở lại với khối lượng, có thể có một nhịp hồi phục ngắn hạn. Ngược lại, nếu phá vỡ 67,000 VND, rủi ro điều chỉnh sâu hơn về vùng 65,000 VND là có thể xảy ra.\n*   **Xu hướng trung hạn:** Mặc dù đang điều chỉnh, VNM đã có một đợt phục hồi ấn tượng từ vùng đáy 60,000 VND, cho thấy dòng tiền đã quay trở lại và có sự quan tâm đối với cổ phiếu này.\n    *   **Dự báo:** Xu hướng trung hạn vẫn được đánh giá là tích cực nếu VNM có thể duy trì trên các mức hỗ trợ quan trọng như 65,000 VND. Việc điều chỉnh hiện tại có thể là cơ hội để cổ phiếu củng cố nền giá trước khi có thể kiểm định lại vùng đỉnh 73,000 - 75,500 VND. Tuy nhiên, cần theo dõi chặt chẽ diễn biến khối lượng và các tin tức vĩ mô/ngành để xác nhận xu hướng này. Nếu VNM không thể giữ được các mức hỗ trợ mạnh và tiếp tục giảm sâu, xu hướng trung hạn sẽ cần được đánh giá lại.",
        "final_report": "Cổ phiếu VNM là một blue-chip với nền tảng tài chính cực kỳ vững chắc, khả năng sinh lời vượt trội (ROE 25.96%, biên lợi nhuận gộp 41.42%) và dòng tiền tự do dồi dào. Mặc dù tốc độ tăng trưởng doanh thu khiêm tốn, công ty vẫn duy trì hiệu quả hoạt động cao và định giá ở mức hợp lý đến hơi cao (P/E 14.54), phản ánh vị thế dẫn đầu thị trường. Về mặt kỹ thuật, VNM vừa trải qua một đợt tăng giá mạnh mẽ, hiện đang điều chỉnh và tích lũy quanh vùng hỗ trợ 67.000 - 68.000 VND với khối lượng giao dịch giảm dần, cho thấy áp lực bán đang cạn kiệt.\n\n**Khuyến nghị:** **GIỮ** đối với nhà đầu tư hiện hữu. Đối với nhà đầu tư mới tìm kiếm sự ổn định và cổ tức, có thể cân nhắc **MUA TÍCH LŨY** quanh vùng hỗ trợ 67.000 - 67.200 VND nếu tín hiệu hồi phục xuất hiện.\n**Lý do:** Sức khỏe tài chính mạnh mẽ và khả năng sinh lời cao là điểm tựa vững chắc, trong khi giai đoạn điều chỉnh kỹ thuật có thể tạo điểm vào hợp lý.\n**Mức giá mục tiêu trung hạn:** 70.000 - 71.000 VND, xa hơn là 73.000 - 75.500 VND nếu xu hướng tăng được xác nhận lại.",
        "data_sources": {
          "metrics_count": 1,
          "price_data_count": 21,
          "note": "Using hard-coded test data"
        }
      },
      "errorCode": 0,
      "errorDesc": "",
      "requestId": "af1e509e-88ec-40ef-be1a-042a2d45a666",
      "result": true
    }

    // const result = await response.json();
    const result = response
    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as AnalysisData,
      };
    }

    return {
      status: false,
      data: null,
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
    };
  }
};