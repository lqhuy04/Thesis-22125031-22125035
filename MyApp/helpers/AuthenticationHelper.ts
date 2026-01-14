type Response<T = any> = {
  status: boolean;
  data: T | null;
};

export const signIn = async ({
  username,
  password,
}: {
  username: string;
  password: string;
}): Promise<Response> => {
  try {
    const response = await fetch("http://192.168.1.71:8000/api/auth/login", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: username,
        password: password,
      }),
    });

    const result = await response.json();
    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
        data: data,
      };
    } else {
      return {
        status: false,
        data: null,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
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
}): Promise<Response> => {
  try {
    const response = await fetch("http://192.168.1.71:8000/api/auth/signup", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        phoneNumber: phoneNumber,
        password: password,
      }),
    });
    const result = await response.json();
    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data,
      };
    } else {
      return {
        status: false,
        data: null,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
    };
  }
};
