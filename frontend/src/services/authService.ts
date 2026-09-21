/**
 * Auth API service — login, register, refresh.
 */
import apiClient from './apiClient'
import { useAuthStore } from '@/store/authStore'

export interface RegisterData {
  email: string
  password: string
  full_name: string
  role: 'student' | 'teacher'
  grade_level?: string
}

export interface LoginData {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  role: string
  user_id: string
}

export const authService = {
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/register', data)
    return response.data.data
  },

  async login(data: LoginData): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/login', data)
    return response.data.data
  },

  logout() {
    useAuthStore.getState().clearAuth()
    window.location.href = '/login'
  },
}
