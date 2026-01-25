import { Redirect } from "expo-router";
import React from "react";

export default function Index() {
  //   // Giả sử bạn có biến kiểm tra login từ Context hoặc Storage
  //   const isLoggedIn = false; // Thay bằng logic thực tế của bạn

  //   if (!isLoggedIn) {
  //     // Nếu chưa đăng nhập, tự động đẩy sang màn hình Authentication
  //     return <Redirect href="/Authentication" />;
  //   }

  // Nếu đã đăng nhập, đẩy sang màn hình chính (ví dụ: /home)
  return <Redirect href="/Home" />;
}
