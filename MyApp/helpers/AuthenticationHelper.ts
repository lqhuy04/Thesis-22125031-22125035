import { sendMessage } from "./api/ApiClients";
import { saveSession, removeSession, getSession } from "./api/TokenStorage";

// Get Profile ------------------------------------------------------------
export type UserProfile = {
  user_id: number;
  email: string;
  has_password: boolean;
};

export const getProfile = async (): Promise<{
  status: boolean;
  data: UserProfile | null;
}> => {
  try {
    const result = await sendMessage("api/auth/me", {
      method: "GET",
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data,
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

// Sign In ------------------------------------------------------------

export const signIn = async ({
  username,
  password,
}: {
  username: string;
  password: string;
}): Promise<{
  status: boolean;
  errorCode: number;
}> => {
  try {
    const result = await sendMessage("api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: username,
        password: password,
      }),
    });

    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      await saveSession(data);

      return {
        status: true,
        errorCode,
      };
    } else {
      return {
        status: false,
        errorCode,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      errorCode: 9999,
    };
  }
};

// Sign Up ------------------------------------------------------------

export const signUp = async ({
  email,
  password,
}: {
  email: string;
  password: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/signup", {
      method: "POST",
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });

    const { errorCode } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

export const resendVerificationEmail = async ({
  email,
}: {
  email: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/resend-verification-otp", {
      method: "POST",
      body: JSON.stringify({
        email,
      }),
    });

    const { errorCode } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

export const verifyRegisterEmail = async ({
  email,
  otp,
}: {
  email: string;
  otp: string;
}): Promise<{
  status: boolean;
  data: string;
}> => {
  try {
    const result = await sendMessage("api/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({
        email,
        otp,
      }),
    });

    const { errorCode } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: "",
      };
    } else {
      return {
        status: false,
        data: "",
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: "",
    };
  }
};

export const socialLogin = async ({
  token,
}: {
  token: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/social-login", {
      method: "POST",
      body: JSON.stringify({ token }),
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      await saveSession(data);
      return { status: true };
    } else {
      return { status: false };
    }
  } catch (error) {
    console.error(error);
    return { status: false };
  }
};

// Forgot Pass ------------------------------------------------------------
export const sendOTPForgotPass = async ({
  email,
}: {
  email: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });

    const { errorCode } = result || {};
    if (errorCode === 0) {
      return { status: true };
    } else {
      return { status: false };
    }
  } catch (error) {
    console.error(error);
    return { status: false };
  }
};

export const resendOTPForgetPass = async ({
  email,
}: {
  email: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/resend-otp", {
      method: "POST",
      body: JSON.stringify({
        email,
      }),
    });

    const { errorCode } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

export const verifyOTPForgetPass = async ({
  email,
  otp,
}: {
  email: string;
  otp: string;
}): Promise<{
  status: boolean;
  data: string;
}> => {
  try {
    const result = await sendMessage("api/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({
        email,
        otp,
      }),
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data?.reset_password_token,
      };
    } else {
      return {
        status: false,
        data: "",
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: "",
    };
  }
};

export const resetForgetPassword = async ({
  reset_password_token,
  new_password,
  confirm_new_password,
}: {
  reset_password_token: string;
  new_password: string;
  confirm_new_password: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/reset-password-with-otp", {
      method: "POST",
      body: JSON.stringify({
        reset_password_token,
        new_password,
        confirm_new_password,
      }),
    });

    const { errorCode } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

// Log out ------------------------------------------------------------
export const resetPassword = async ({
  old_password,
  new_password,
  confirm_new_password,
}: {
  old_password: string | undefined;
  new_password: string;
  confirm_new_password: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({
        old_password,
        new_password,
        confirm_new_password,
      }),
    });

    const { errorCode } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

// Log out ------------------------------------------------------------
export const logOut = async (): Promise<{
  status: boolean;
}> => {
  try {
    const refresh_token = await getSession().then(
      (session) => session?.refresh_token,
    );

    const result = await sendMessage("api/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    });

    const { errorCode } = result || {};

    if (errorCode === 0) {
      await removeSession();

      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};
