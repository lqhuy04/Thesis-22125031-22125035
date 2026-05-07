import { useTheme } from "@/hooks/ThemeContext";
import React, { useEffect, useState } from "react";
import { TouchableOpacity, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Text } from "@/components/ui/Text";
import { router } from "expo-router";
import { getSession, removeSession, Session } from "@/helpers/api/TokenStorage";
import { SafeAreaView } from "react-native-safe-area-context";
import AntDesign from "@expo/vector-icons/AntDesign";
import FontAwesome6 from "@expo/vector-icons/FontAwesome6";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";

const Profile = () => {
  const { theme } = useTheme();
  const [profile, setProfile] = useState<Session | null>(null);

  useEffect(() => {
    getSession().then((res) => {
      setProfile(res);
    });
  }, []);

  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
      }}
    >
      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginHorizontal: 12,
          marginTop: 12,
          flexDirection: "row",
          alignItems: "center",
        }}
      >
        <View
          style={{
            backgroundColor: theme.base.primary + "12",
            width: 48,
            height: 48,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <FontAwesome6 name="user" size={20} color={theme.base.primary + 80} />
        </View>

        <View style={{ flex: 1, marginLeft: 8 }}>
          <Text typography="titleMedium">{profile?.email}</Text>
          <Text typography="bodyLarge">{profile?.user_id}</Text>
        </View>
      </View>

      <Text
        typography="titleMedium"
        style={{ marginHorizontal: 12, marginTop: 24, marginBottom: 8 }}
      >
        Quản lý
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginHorizontal: 12,
        }}
      >
        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 30,
              marginRight: 8,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <MaterialIcons
              name="attach-money"
              size={20}
              color={theme.base.primary}
            />
          </View>
          <View style={{ flex: 1 }}>
            <Text typography="bodyLarge">Quản lý tài sản</Text>
          </View>

          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color="black"
          />
        </TouchableOpacity>

        <View
          style={{
            height: 1,
            backgroundColor: theme.border.default + "80",
            marginVertical: 12,
          }}
        />

        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 30,
              marginRight: 8,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Ionicons
              name="bar-chart-outline"
              size={20}
              style={{ marginRight: 8 }}
              color={theme.base.primary}
            />
          </View>
          <View style={{ flex: 1 }}>
            <Text typography="bodyLarge">Khẩu vị rủi ro</Text>
          </View>

          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color="black"
          />
        </TouchableOpacity>

        <View
          style={{
            height: 1,
            backgroundColor: theme.border.default + "80",
            marginVertical: 12,
          }}
        />

        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 30,
              marginRight: 8,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <AntDesign
              name="stock"
              size={20}
              color={theme.base.primary}
              style={{ marginRight: 8 }}
            />
          </View>

          <View style={{ flex: 1 }}>
            <Text typography="bodyLarge">Danh sách theo dõi</Text>
          </View>

          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color="black"
          />
        </TouchableOpacity>
      </View>

      <Text
        typography="titleMedium"
        style={{ marginHorizontal: 12, marginTop: 24, marginBottom: 8 }}
      >
        Hệ thống
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginHorizontal: 12,
        }}
      >
        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 30,
              marginRight: 8,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <MaterialCommunityIcons
              name="theme-light-dark"
              size={20}
              color={theme.base.primary}
            />
          </View>
          <View style={{ flex: 1 }}>
            <Text typography="bodyLarge">Chế độ tối</Text>
          </View>

          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color="black"
          />
        </TouchableOpacity>

        <View
          style={{
            height: 1,
            backgroundColor: theme.border.default + "80",
            marginVertical: 12,
          }}
        />

        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 30,
              marginRight: 8,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Ionicons
              name="language-outline"
              size={20}
              color={theme.base.primary}
            />
          </View>
          <View style={{ flex: 1 }}>
            <Text typography="bodyLarge">Ngôn ngữ</Text>
          </View>

          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color="black"
          />
        </TouchableOpacity>
      </View>

      <Text
        typography="titleMedium"
        style={{ marginHorizontal: 12, marginTop: 24, marginBottom: 8 }}
      >
        Tài khoản
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          padding: 12,
          marginHorizontal: 12,
        }}
      >
        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 30,
              marginRight: 8,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <MaterialIcons
              name="password"
              size={20}
              color={theme.base.primary}
            />
          </View>
          <View style={{ flex: 1 }}>
            <Text typography="bodyLarge">Đổi mật khẩu</Text>
          </View>

          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color="black"
          />
        </TouchableOpacity>

        <View
          style={{
            height: 1,
            backgroundColor: theme.border.default + "80",
            marginVertical: 12,
          }}
        />

        <TouchableOpacity
          onPress={() => router.push("/WatchListStock")}
          style={{
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 30,
              marginRight: 8,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <MaterialIcons name="logout" size={20} color={theme.base.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text typography="bodyLarge">Đăng xuất</Text>
          </View>

          <MaterialCommunityIcons
            name="chevron-right"
            size={24}
            color="black"
          />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

export default Profile;
