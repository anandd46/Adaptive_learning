/**
 * Axios API client with JWT interceptor.
 * Automatically attaches Authorization header and handles 401 refresh.
 */
import axios, { AxiosError } from 'axios'
import { useAuthStore } from '@/store/authStore'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// ─── Request Interceptor — attach token ───────────────────────────────────────
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Response Interceptor — handle 401 ───────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const { refreshToken, setAuth, clearAuth } = useAuthStore.getState()

      if (refreshToken) {
        try {
          const response = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token, user_id, role } = response.data.data
          const currentUser = useAuthStore.getState().user!
          setAuth(access_token, refresh_token, { ...currentUser, id: user_id, role })
          originalRequest!.headers!.Authorization = `Bearer ${access_token}`
          return apiClient(originalRequest!)
        } catch {
          clearAuth()
          window.location.href = '/login'
        }
      } else {
        clearAuth()
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
