import { sendMessage } from "./api/ApiClients";
import { saveSession, removeSession } from "./api/TokenStorage";

export const signIn = async ({
  username,
  password,
}: {
  username: string;
  password: string;
}): Promise<{
  status: boolean;
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

export const signUp = async ({
  email,
  phoneNumber,
  password,
}: {
  email: string;
  phoneNumber: string;
  password: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/auth/signup", {
      method: "POST",
      body: JSON.stringify({
        email: email,
        phone_number: phoneNumber,
        password: password,
      }),
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      await saveSession(data);
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

export const logout = async () => {
  await removeSession();
};
