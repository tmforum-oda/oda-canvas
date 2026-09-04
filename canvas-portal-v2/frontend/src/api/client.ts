import axios from 'axios';
import { getToken, refreshAccessToken, logout } from '@/lib/auth';
import { getApiBaseUrl } from '@/config';

const apiClient = axios.create({
  baseURL: getApiBaseUrl() || undefined,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    // On 401, try a one-time silent refresh via the httpOnly cookie, then
    // retry the original request. If refresh fails, the session is over.
    if (err.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      const ok = await refreshAccessToken();
      if (ok) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${getToken()}`;
        return apiClient(original);
      }
      logout();
    }
    return Promise.reject(err);
  }
);

export default apiClient;
