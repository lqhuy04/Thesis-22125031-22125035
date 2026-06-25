import { useState, useEffect } from "react";
import { Keyboard, Platform, LayoutAnimation } from "react-native";

const useKeyboardVisible = (enableAnimation: boolean = true) => {
  const [isKeyboardVisible, setKeyboardVisible] = useState(false);

  useEffect(() => {
    const showEvent =
      Platform?.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow";
    const hideEvent =
      Platform?.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide";

    const onKeyboardShow = () => {
      if (enableAnimation) {
        LayoutAnimation?.configureNext?.(
          LayoutAnimation?.Presets?.easeInEaseOut,
        );
      }
      setKeyboardVisible(true);
    };

    const onKeyboardHide = () => {
      if (enableAnimation) {
        LayoutAnimation?.configureNext?.(
          LayoutAnimation?.Presets?.easeInEaseOut,
        );
      }
      setKeyboardVisible(false);
    };

    const showSub = Keyboard?.addListener?.(showEvent, onKeyboardShow);
    const hideSub = Keyboard?.addListener?.(hideEvent, onKeyboardHide);

    return () => {
      showSub?.remove?.();
      hideSub?.remove?.();
    };
  }, [enableAnimation]);

  return isKeyboardVisible;
};

export default useKeyboardVisible;
