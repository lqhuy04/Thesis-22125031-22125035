import * as SecureStore from "expo-secure-store";

const ONBOARDING_KEY = "onboarding_done";

export const hasSeenOnboarding = async (): Promise<boolean> => {
  const val = await SecureStore.getItemAsync(ONBOARDING_KEY);
  return val === "true";
};

export const markOnboardingDone = async (): Promise<void> => {
  await SecureStore.setItemAsync(ONBOARDING_KEY, "true");
};

// Hữu ích khi test lại flow onboarding
export const resetOnboarding = async (): Promise<void> => {
  await SecureStore.deleteItemAsync(ONBOARDING_KEY);
};
