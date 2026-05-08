import { FavoriteItem, getFavoritelist } from "@/helpers/ProfileHelpers";
import React, { useEffect, useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";
import { View } from "react-native";

const Favorite = () => {
  const { theme } = useTheme();
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);

  useEffect(() => {
    getFavoritelist().then((res) => {
      if (res?.status) {
        setFavorites(res?.data);
      }
    });
  }, []);

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: theme.background.surface }}
    >
      {favorites.map((item, index) => {
        return (
          <View
            key={item.id}
            style={{ padding: 12, backgroundColor: "red" }}
          ></View>
        );
      })}
    </SafeAreaView>
  );
};

export default Favorite;
