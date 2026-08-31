const TOKEN_KEY = "shelly-manager-auth-token";

export const getStoredToken = (): string | null =>
  localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(TOKEN_KEY);

export const storeToken = (token: string, rememberMe: boolean): void => {
  clearToken();
  (rememberMe ? localStorage : sessionStorage).setItem(TOKEN_KEY, token);
};

export const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
};
