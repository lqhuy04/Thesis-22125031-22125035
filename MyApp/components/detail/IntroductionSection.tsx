import React from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";

const IntroductionSection = () => {
  return (
    <View style={{ marginTop: 12, marginHorizontal: 12 }}>
      <Text typography="titleLarge" style={{ marginBottom: 8 }}>
        Introduction
      </Text>

      <Text typography="bodyMedium">
        Công ty Cổ phần Sữa Việt Nam (VNM) có tiền thân là Công ty Sữa – Cà Phê
        Miền Nam, được thành lập vào năm 1976. Công ty hoạt động chính trong
        lĩnh vực chế biến sản xuất, kinh doanh xuất nhập khẩu các sản phẩm sữa
        và các sản phẩm dinh dưỡng khác. VNM chính thức hoạt động theo mô hình
        công ty cổ phần từ năm 2003. Công ty giữ vững vị thế top 1 thị phần
        ngành sữa Việt Nam , hiện nay VNM đang quản lý hơn 130.000 đàn bò sữa
        đang khai thác, 15 trang trại bò sữa công nghệ cao, 16 nhà máy sữa hiện
        đại và 1 nhà máy thị bò mát 10.000 tấn. Sản phẩm của VNM đã có mặt tại
        hơn 200.000 điểm bán trong hệ thống phân phối và được xuất khẩu trực
        tiếp đến 63 quốc gia và vùng lãnh thổ trên thế giới. VNM được niêm yết
        và giao dịch trên Sở Chứng khoán Thành phố Hồ Chí Minh (HOSE) từ năm
        2006.
      </Text>
    </View>
  );
};
export default IntroductionSection;
